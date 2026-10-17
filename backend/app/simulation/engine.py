"""
Discrete-Event Simulation (DES) Engine for Multi-Agent Hospital Emergency Operations.
Enhanced with OS Resource Management (PCBs, Semaphores, Mutexes, and Dynamic Aging).
"""
import heapq
import copy
from typing import Dict, Any, List, Optional
from backend.app.models.enums import AllocationStrategy, WorkflowState, ResourceStatus
from backend.app.coordinator.hospital_coordinator import HospitalCoordinator
from backend.app.simulation.events import SimEvent
from backend.app.simulation.metrics import calculate_simulation_metrics
from backend.app.schemas.hospital_schemas import MetricsSummary, SimulationEventSchema, AgentMessageSchema


class SimulationEngine:
    """
    Priority-queue event scheduler managing the execution of simulated hospital time,
    agent communications, conflict resolution, OS scheduling, and deterministic reproducibility.
    """

    def __init__(
        self,
        strategy: AllocationStrategy = AllocationStrategy.PRIORITY_AWARE,
        seed: int = 42,
    ):
        self.strategy = strategy
        self.seed = seed
        self.current_time: float = 0.0
        self.event_counter: int = 0
        self.event_queue: List[SimEvent] = []

        self.coordinator = HospitalCoordinator(strategy=self.strategy)
        self.patients: Dict[str, Dict[str, Any]] = {}
        self.ambulances: List[Dict[str, Any]] = []
        self.doctors: List[Dict[str, Any]] = []
        self.diagnostic_resources: List[Dict[str, Any]] = []
        self.icu_beds: List[Dict[str, Any]] = []

        self.all_events: List[SimulationEventSchema] = []
        self.all_messages: List[AgentMessageSchema] = []
        self.is_running: bool = False
        self.is_completed: bool = False

    def schedule_event(
        self,
        time: float,
        event_type: str,
        patient_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        """Enqueue an event into the priority heap."""
        self.event_counter += 1
        event = SimEvent(
            time=time,
            event_id=self.event_counter,
            event_type=event_type,
            patient_id=patient_id,
            resource_id=resource_id,
            payload=payload or {},
        )
        heapq.heappush(self.event_queue, event)

    def load_scenario(
        self,
        patients_data: List[Dict[str, Any]],
        resources_data: Dict[str, List[Dict[str, Any]]],
    ):
        """Initialize engine state with deep-copied scenario data and register OS primitives."""
        self.patients = {p["id"]: copy.deepcopy(p) for p in patients_data}
        self.ambulances = copy.deepcopy(resources_data.get("ambulances", []))
        self.doctors = copy.deepcopy(resources_data.get("doctors", []))
        self.diagnostic_resources = copy.deepcopy(resources_data.get("diagnostic_resources", []))
        self.icu_beds = copy.deepcopy(resources_data.get("icu_beds", []))

        # Synchronize OS manager resources
        env = {
            "doctors": self.doctors,
            "diagnostic_resources": self.diagnostic_resources,
            "icu_beds": self.icu_beds,
            "ambulances": self.ambulances,
        }
        self.coordinator.sync_os_resources(env)

        # Register PCBs for patients
        for p in self.patients.values():
            if p.get("workflow_state") != WorkflowState.REGISTERED.value:
                continue
            self.coordinator.os_manager.register_patient_process(p, p.get("arrival_time", 0.0))
            self.schedule_event(
                time=p.get("arrival_time", 0.0),
                event_type="PATIENT_ARRIVAL",
                patient_id=p["id"],
            )

    def _sync_logs(self):
        """Collect events and messages emitted by coordinator and all agents."""
        for agent in [self.coordinator] + self.coordinator.specialized_agents:
            while agent.event_log:
                self.all_events.append(agent.event_log.pop(0))
            while agent.outbox:
                self.all_messages.append(agent.outbox.pop(0))

    def step(self) -> Optional[SimEvent]:
        """Process the single next chronologically ordered simulation event."""
        if not self.event_queue:
            self.is_completed = True
            return None

        event = heapq.heappop(self.event_queue)
        self.current_time = max(self.current_time, event.time)

        env = {
            "simulation_time": self.current_time,
            "ambulances": self.ambulances,
            "doctors": self.doctors,
            "diagnostic_resources": self.diagnostic_resources,
            "icu_beds": self.icu_beds,
            "patients": self.patients,
        }

        # Dispatch event to appropriate handler
        if event.event_type == "PATIENT_ARRIVAL":
            self._handle_patient_arrival(event, env)
        elif event.event_type == "PATIENT_ARRIVED_AT_HOSPITAL":
            self._handle_patient_arrived_at_hospital(event, env)
        elif event.event_type == "DOCTOR_EXAM_COMPLETED":
            self._handle_doctor_exam_completed(event, env)
        elif event.event_type == "DIAGNOSTIC_COMPLETED":
            self._handle_diagnostic_completed(event, env)
        elif event.event_type == "TREATMENT_COMPLETED":
            self._handle_treatment_completed(event, env)
        elif event.event_type == "PATIENT_DISCHARGED":
            self._handle_patient_discharged(event, env)

        self._sync_logs()
        return event

    def run_until_complete(self, max_steps: int = 1000) -> MetricsSummary:
        """Execute simulation events until the queue is exhausted or step limit reached."""
        self.is_running = True
        steps = 0
        while self.event_queue and steps < max_steps:
            self.step()
            steps += 1

        self.is_running = False
        self.is_completed = True
        return self.get_metrics()

    # -------------------------------------------------------------
    # Event Handlers
    # -------------------------------------------------------------

    def _handle_patient_arrival(self, event: SimEvent, env: Dict[str, Any]):
        patient = self.patients.get(event.patient_id)
        if not patient:
            return

        # Step 1: Coordinator handles registration & triage
        self.coordinator.handle_patient_registration(patient, env)

        # Step 2: Request Ambulance
        amb_result = self.coordinator.request_ambulance_allocation(patient, env)
        if amb_result.get("status") == "ALLOCATED":
            self.coordinator.transition_patient(
                patient, WorkflowState.IN_TRANSIT, self.current_time
            )
            travel_time = amb_result.get("travel_time", 5.0)
            # Track ambulance busy time
            for amb in self.ambulances:
                if amb["id"] == amb_result["ambulance_id"]:
                    amb["total_busy_time"] = amb.get("total_busy_time", 0.0) + travel_time

            # Schedule hospital arrival
            self.schedule_event(
                time=self.current_time + travel_time,
                event_type="PATIENT_ARRIVED_AT_HOSPITAL",
                patient_id=patient["id"],
                resource_id=amb_result["ambulance_id"],
            )
        elif amb_result.get("status") == "WALK_IN":
            self.schedule_event(
                time=self.current_time,
                event_type="PATIENT_ARRIVED_AT_HOSPITAL",
                patient_id=patient["id"],
            )

    def _handle_patient_arrived_at_hospital(self, event: SimEvent, env: Dict[str, Any]):
        patient = self.patients.get(event.patient_id)
        if not patient:
            return

        patient["hospital_arrival_time"] = self.current_time
        if patient["workflow_state"] == WorkflowState.IN_TRANSIT.value:
            self.coordinator.transition_patient(
                patient, WorkflowState.ARRIVED, self.current_time
            )
        self.coordinator.transition_patient(
            patient, WorkflowState.ADMITTED, self.current_time
        )

        # Release ambulance if one transported the patient
        if event.resource_id:
            self.coordinator.ambulance_agent.release_ambulance(
                event.resource_id,
                self.ambulances,
                self.current_time,
                expected_patient_id=patient["id"],
            )
            self.coordinator.os_manager.ambulance_semaphore.release(patient["id"])
            # Retry any waiting ambulances
            self._retry_waiting_ambulances(env)

        # Request Doctor
        doc_res = self.coordinator.request_doctor_allocation(patient, env)
        if doc_res.get("status") == "ALLOCATED":
            exam_duration = 10.0
            # Track doctor busy time
            for d in self.doctors:
                if d["id"] == doc_res["doctor_id"]:
                    d["total_busy_time"] = d.get("total_busy_time", 0.0) + exam_duration

            self.schedule_event(
                time=self.current_time + exam_duration,
                event_type="DOCTOR_EXAM_COMPLETED",
                patient_id=patient["id"],
                resource_id=doc_res["doctor_id"],
            )

    def _handle_doctor_exam_completed(self, event: SimEvent, env: Dict[str, Any]):
        patient = self.patients.get(event.patient_id)
        if not patient:
            return

        if event.resource_id:
            self.coordinator.doctor_agent.release_doctor(
                event.resource_id,
                self.doctors,
                self.current_time,
                expected_patient_id=patient["id"],
            )
            self.coordinator.release_doctor_mutex(
                event.resource_id, patient["id"], self.current_time
            )
            self._retry_waiting_doctors(env)

        # Check if diagnostic required
        if patient.get("required_diagnostic"):
            diag_res = self.coordinator.request_diagnostic_allocation(patient, env)
            if diag_res.get("status") == "ALLOCATED":
                duration = diag_res.get("duration", 15.0)
                for diag in self.diagnostic_resources:
                    if diag["id"] == diag_res["resource_id"]:
                        diag["total_busy_time"] = diag.get("total_busy_time", 0.0) + duration

                self.schedule_event(
                    time=self.current_time + duration,
                    event_type="DIAGNOSTIC_COMPLETED",
                    patient_id=patient["id"],
                    resource_id=diag_res["resource_id"],
                )
        else:
            # Check ICU or proceed to simulated treatment
            self._route_after_exam_or_diagnostics(patient, env)

    def _handle_diagnostic_completed(self, event: SimEvent, env: Dict[str, Any]):
        patient = self.patients.get(event.patient_id)
        if not patient:
            return

        patient["diagnostic_end_time"] = self.current_time
        self.coordinator.transition_patient(
            patient, WorkflowState.DIAGNOSTICS_COMPLETED, self.current_time
        )

        # Release diagnostic resource
        if event.resource_id:
            self.coordinator.diagnostic_agent.release_diagnostic(
                event.resource_id,
                self.diagnostic_resources,
                self.current_time,
                expected_patient_id=patient["id"],
            )
            self.coordinator.release_diagnostic_mutex(event.resource_id, patient["id"], self.current_time)
            self._retry_waiting_diagnostics(env)

        self._route_after_exam_or_diagnostics(patient, env)

    def _route_after_exam_or_diagnostics(self, patient: Dict[str, Any], env: Dict[str, Any]):
        """Decide whether ICU or regular emergency treatment comes next."""
        treatment_duration = 15.0 if patient.get("priority") in ("P1", "P2") else 10.0

        if patient.get("requires_icu"):
            icu_res = self.coordinator.request_icu_allocation(patient, env)
            if icu_res.get("status") == "ALLOCATED":
                for bed in self.icu_beds:
                    if bed["id"] == icu_res["icu_bed_id"]:
                        bed["total_busy_time"] = bed.get("total_busy_time", 0.0) + treatment_duration

                self.coordinator.transition_patient(
                    patient, WorkflowState.TREATMENT_SIMULATED, self.current_time
                )
                patient["treatment_start_time"] = self.current_time
                self.schedule_event(
                    time=self.current_time + treatment_duration,
                    event_type="TREATMENT_COMPLETED",
                    patient_id=patient["id"],
                )
        else:
            self.coordinator.transition_patient(
                patient, WorkflowState.TREATMENT_SIMULATED, self.current_time
            )
            patient["treatment_start_time"] = self.current_time
            self.schedule_event(
                time=self.current_time + treatment_duration,
                event_type="TREATMENT_COMPLETED",
                patient_id=patient["id"],
            )

    def _handle_treatment_completed(self, event: SimEvent, env: Dict[str, Any]):
        patient = self.patients.get(event.patient_id)
        if not patient:
            return

        patient["completion_time"] = self.current_time
        self.coordinator.transition_patient(
            patient, WorkflowState.COMPLETED, self.current_time
        )

        # Release ICU bed if occupied
        bed_id = patient.get("assigned_icu_bed_id")
        if bed_id:
            self.coordinator.icu_agent.release_bed(
                bed_id,
                self.icu_beds,
                self.current_time,
                expected_patient_id=patient["id"],
            )
            self.coordinator.release_icu_semaphore(patient["id"])
            self._retry_waiting_icu(env)

        self.schedule_event(
            time=self.current_time + 1.0,
            event_type="PATIENT_DISCHARGED",
            patient_id=patient["id"],
        )

    def _handle_patient_discharged(self, event: SimEvent, env: Dict[str, Any]):
        patient = self.patients.get(event.patient_id)
        if patient:
            self.coordinator.transition_patient(
                patient, WorkflowState.DISCHARGED, self.current_time
            )
            self.coordinator.complete_patient_process(patient["id"], self.current_time)
            self.coordinator.emit_event(
                simulation_time=self.current_time,
                event_type="PATIENT_DISCHARGED",
                description=f"Patient {patient['name']} ({patient['id']}) discharged from emergency department.",
                patient_id=patient["id"],
            )

    # -------------------------------------------------------------
    # Waiting Queue Retries
    # -------------------------------------------------------------

    def _retry_waiting_ambulances(self, env: Dict[str, Any]):
        sorted_pids = self.coordinator.sort_waiting_queue(
            self.coordinator.waiting_ambulances,
            self.patients,
            self.current_time,
            request_time_field="arrival_time",
        )
        for pid in sorted_pids:
            p = self.patients[pid]
            res = self.coordinator.request_ambulance_allocation(p, env)
            if res.get("status") == "ALLOCATED":
                self.coordinator.transition_patient(
                    p, WorkflowState.IN_TRANSIT, self.current_time
                )
                travel_time = res.get("travel_time", 5.0)
                for amb in self.ambulances:
                    if amb["id"] == res["ambulance_id"]:
                        amb["total_busy_time"] = amb.get("total_busy_time", 0.0) + travel_time
                self.schedule_event(
                    time=self.current_time + travel_time,
                    event_type="PATIENT_ARRIVED_AT_HOSPITAL",
                    patient_id=pid,
                    resource_id=res["ambulance_id"],
                )
                break

    def _retry_waiting_doctors(self, env: Dict[str, Any]):
        sorted_pids = self.coordinator.sort_waiting_queue(
            self.coordinator.waiting_doctors,
            self.patients,
            self.current_time,
            request_time_field="doctor_request_time",
        )
        for pid in sorted_pids:
            p = self.patients[pid]
            res = self.coordinator.request_doctor_allocation(p, env)
            if res.get("status") == "ALLOCATED":
                exam_duration = 10.0
                for d in self.doctors:
                    if d["id"] == res["doctor_id"]:
                        d["total_busy_time"] = d.get("total_busy_time", 0.0) + exam_duration
                self.schedule_event(
                    time=self.current_time + exam_duration,
                    event_type="DOCTOR_EXAM_COMPLETED",
                    patient_id=pid,
                    resource_id=res["doctor_id"],
                )
                break

    def _retry_waiting_diagnostics(self, env: Dict[str, Any]):
        sorted_pids = self.coordinator.sort_waiting_queue(
            self.coordinator.waiting_diagnostics,
            self.patients,
            self.current_time,
            request_time_field="diagnostic_request_time",
        )
        for pid in sorted_pids:
            p = self.patients[pid]
            res = self.coordinator.request_diagnostic_allocation(p, env)
            if res.get("status") == "ALLOCATED":
                duration = res.get("duration", 15.0)
                for diag in self.diagnostic_resources:
                    if diag["id"] == res["resource_id"]:
                        diag["total_busy_time"] = diag.get("total_busy_time", 0.0) + duration
                self.schedule_event(
                    time=self.current_time + duration,
                    event_type="DIAGNOSTIC_COMPLETED",
                    patient_id=pid,
                    resource_id=res["resource_id"],
                )
                break

    def _retry_waiting_icu(self, env: Dict[str, Any]):
        sorted_pids = self.coordinator.sort_waiting_queue(
            self.coordinator.waiting_icu,
            self.patients,
            self.current_time,
            request_time_field="icu_request_time",
        )
        for pid in sorted_pids:
            p = self.patients[pid]
            res = self.coordinator.request_icu_allocation(p, env)
            if res.get("status") == "ALLOCATED":
                treatment_duration = 15.0
                for bed in self.icu_beds:
                    if bed["id"] == res["icu_bed_id"]:
                        bed["total_busy_time"] = bed.get("total_busy_time", 0.0) + treatment_duration
                self.coordinator.transition_patient(
                    p, WorkflowState.TREATMENT_SIMULATED, self.current_time
                )
                p["treatment_start_time"] = self.current_time
                self.schedule_event(
                    time=self.current_time + treatment_duration,
                    event_type="TREATMENT_COMPLETED",
                    patient_id=pid,
                )
                break

    def get_metrics(self) -> MetricsSummary:
        """Compute simulation metrics over current state."""
        metrics = calculate_simulation_metrics(
            patients=list(self.patients.values()),
            ambulances=self.ambulances,
            doctors=self.doctors,
            diagnostic_resources=self.diagnostic_resources,
            icu_beds=self.icu_beds,
            conflict_count=self.coordinator.conflict_count,
            simulation_duration=self.current_time,
            strategy=self.strategy.value,
        )
        return metrics
