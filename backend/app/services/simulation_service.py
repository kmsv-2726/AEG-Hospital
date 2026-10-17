"""
Simulation Service: Singleton state manager bridging the FastAPI API layer,
the SQLite database, the in-memory SimulationEngine, and OS Resource Management.
"""
import json
import os
import copy
from typing import Dict, Any, List, Optional
from backend.app.simulation.engine import SimulationEngine
from backend.app.simulation.scenarios import DEMO_PATIENTS, DEMO_RESOURCES
from backend.app.models.enums import AllocationStrategy, ResourceStatus, WorkflowState
from backend.app.schemas.hospital_schemas import (
    PatientCreate,
    PatientRead,
    ResourceSummary,
    AgentStatusRead,
    SimulationEventSchema,
    MetricsSummary,
    OSManagerStatusRead,
    PatientOrchestrationResponse,
    OrchestrationStep,
)
from backend.app.database.init_db import init_db, reset_db
from backend.app.database.session import SessionLocal
from backend.app.models.entities import (
    PatientModel,
    AmbulanceModel,
    DoctorModel,
    DiagnosticResourceModel,
    ICUBedModel,
    SimulationEventModel,
    AgentMessageModel,
)
from backend.app.models.enums import MessageType
from backend.app.schemas.hospital_schemas import AgentMessageSchema


