"""
Simulation Service: Singleton state manager bridging the FastAPI API layer,
the SQLite database, and the in-memory SimulationEngine.
"""
import json
import os
import copy
from typing import Dict, Any, List, Optional
from backend.app.simulation.engine import SimulationEngine
from backend.app.simulation.scenarios import DEMO_PATIENTS, DEMO_RESOURCES
from backend.app.models.enums import AllocationStrategy, ResourceStatus
from backend.app.schemas.hospital_schemas import (
    PatientCreate,
    PatientRead,
    ResourceSummary,
    AgentStatusRead,
    SimulationEventSchema,
    MetricsSummary,
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

    def start_simulation(self, strategy: AllocationStrategy = AllocationStrategy.PRIORITY_AWARE) -> MetricsSummary:
        """Run the simulation to completion and synchronize state back to database."""
        self.strategy = strategy
        db = SessionLocal()
        try:
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
        # Update patients
        for p_data in self.engine.patients.values():
            db_p = db.query(PatientModel).filter(PatientModel.id == p_data["id"]).first()
            if db_p:
                for k, v in p_data.items():
                    if hasattr(db_p, k):
                        setattr(db_p, k, v)
            else:
                db.add(PatientModel(**p_data))

        # Update ambulances
        for amb in self.engine.ambulances:
            db_amb = db.query(AmbulanceModel).filter(AmbulanceModel.id == amb["id"]).first()
            if db_amb:
                for k, v in amb.items():
                    if hasattr(db_amb, k):
                        setattr(db_amb, k, v)

        # Update doctors
        for doc in self.engine.doctors:
            db_doc = db.query(DoctorModel).filter(DoctorModel.id == doc["id"]).first()
            if db_doc:
                for k, v in doc.items():
                    if hasattr(db_doc, k):
                        setattr(db_doc, k, v)

        # Update diagnostic resources
        for diag in self.engine.diagnostic_resources:
            db_diag = db.query(DiagnosticResourceModel).filter(DiagnosticResourceModel.id == diag["id"]).first()
            if db_diag:
                for k, v in diag.items():
                    if hasattr(db_diag, k):
                        setattr(db_diag, k, v)

        # Update ICU beds
        for bed in self.engine.icu_beds:
            db_bed = db.query(ICUBedModel).filter(ICUBedModel.id == bed["id"]).first()
            if db_bed:
                for k, v in bed.items():
                    if hasattr(db_bed, k):
                        setattr(db_bed, k, v)

        # Save events
        for evt in self.engine.all_events:
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

        db.commit()

    def get_patients(self) -> List[Dict[str, Any]]:
        """Return all active patient records from engine state."""
        return list(self.engine.patients.values())

    def add_emergency_patient(self, patient_data: PatientCreate) -> Dict[str, Any]:
        """Submit and process a new emergency patient through the complete multi-agent pipeline."""
        p_dict = patient_data.model_dump()
        p_dict["workflow_state"] = "REGISTERED"
        self.engine.patients[p_dict["id"]] = p_dict

        initial_event_count = len(self.engine.all_events)

        # Schedule arrival at current simulation time
        arrival_time = max(self.engine.current_time, p_dict.get("arrival_time", self.engine.current_time))
        self.engine.schedule_event(
            time=arrival_time,
            event_type="PATIENT_ARRIVAL",
            patient_id=p_dict["id"],
        )

        # Step simulation to dynamically orchestrate agents across all clinical milestones
        max_steps = 40
        steps = 0
        while self.engine.event_queue and steps < max_steps:
            event = self.engine.step()
            steps += 1
            curr_state = self.engine.patients[p_dict["id"]].get("workflow_state")
            if curr_state in ("COMPLETED", "DISCHARGED") and not any(e.patient_id == p_dict["id"] for e in self.engine.event_queue):
                break

        self.engine._sync_logs()

        # Collect events created during this patient's orchestration
        patient_events = [
            evt for evt in self.engine.all_events[initial_event_count:]
            if evt.patient_id == p_dict["id"]
        ]

        updated_patient = copy.deepcopy(self.engine.patients[p_dict["id"]])
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
        """Return monitor data for all agents."""
        agents = [self.engine.coordinator] + self.engine.coordinator.specialized_agents
        res_list = []
        for ag in agents:
            status_data = ag.get_status()
            res_list.append(
                AgentStatusRead(
                    name=status_data["name"],
                    role=status_data["role"],
                    status=status_data["status"],
                    last_action=status_data["last_action"],
                    last_message=status_data["last_message"],
                    pending_count=status_data["pending_count"],
                )
            )
        return res_list

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
