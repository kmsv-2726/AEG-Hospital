"""
Hospital Coordinator Agent: Central cooperative orchestrator for multi-agent workflows,
message routing, queue retries, conflict management, and OS resource allocation.
"""
from typing import Dict, Any, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.agents.triage_agent import TriageAgent
from backend.app.agents.ambulance_agent import AmbulanceAgent
from backend.app.agents.doctor_agent import DoctorAgent
from backend.app.agents.diagnostic_agent import DiagnosticAgent
from backend.app.agents.icu_agent import ICUAgent
from backend.app.coordinator.message_bus import AgentMessageBus
from backend.app.models.os_primitives import HospitalOSManager, ProcessState
from backend.app.workflows.patient_workflow import PatientWorkflowFSM, WorkflowTransitionError
from backend.app.models.enums import (
    WorkflowState,
    MessageType,
    AllocationStrategy,
    PriorityLevel,
)
from backend.app.schemas.hospital_schemas import AgentMessageSchema, SimulationEventSchema

class HospitalCoordinator(BaseAgent):
    """
    Coordinates the cooperative Multi-Agent emergency workflow:
    - Oversees AgentMessageBus facilitating autonomous structured communication.
    - Employs OS resource allocation principles: Process Control Blocks (PCBs),
      Counting Semaphores (ICU, Ambulance), Resource Mutexes (Doctors, Scanners),
      and Priority Preemption with Dynamic Aging.
    - Resolves conflicts by maintaining prioritized waiting queues.
    - Dispatches state updates and triggers waiting-queue reconsiderations upon resource releases.
    """

    def __init__(
        self,
        agent_id: str = "AGENT-COORD",
        name: str = "HospitalCoordinator",
        strategy: AllocationStrategy = AllocationStrategy.PRIORITY_AWARE,
    ):
        super().__init__(agent_id=agent_id, name=name, role="Master Workflow Coordinator")
        self.strategy = strategy
        
        # Inter-Agent Message Bus
        self.message_bus = AgentMessageBus()
        self.set_message_bus(self.message_bus)

        # Specialized autonomous agents
        self.triage_agent = TriageAgent()
        self.ambulance_agent = AmbulanceAgent()
        self.doctor_agent = DoctorAgent()
        self.diagnostic_agent = DiagnosticAgent()
        self.icu_agent = ICUAgent()

        # Connect agents to the shared message bus
        for ag in self.specialized_agents:
            ag.set_message_bus(self.message_bus)

        # OS Resource & Process Control Manager
        self.os_manager = HospitalOSManager()

        self.waiting_ambulances: List[str] = []  # Patient IDs waiting for ambulance
        self.waiting_doctors: List[str] = []     # Patient IDs waiting for doctor
        self.waiting_diagnostics: List[str] = [] # Patient IDs waiting for diagnostic
        self.waiting_icu: List[str] = []         # Patient IDs waiting for ICU bed
        self.conflict_count: int = 0

    @property
    def specialized_agents(self) -> List[BaseAgent]:
        return [
            self.triage_agent,
            self.ambulance_agent,
            self.doctor_agent,
            self.diagnostic_agent,
            self.icu_agent,
        ]

    def sync_os_resources(self, env: Dict[str, Any]):
        """Synchronize OS mutexes and semaphores with live simulation resources."""
        self.os_manager.sync_resources(
            doctors=env.get("doctors", []),
            diagnostics=env.get("diagnostic_resources", []),
            icu_beds=env.get("icu_beds", []),
            ambulances=env.get("ambulances", []),
        )

    def perceive(self, environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate high-level overview of active workflows, OS states, and waiting queues."""
        sim_time = environment_state.get("simulation_time", 0.0)
        self.sync_os_resources(environment_state)
        return {
            "simulation_time": sim_time,
            "waiting_ambulances": list(self.waiting_ambulances),
            "waiting_doctors": list(self.waiting_doctors),
            "waiting_diagnostics": list(self.waiting_diagnostics),
            "waiting_icu": list(self.waiting_icu),
            "os_metrics": self.os_manager.get_os_metrics(sim_time),
        }

    def decide(self, percepts: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinator determines if waiting queues need reconsideration."""
        return {"action": "MONITOR_QUEUES"}

    def act(self, decision: Dict[str, Any], environment_state: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ACTIVE"}

    def transition_patient(
        self,
        patient: Dict[str, Any],
        next_state: WorkflowState,
        simulation_time: float,
    ) -> None:
        """Validate, apply, and log one patient workflow transition."""
        patient_id = patient["id"]
        current_state = WorkflowState(patient["workflow_state"])
        if current_state == next_state:
            return
        try:
            PatientWorkflowFSM.validate_transition(current_state, next_state, patient_id)
        except WorkflowTransitionError as error:
            self.emit_event(
                simulation_time=simulation_time,
                event_type="WORKFLOW_TRANSITION_REJECTED",
                description=str(error),
                patient_id=patient_id,
                outcome="REJECTED",
            )
            raise

        patient["workflow_state"] = next_state.value
        self.emit_event(
            simulation_time=simulation_time,
            event_type="WORKFLOW_TRANSITION",
            description=f"Patient {patient_id} transitioned from {current_state.value} to {next_state.value}.",
            patient_id=patient_id,
            outcome="SUCCESS",
        )

    def record_decision(
        self,
        patient: Dict[str, Any],
        agent: str,
        action: str,
        status: str,
        reason: str,
        simulation_time: float,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append an actual agent activation/skip/result to the patient trace."""
        trace = patient.setdefault("decision_trace", [])
        trace.append({
            "sequence": len(trace) + 1,
            "simulation_time": simulation_time,
            "agent": agent,
            "action": action,
            "status": status,
            "description": reason,
            "details": details or {},
        })

    def record_reservation_result(
        self,
        patient: Dict[str, Any],
        agent: str,
        result: Dict[str, Any],
        resources: List[Dict[str, Any]],
        resource_id: Optional[str],
        simulation_time: float,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        resource = next(
            (item for item in resources if item.get("id") == resource_id), None
        )
        status = result.get("status", "UNKNOWN")
        self.record_decision(
            patient,
            agent,
            "RESERVE_RESOURCE",
            status,
            result.get("reason") or (
                f"Allocation result: {status}."
                if status != "ALLOCATED"
                else f"Resource {resource_id} reserved for patient {patient['id']}."
            ),
            simulation_time,
            {
                **(details or {}),
                "resource_id": resource_id,
                "availability_after": resource.get("status") if resource else None,
                "owner_after": resource.get("current_patient_id") if resource else None,
                "allocation_status": status,
            },
        )

    def _refresh_diagnostic_queue_lengths(
        self,
        patients: Dict[str, Dict[str, Any]],
        diagnostic_resources: List[Dict[str, Any]],
    ) -> None:
        counts: Dict[str, int] = {}
        for patient_id in self.waiting_diagnostics:
            patient = patients.get(patient_id, {})
            category = patient.get("required_diagnostic")
            if category:
                counts[category] = counts.get(category, 0) + 1
        for resource in diagnostic_resources:
            resource["queue_length"] = counts.get(resource.get("category"), 0)

    def sort_waiting_queue(
        self,
        queue: List[str],
        patients: Dict[str, Dict[str, Any]],
        current_time: float = 0.0,
        request_time_field: str = "arrival_time",
    ) -> List[str]:
        """
        Sort waiting requests:
        - In FIFO mode: Sort by arrival_time / request_time.
        - In PRIORITY_AWARE mode: Sort by Dynamic OS Priority (considering aging) or base priority, then arrival_time.
        """
        def request_order(patient_id: str):
            patient = patients.get(patient_id, {})
            request_time = patient.get(request_time_field)
            if request_time is None:
                request_time = patient.get("arrival_time", 0.0)
            return request_time, patient_id

        if self.strategy == AllocationStrategy.FIFO:
            return sorted(queue, key=request_order)

        self.os_manager.apply_aging(current_time)
        priority_order = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
        return sorted(
            queue,
            key=lambda pid: (
                self.os_manager.pcbs[pid].dynamic_priority
                if pid in self.os_manager.pcbs
                else priority_order.get(patients.get(pid, {}).get("priority", "P3"), 3),
                *request_order(pid),
            ),
        )

    # -------------------------------------------------------------
    # Step-by-Step Autonomous Workflow Transitions
    # -------------------------------------------------------------

    def handle_patient_registration(
        self, patient: Dict[str, Any], env: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 1: Patient Registered -> OS PCB creation -> Delegate to Triage."""
        sim_time = env.get("simulation_time", 0.0)
        pid = patient["id"]
        patient.setdefault("workflow_state", WorkflowState.REGISTERED.value)

        # Register in OS Manager
        self.sync_os_resources(env)
        self.os_manager.register_patient_process(patient, sim_time)

        self.emit_event(
            simulation_time=sim_time,
            event_type="PATIENT_REGISTERED",
            description=f"Patient {patient['name']} ({pid}) registered. Initialized OS PCB and entered Intake.",
            patient_id=pid,
        )

        # Autonomous communication via Message Bus
        self.send_message(
            receiver="TriageAgent",
            message_type=MessageType.PATIENT_REGISTERED,
            patient_id=pid,
            simulation_time=sim_time,
            payload={"patient": patient, "severity_category": patient.get("severity_category")},
        )

        # Delegate to Triage Agent
        triage_env = {"patient": patient, "simulation_time": sim_time}
        percepts = self.triage_agent.perceive(triage_env)
        decision = self.triage_agent.decide(percepts)
        triage_result = self.triage_agent.act(decision, triage_env)

        # Update patient priority and transition PCB to READY
        patient["priority"] = triage_result["priority"]
        patient["triage_reason"] = triage_result["reason"]
        patient["triage_requires_review"] = triage_result.get("requires_review", False)
        pcb = self.os_manager.pcbs.get(pid)
        if pcb:
            pcb.base_priority = patient["priority"]
            pcb.numeric_priority = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}.get(patient["priority"], 3)
            pcb.dynamic_priority = float(pcb.numeric_priority)
        self.record_decision(
            patient,
            "TriageAgent",
            "CLASSIFY",
            "REVIEW_REQUIRED" if triage_result.get("requires_review") else "COMPLETED",
            triage_result["reason"],
            sim_time,
            {"priority": patient["priority"], "mode": triage_result.get("mode"),
             "requires_review": triage_result.get("requires_review", False), "patient": {
                "severity_category": patient.get("severity_category"),
                "chief_complaint": patient.get("chief_complaint"),
                "symptoms": patient.get("symptoms"),
                "heart_rate": patient.get("heart_rate"),
                "oxygen_saturation": patient.get("oxygen_saturation"),
                "blood_pressure": patient.get("blood_pressure"),
            }},
        )
        if not patient.get("required_diagnostic"):
            self.record_decision(
                patient,
                "DiagnosticAgent",
                "ALLOCATION_SKIPPED",
                "SKIPPED",
                "Intake plan contains no diagnostic requirement; diagnostic equipment will not be reserved.",
                sim_time,
            )
        if not patient.get("requires_icu"):
            self.record_decision(
                patient,
                "ICUAgent",
                "ALLOCATION_SKIPPED",
                "SKIPPED",
                "Intake plan does not require ICU care; no bed request will be made.",
                sim_time,
            )
        self.transition_patient(patient, WorkflowState.TRIAGED, sim_time)
        self.os_manager.transition_process(pid, ProcessState.READY, sim_time)

        self.emit_event(
            simulation_time=sim_time,
            event_type="WORKFLOW_UPDATED",
            description=f"Patient {pid} triaged as {patient['priority']}. State transitioned to READY.",
            patient_id=pid,
        )

        return triage_result

    def request_ambulance_allocation(
        self, patient: Dict[str, Any], env: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 2: Request Ambulance from AmbulanceAgent."""
        sim_time = env.get("simulation_time", 0.0)
        pid = patient["id"]

        if not patient.get("requires_ambulance", True):
            self.record_decision(
                patient, "AmbulanceAgent", "ALLOCATION_SKIPPED", "SKIPPED",
                "Patient is configured as a walk-in; ambulance dispatch is not required.", sim_time,
            )
            self.transition_patient(patient, WorkflowState.ARRIVED, sim_time)
            patient["hospital_arrival_time"] = sim_time
            self.emit_event(
                simulation_time=sim_time,
                event_type="PATIENT_ARRIVED",
                description=f"Patient {pid} is walk-in / ambulatory. Arrived at hospital.",
                patient_id=pid,
            )
            return {"status": "WALK_IN", "travel_time": 0.0}

        # Autonomous request message to AmbulanceAgent
        self.send_message(
            receiver="AmbulanceAgent",
            message_type=MessageType.AMBULANCE_REQUEST,
            patient_id=pid,
            simulation_time=sim_time,
            payload={"patient": patient, "priority": patient.get("priority", "P3")},
        )

        amb_env = {
            "patient": patient,
            "ambulances": env.get("ambulances", []),
            "simulation_time": sim_time,
        }
        percepts = self.ambulance_agent.perceive(amb_env)
        decision = self.ambulance_agent.decide(percepts)
        self.record_decision(
            patient, "AmbulanceAgent", "EVALUATE_CANDIDATES",
            "CANDIDATES_FOUND" if decision.get("action") == "ALLOCATE" else "WAITING",
            decision.get("reason", "Candidate evaluation completed."), sim_time,
            {"candidates": decision.get("candidates", []), "selected_resource": decision.get("ambulance", {}).get("id"),
             "required_equipment": patient.get("required_equipment", []), "action": decision.get("action")},
        )
        result = self.ambulance_agent.act(decision, amb_env)

        if result["status"] == "ALLOCATED":
            patient["assigned_ambulance_id"] = result["ambulance_id"]
            self.transition_patient(patient, WorkflowState.AMBULANCE_ASSIGNED, sim_time)
            patient["ambulance_dispatch_time"] = sim_time
            self.os_manager.ambulance_semaphore.acquire(pid, result["ambulance_id"])
            self.os_manager.transition_process(
                pid, ProcessState.RUNNING, sim_time, resource=result["ambulance_id"]
            )
            if pid in self.waiting_ambulances:
                self.waiting_ambulances.remove(pid)
        else:
            self.transition_patient(patient, WorkflowState.WAITING_FOR_AMBULANCE, sim_time)
            self.conflict_count += 1
            if pid not in self.waiting_ambulances:
                self.os_manager.transition_process(pid, ProcessState.BLOCKED, sim_time, resource="Ambulance")
                self.waiting_ambulances.append(pid)

        self.record_reservation_result(
            patient,
            "AmbulanceAgent",
            result,
            env.get("ambulances", []),
            result.get("ambulance_id"),
            sim_time,
            {"travel_time": result.get("travel_time"), "score": result.get("score")},
        )

        return result

    def request_doctor_allocation(
        self, patient: Dict[str, Any], env: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 3: Request Doctor from DoctorAgent."""
        sim_time = env.get("simulation_time", 0.0)
        pid = patient["id"]
        patient.setdefault("doctor_request_time", sim_time)

        # Autonomous request message to DoctorAgent
        self.send_message(
            receiver="DoctorAgent",
            message_type=MessageType.DOCTOR_REQUEST,
            patient_id=pid,
            simulation_time=sim_time,
            payload={"patient": patient, "specialty": patient.get("required_specialty")},
        )

        doc_env = {
            "patient": patient,
            "doctors": env.get("doctors", []),
            "simulation_time": sim_time,
        }
        percepts = self.doctor_agent.perceive(doc_env)
        decision = self.doctor_agent.decide(percepts)
        self.record_decision(
            patient, "DoctorAgent", "MATCH_SPECIALTY",
            "CANDIDATES_FOUND" if decision.get("action") == "ALLOCATE" else "WAITING",
            decision.get("reason", "Candidate evaluation completed."), sim_time,
            {"candidates": decision.get("candidates", []), "selected_resource": decision.get("doctor", {}).get("id"),
             "required_specialty": patient.get("required_specialty"), "action": decision.get("action")},
        )
        result = self.doctor_agent.act(decision, doc_env)

        if result["status"] == "ALLOCATED":
            doc_id = result["doctor_id"]
            patient["assigned_doctor_id"] = doc_id
            patient["doctor_assignment_time"] = sim_time
            self.transition_patient(patient, WorkflowState.DOCTOR_ASSIGNED, sim_time)
            
            # OS Mutex Acquisition & Transition to RUNNING
            if doc_id in self.os_manager.doctor_mutexes:
                self.os_manager.doctor_mutexes[doc_id].acquire(pid, sim_time)
            self.os_manager.transition_process(pid, ProcessState.RUNNING, sim_time, resource=doc_id)

            if pid in self.waiting_doctors:
                self.waiting_doctors.remove(pid)
        else:
            self.transition_patient(patient, WorkflowState.WAITING_FOR_DOCTOR, sim_time)
            self.conflict_count += 1
            # OS Blocked Queue transition
            if pid not in self.waiting_doctors:
                self.os_manager.transition_process(pid, ProcessState.BLOCKED, sim_time, resource=f"Doctor ({patient.get('required_specialty')})")
                self.waiting_doctors.append(pid)

            self.record_reservation_result(
                patient,
                "DoctorAgent",
                result,
                env.get("doctors", []),
                result.get("doctor_id"),
                sim_time,
                {"specialty": patient.get("required_specialty"), "score": decision.get("score")},
            )

        return result

    def request_diagnostic_allocation(
        self, patient: Dict[str, Any], env: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 4: Request Diagnostic resource from DiagnosticAgent."""
        sim_time = env.get("simulation_time", 0.0)
        pid = patient["id"]
        category = patient.get("required_diagnostic")

        if not category:
            return {"status": "NOT_REQUIRED"}

        patient.setdefault("diagnostic_request_time", sim_time)

        # Autonomous request message to DiagnosticAgent
        self.send_message(
            receiver="DiagnosticAgent",
            message_type=MessageType.DIAGNOSTIC_REQUEST,
            patient_id=pid,
            simulation_time=sim_time,
            payload={"patient": patient, "category": category},
        )

        diag_env = {
            "patient": patient,
            "diagnostic_resources": env.get("diagnostic_resources", []),
            "simulation_time": sim_time,
        }
        percepts = self.diagnostic_agent.perceive(diag_env)
        decision = self.diagnostic_agent.decide(percepts)
        self.record_decision(
            patient, "DiagnosticAgent", "MATCH_DIAGNOSTIC",
            "CANDIDATES_FOUND" if decision.get("action") == "ALLOCATE" else "WAITING",
            decision.get("reason", "Candidate evaluation completed."), sim_time,
            {"candidates": decision.get("candidates", []), "selected_resource": decision.get("resource", {}).get("id"),
             "required_diagnostic": category, "action": decision.get("action")},
        )
        result = self.diagnostic_agent.act(decision, diag_env)

        if result["status"] == "ALLOCATED":
            res_id = result["resource_id"]
            patient["assigned_diagnostic_id"] = res_id
            patient["diagnostic_start_time"] = sim_time
            self.transition_patient(patient, WorkflowState.DIAGNOSTICS_IN_PROGRESS, sim_time)
            
            # OS Scanner Mutex Acquisition
            if res_id in self.os_manager.diagnostic_mutexes:
                self.os_manager.diagnostic_mutexes[res_id].acquire(pid, sim_time)
            self.os_manager.transition_process(pid, ProcessState.RUNNING, sim_time, resource=res_id)

            if pid in self.waiting_diagnostics:
                self.waiting_diagnostics.remove(pid)
        else:
            self.transition_patient(patient, WorkflowState.WAITING_FOR_DIAGNOSTIC, sim_time)
            self.conflict_count += 1
            if pid not in self.waiting_diagnostics:
                self.os_manager.transition_process(pid, ProcessState.BLOCKED, sim_time, resource=f"Scanner ({category})")
                self.waiting_diagnostics.append(pid)
        self._refresh_diagnostic_queue_lengths(
            env.get("patients", {pid: patient}), env.get("diagnostic_resources", [])
        )
        self.record_reservation_result(
            patient,
            "DiagnosticAgent",
            result,
            env.get("diagnostic_resources", []),
            result.get("resource_id"),
            sim_time,
            {"category": category, "duration": result.get("duration")},
        )

        return result

    def request_icu_allocation(
        self, patient: Dict[str, Any], env: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 5: Request ICU bed from ICUAgent."""
        sim_time = env.get("simulation_time", 0.0)
        pid = patient["id"]

        if not patient.get("requires_icu", False):
            return {"status": "NOT_REQUIRED"}

        patient.setdefault("icu_request_time", sim_time)

        # Autonomous request message to ICUAgent
        self.send_message(
            receiver="ICUAgent",
            message_type=MessageType.ICU_REQUEST,
            patient_id=pid,
            simulation_time=sim_time,
            payload={"patient": patient, "priority": patient.get("priority", "P1")},
        )

        icu_env = {
            "patient": patient,
            "icu_beds": env.get("icu_beds", []),
            "simulation_time": sim_time,
        }
        percepts = self.icu_agent.perceive(icu_env)
        decision = self.icu_agent.decide(percepts)
        self.record_decision(
            patient, "ICUAgent", "MATCH_BED",
            "CANDIDATES_FOUND" if decision.get("action") == "ALLOCATE" else "WAITING",
            decision.get("reason", "Candidate evaluation completed."), sim_time,
            {"candidates": decision.get("candidates", []), "selected_resource": decision.get("bed", {}).get("id"),
             "required_equipment": patient.get("required_icu_equipment", []), "action": decision.get("action")},
        )
        result = self.icu_agent.act(decision, icu_env)

        if result["status"] == "ALLOCATED":
            bed_id = result["icu_bed_id"]
            patient["assigned_icu_bed_id"] = bed_id
            patient["icu_reservation_time"] = sim_time
            self.transition_patient(patient, WorkflowState.ICU_ALLOCATED, sim_time)

            # OS ICU Counting Semaphore Acquisition
            self.os_manager.icu_semaphore.acquire(pid, bed_id)
            self.os_manager.transition_process(pid, ProcessState.RUNNING, sim_time, resource=bed_id)

            if pid in self.waiting_icu:
                self.waiting_icu.remove(pid)
        else:
            self.transition_patient(patient, WorkflowState.WAITING_FOR_ICU, sim_time)
            self.conflict_count += 1
            if pid not in self.waiting_icu:
                self.os_manager.transition_process(pid, ProcessState.BLOCKED, sim_time, resource="ICU Bed")
                self.waiting_icu.append(pid)

            self.record_reservation_result(
                patient,
                "ICUAgent",
                result,
                env.get("icu_beds", []),
                result.get("icu_bed_id"),
                sim_time,
                {"required_equipment": patient.get("required_icu_equipment", [])},
            )

        return result

    def release_doctor_mutex(self, doc_id: str, pid: str, sim_time: float):
        """Release OS Doctor Mutex."""
        if doc_id in self.os_manager.doctor_mutexes:
            self.os_manager.doctor_mutexes[doc_id].release(pid, sim_time)

    def release_diagnostic_mutex(self, res_id: str, pid: str, sim_time: float):
        """Release OS Scanner Mutex."""
        if res_id in self.os_manager.diagnostic_mutexes:
            self.os_manager.diagnostic_mutexes[res_id].release(pid, sim_time)

    def release_icu_semaphore(self, pid: str):
        """Release OS ICU Bed Semaphore permit."""
        self.os_manager.icu_semaphore.release(pid)

    def complete_patient_process(self, pid: str, sim_time: float):
        """Transition Patient PCB to TERMINATED upon discharge."""
        self.os_manager.transition_process(pid, ProcessState.TERMINATED, sim_time)