class SimulationService:
    """Manages active simulation lifecycle, database synchronization, and API queries."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SimulationService, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def initialize(self, strategy: AllocationStrategy = AllocationStrategy.PRIORITY_AWARE):
        init_db()
        self.strategy = strategy
        self.engine = SimulationEngine(strategy=strategy, seed=42)

        # Check if database already has seeded data, if not seed it
        db = SessionLocal()
        try:
            if db.query(PatientModel).count() == 0:
                self._seed_default_db(db)
            self._load_from_db(db)
        finally:
            db.close()

        self.initialized = True

    def _seed_default_db(self, db):
        """Seed initial demonstration scenario into database."""
        for amb in DEMO_RESOURCES["ambulances"]:
            db.add(AmbulanceModel(**amb))
        for doc in DEMO_RESOURCES["doctors"]:
            db.add(DoctorModel(**doc))
        for diag in DEMO_RESOURCES["diagnostic_resources"]:
            db.add(DiagnosticResourceModel(**diag))
        for bed in DEMO_RESOURCES["icu_beds"]:
            db.add(ICUBedModel(**bed))
        for p in DEMO_PATIENTS:
            db.add(PatientModel(**p))
        db.commit()

    def _load_from_db(self, db):
        """Load scenario data from database into SimulationEngine."""
        patients = [
            {c.name: getattr(p, c.name) for c in p.__table__.columns}
            for p in db.query(PatientModel).all()
        ]
        for patient in patients:
            patient["required_equipment"] = [
                value for value in (patient.get("required_equipment") or "").split(",") if value
            ]
            patient["required_icu_equipment"] = [
                value for value in (patient.get("required_icu_equipment") or "").split(",") if value
            ]
            patient["decision_trace"] = json.loads(patient.pop("decision_trace_json", "[]") or "[]")
        resources = {
            "ambulances": [
                {c.name: getattr(a, c.name) for c in a.__table__.columns}
                for a in db.query(AmbulanceModel).all()
            ],
            "doctors": [
                {c.name: getattr(d, c.name) for c in d.__table__.columns}
                for d in db.query(DoctorModel).all()
            ],
            "diagnostic_resources": [
                {c.name: getattr(r, c.name) for c in r.__table__.columns}
                for r in db.query(DiagnosticResourceModel).all()
            ],
            "icu_beds": [
                {c.name: getattr(b, c.name) for c in b.__table__.columns}
                for b in db.query(ICUBedModel).all()
            ],
        }
        self.engine = SimulationEngine(strategy=self.strategy, seed=42)
        self.engine.load_scenario(patients, resources)
        self.engine.all_events = [
            SimulationEventSchema.model_validate(event)
            for event in db.query(SimulationEventModel).order_by(
                SimulationEventModel.id
            ).all()
        ]
        persisted_messages = db.query(AgentMessageModel).order_by(AgentMessageModel.id).all()
        self.engine.coordinator.message_bus.message_history = [
            AgentMessageSchema(
                message_id=message.message_id,
                sender=message.sender,
                receiver=message.receiver,
                message_type=MessageType(message.message_type),
                patient_id=message.patient_id,
                resource_id=message.resource_id,
                simulation_time=message.simulation_time,
                correlation_id=message.correlation_id,
                payload=json.loads(message.payload_json or "{}"),
                status=message.status,
            )
            for message in persisted_messages
        ]
        self.engine.all_messages = list(self.engine.coordinator.message_bus.message_history)
        self._persisted_event_count = len(self.engine.all_events)
        self._persisted_message_count = len(self.engine.all_messages)

    def _reset_run_state(self, db):
        """Reset persisted runtime fields so a completed cohort can be replayed."""
        patient_runtime_fields = (
            "hospital_arrival_time",
            "ambulance_dispatch_time",
            "doctor_request_time",
            "doctor_assignment_time",
            "diagnostic_request_time",
            "diagnostic_start_time",
            "diagnostic_end_time",
            "icu_request_time",
            "icu_reservation_time",
            "treatment_start_time",
            "completion_time",
        )
        assignment_fields = (
            "assigned_ambulance_id",
            "assigned_doctor_id",
            "assigned_diagnostic_id",
            "assigned_icu_bed_id",
        )

        for patient in db.query(PatientModel).all():
            patient.workflow_state = WorkflowState.REGISTERED.value
            patient.waiting_duration = 0.0
            patient.decision_trace_json = "[]"
            patient.triage_reason = None
            patient.triage_requires_review = False
            for field in patient_runtime_fields:
                setattr(patient, field, None)
            for field in assignment_fields:
                setattr(patient, field, None)

        for model in (AmbulanceModel, DoctorModel, DiagnosticResourceModel, ICUBedModel):
            for resource in db.query(model).all():
                resource.status = ResourceStatus.AVAILABLE.value
                resource.current_patient_id = None
                resource.total_busy_time = 0.0
                resource.availability_timestamp = 0.0
                if isinstance(resource, DoctorModel):
                    resource.workload_count = 0
                elif isinstance(resource, AmbulanceModel):
                    resource.total_dispatches = 0
                elif isinstance(resource, DiagnosticResourceModel):
                    resource.queue_length = 0
                elif isinstance(resource, ICUBedModel):
                    resource.reservation_timestamp = None
                    resource.release_timestamp = None

        db.query(SimulationEventModel).delete(synchronize_session=False)
        db.query(AgentMessageModel).delete(synchronize_session=False)
        db.commit()

    def start_simulation(self, strategy: AllocationStrategy = AllocationStrategy.PRIORITY_AWARE) -> MetricsSummary:
        """Replay the persisted synthetic cohort from a clean runtime state."""
        self.strategy = strategy
        db = SessionLocal()
        try:
            self._reset_run_state(db)
            self._load_from_db(db)
            metrics = self.engine.run_until_complete()
            self._sync_to_db(db)
            return metrics
        finally:
            db.close()

    def reset_simulation(self, strategy: AllocationStrategy = AllocationStrategy.PRIORITY_AWARE):
        """Reset database and simulation engine back to standard demonstration state."""
        self.strategy = strategy
        reset_db()
        db = SessionLocal()
        try:
            self._seed_default_db(db)
            self._load_from_db(db)
        finally:
            db.close()

    def _sync_to_db(self, db):
        """Persist engine state back to database tables."""
        for p_data in self.engine.patients.values():
            db_p = db.query(PatientModel).filter(PatientModel.id == p_data["id"]).first()
            filtered_p = {k: v for k, v in p_data.items() if hasattr(PatientModel, k) and k != "_sa_instance_state"}
            if "required_equipment" in filtered_p:
                filtered_p["required_equipment"] = ",".join(filtered_p["required_equipment"] or [])
            if "required_icu_equipment" in filtered_p:
                filtered_p["required_icu_equipment"] = ",".join(filtered_p["required_icu_equipment"] or [])
            filtered_p["decision_trace_json"] = json.dumps(p_data.get("decision_trace", []))
            if db_p:
                for k, v in filtered_p.items():
                    setattr(db_p, k, v)
            else:
                db.add(PatientModel(**filtered_p))

        for amb in self.engine.ambulances:
            db_amb = db.query(AmbulanceModel).filter(AmbulanceModel.id == amb["id"]).first()
            if db_amb:
                for k, v in amb.items():
                    if hasattr(db_amb, k):
                        setattr(db_amb, k, v)

        for doc in self.engine.doctors:
            db_doc = db.query(DoctorModel).filter(DoctorModel.id == doc["id"]).first()
            if db_doc:
                for k, v in doc.items():
                    if hasattr(db_doc, k):
                        setattr(db_doc, k, v)

        for diag in self.engine.diagnostic_resources:
            db_diag = db.query(DiagnosticResourceModel).filter(DiagnosticResourceModel.id == diag["id"]).first()
            if db_diag:
                for k, v in diag.items():
                    if hasattr(db_diag, k):
                        setattr(db_diag, k, v)

        for bed in self.engine.icu_beds:
            db_bed = db.query(ICUBedModel).filter(ICUBedModel.id == bed["id"]).first()
            if db_bed:
                for k, v in bed.items():
                    if hasattr(db_bed, k):
                        setattr(db_bed, k, v)

        for evt in self.engine.all_events[getattr(self, "_persisted_event_count", 0):]:
            db_evt = SimulationEventModel(
                simulation_time=evt.simulation_time,
                event_type=evt.event_type,
                agent=evt.agent,
                patient_id=evt.patient_id,
                resource_id=evt.resource_id,
                description=evt.description,
                outcome=evt.outcome,
                is_conflict=evt.is_conflict,
            )
            db.add(db_evt)

        messages = self.engine.coordinator.message_bus.message_history
        for message in messages[getattr(self, "_persisted_message_count", 0):]:
            db.add(AgentMessageModel(
                message_id=message.message_id,
                sender=message.sender,
                receiver=message.receiver,
                message_type=message.message_type.value,
                patient_id=message.patient_id,
                resource_id=message.resource_id,
                simulation_time=message.simulation_time,
                correlation_id=message.correlation_id,
                payload_json=json.dumps(message.payload),
                status=message.status,
            ))

        db.commit()
        self._persisted_event_count = len(self.engine.all_events)
        self._persisted_message_count = len(messages)

    def get_patients(self) -> List[Dict[str, Any]]:
        """Return all active patient records from engine state."""
        return list(self.engine.patients.values())

    def add_emergency_patient(self, patient_data: PatientCreate) -> Dict[str, Any]:
        """
        Submit and process a new emergency patient through the autonomous multi-agent pipeline.
        Engages specialized agents (Triage, Ambulance, Doctor, Diagnostic, ICU)
        and leaves resources and agents actively occupied for live monitoring.
        """
        p_dict = patient_data.model_dump()
        pid = p_dict["id"]
        if pid in self.engine.patients:
            raise ValueError(f"Patient ID '{pid}' is already registered.")
        p_dict["workflow_state"] = "REGISTERED"
        p_dict["decision_trace"] = []
        self.engine.patients[pid] = p_dict

        initial_event_count = len(self.engine.all_events)

        # Register in OS Manager
        arrival_time = max(self.engine.current_time, p_dict.get("arrival_time", self.engine.current_time))
        self.engine.coordinator.os_manager.register_patient_process(p_dict, arrival_time)

        # Schedule arrival
        self.engine.schedule_event(
            time=arrival_time,
            event_type="PATIENT_ARRIVAL",
            patient_id=pid,
        )

        # Step simulation to dynamically orchestrate agents across intake and admission milestones
        # We process through arrival, triage, ambulance dispatch, and hospital admission/doctor assignment
        max_steps = 15
        steps = 0
        while self.engine.event_queue and steps < max_steps:
            # Check if next event belongs to this patient or related waiting queues
            next_evt = self.engine.event_queue[0]
            curr_state = self.engine.patients[pid].get("workflow_state", "")

            # If patient is actively admitted and in clinical care, stop so agents stay visibly active!
            if curr_state in (
                WorkflowState.DOCTOR_ASSIGNED.value,
                WorkflowState.DIAGNOSTICS_IN_PROGRESS.value,
                WorkflowState.TREATMENT_SIMULATED.value,
                WorkflowState.WAITING_FOR_DOCTOR.value,
                WorkflowState.WAITING_FOR_AMBULANCE.value,
                WorkflowState.WAITING_FOR_ICU.value,
                WorkflowState.WAITING_FOR_DIAGNOSTIC.value,
            ) and next_evt.event_type in ("DOCTOR_EXAM_COMPLETED", "TREATMENT_COMPLETED", "DIAGNOSTIC_COMPLETED"):
                break

            self.engine.step()
            steps += 1

            if curr_state in ("COMPLETED", "DISCHARGED"):
                break

        self.engine._sync_logs()

        # Collect events created during this patient's orchestration
        patient_events = [
            evt for evt in self.engine.all_events[initial_event_count:]
            if evt.patient_id == pid
        ]

        updated_patient = copy.deepcopy(self.engine.patients[pid])
        updated_patient["orchestration_events"] = patient_events

        # Sync to database
        db = SessionLocal()
        try:
            self._sync_to_db(db)
        finally:
            db.close()

        return updated_patient

    def step_simulation(self) -> Dict[str, Any]:
        """Advance simulation by a single discrete event and return event detail."""
        if not self.engine.event_queue:
            return {
                "event": None,
                "message": "Simulation event queue is empty. All emergency workflows completed.",
                "is_completed": True,
                "current_time": self.engine.current_time,
            }

        prev_count = len(self.engine.all_events)
        event = self.engine.step()
        new_events = self.engine.all_events[prev_count:]

        db = SessionLocal()
        try:
            self._sync_to_db(db)
        finally:
            db.close()

        return {
            "event": {
                "event_type": event.event_type,
                "patient_id": event.patient_id,
                "time": event.time,
                "resource_id": event.resource_id,
            } if event else None,
            "new_events": [e.model_dump() for e in new_events],
            "current_time": self.engine.current_time,
            "is_completed": self.engine.is_completed,
            "queue_remaining": len(self.engine.event_queue),
        }

    def get_resources(self) -> Dict[str, Any]:
        """Return resources and live status counts."""
        ambs = self.engine.ambulances
        docs = self.engine.doctors
        diags = self.engine.diagnostic_resources
        beds = self.engine.icu_beds

        def count_status(items):
            avail = sum(1 for x in items if x.get("status") == ResourceStatus.AVAILABLE.value)
            busy = sum(1 for x in items if x.get("status") == ResourceStatus.BUSY.value)
            return {"available": avail, "busy": busy, "total": len(items)}

        return {
            "ambulances": ambs,
            "doctors": docs,
            "diagnostic_resources": diags,
            "icu_beds": beds,
            "counts": {
                "ambulances": count_status(ambs),
                "doctors": count_status(docs),
                "diagnostic_resources": count_status(diags),
                "icu_beds": count_status(beds),
            },
        }

    def get_agents(self) -> List[AgentStatusRead]:
        """Return monitor data for all agents including active patients, inbox, and recent messages."""
        agents = [self.engine.coordinator] + self.engine.coordinator.specialized_agents
        res_list = []
        for ag in agents:
            status_data = ag.get_status()
            # Fetch recent messages involving this agent
            recent_msgs = [
                m for m in self.engine.coordinator.message_bus.message_history
                if m.sender == ag.name or m.receiver == ag.name
            ][-5:]

            res_list.append(
                AgentStatusRead(
                    name=status_data["name"],
                    role=status_data["role"],
                    status=status_data["status"],
                    last_action=status_data["last_action"],
                    last_message=status_data["last_message"],
                    pending_count=status_data["pending_count"],
                    active_patients=status_data.get("active_patients", []),
                    current_process_id=status_data.get("current_process_id"),
                    inbox_count=status_data.get("inbox_count", 0),
                    recent_messages=recent_msgs,
                )
            )
        return res_list

    def get_os_status(self) -> Dict[str, Any]:
        """Return OS Resource Manager state: semaphores, mutexes, ready queue, and PCBs."""
        return self.engine.coordinator.os_manager.get_os_metrics(self.engine.current_time)

    def get_patient_orchestration(self, patient_id: str) -> Dict[str, Any]:
        """Return complete multi-agent orchestration transcript, PCB, and message feed for a patient."""
        patient = self.engine.patients.get(patient_id)
        if not patient:
            return {}

        pcb = self.engine.coordinator.os_manager.pcbs.get(patient_id)
        messages = self.engine.coordinator.message_bus.get_messages_for_patient(patient_id)
        events = [e for e in self.engine.all_events if e.patient_id == patient_id]

        steps = [
            OrchestrationStep(
                agent=trace.get("agent", "HospitalCoordinator"),
                action=trace.get("action", "DECISION"),
                timestamp=trace.get("simulation_time", 0.0),
                description=trace.get("description", ""),
                status=trace.get("status", "UNKNOWN"),
                details=trace.get("details", {}),
            )
            for trace in patient.get("decision_trace", [])
        ]

        return {
            "patient": patient,
            "pcb": pcb.model_dump() if pcb else None,
            "orchestration_steps": [s.model_dump() for s in steps],
            "agent_messages": [m.model_dump() for m in messages],
            "events": [e.model_dump() for e in events],
        }

    def get_events(self) -> List[SimulationEventSchema]:
        """Return full event log."""
        return self.engine.all_events

    def get_metrics(self) -> MetricsSummary:
        """Return current performance metrics."""
        return self.engine.get_metrics()

    def get_baseline_comparison(self) -> Dict[str, Any]:
        """Return stored baseline comparison results."""
        path = os.path.join(os.path.dirname(__file__), "..", "simulation", "baseline_results.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}


# Module singleton
sim_service = SimulationService()
