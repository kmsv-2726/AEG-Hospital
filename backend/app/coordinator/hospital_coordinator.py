"""
Hospital Coordinator Agent: Central cooperative orchestrator for multi-agent workflows,
message routing, queue retries, and conflict management.
"""
from typing import Dict, Any, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.agents.triage_agent import TriageAgent
from backend.app.agents.ambulance_agent import AmbulanceAgent
from backend.app.agents.doctor_agent import DoctorAgent
from backend.app.agents.diagnostic_agent import DiagnosticAgent
from backend.app.agents.icu_agent import ICUAgent
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
    - Delegates resource allocation decisions to specialized agents.
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
        self.triage_agent = TriageAgent()
        self.ambulance_agent = AmbulanceAgent()
        self.doctor_agent = DoctorAgent()
        self.diagnostic_agent = DiagnosticAgent()
        self.icu_agent = ICUAgent()

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

    def perceive(self, environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate high-level overview of active workflows and waiting queues."""
        return {
            "simulation_time": environment_state.get("simulation_time", 0.0),
            "waiting_ambulances": list(self.waiting_ambulances),
            "waiting_doctors": list(self.waiting_doctors),
            "waiting_diagnostics": list(self.waiting_diagnostics),
            "waiting_icu": list(self.waiting_icu),
        }

    def decide(self, percepts: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinator determines if waiting queues need reconsideration."""
        return {"action": "MONITOR_QUEUES"}

    def act(self, decision: Dict[str, Any], environment_state: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ACTIVE"}

    def sort_waiting_queue(self, queue: List[str], patients: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        Sort waiting requests:
        - In FIFO mode: Sort by arrival_time / request_time.
        - In PRIORITY_AWARE mode: Sort by Priority (P1 > P2 > P3 > P4), then arrival_time.
        """
        if self.strategy == AllocationStrategy.FIFO:
            return sorted(queue, key=lambda pid: patients.get(pid, {}).get("arrival_time", 0.0))

        priority_order = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
        return sorted(
            queue,
            key=lambda pid: (
                priority_order.get(patients.get(pid, {}).get("priority", "P3"), 3),
                patients.get(pid, {}).get("arrival_time", 0.0),
            ),
        )

    # -------------------------------------------------------------
    # Step-by-Step Workflow Transitions
    # -------------------------------------------------------------

    def handle_patient_registration(
        self, patient: Dict[str, Any], env: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 1: Patient Registered -> Perform Triage."""
        sim_time = env.get("simulation_time", 0.0)
        pid = patient["id"]
        patient["workflow_state"] = WorkflowState.REGISTERED.value

        self.emit_event(
            simulation_time=sim_time,
            event_type="PATIENT_REGISTERED",
            description=f"Patient {patient['name']} ({pid}) registered in Emergency ED.",
            patient_id=pid,
        )

        # Delegate to Triage Agent
        triage_env = {"patient": patient, "simulation_time": sim_time}
        percepts = self.triage_agent.perceive(triage_env)
        decision = self.triage_agent.decide(percepts)
        triage_result = self.triage_agent.act(decision, triage_env)

        # Update patient priority
        patient["priority"] = triage_result["priority"]
        patient["workflow_state"] = WorkflowState.TRIAGED.value

        self.emit_event(
            simulation_time=sim_time,
            event_type="WORKFLOW_UPDATED",
            description=f"Patient {pid} transitioned to TRIAGED ({patient['priority']}).",
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
            patient["workflow_state"] = WorkflowState.ARRIVED.value
            patient["hospital_arrival_time"] = sim_time
            self.emit_event(
                simulation_time=sim_time,
                event_type="PATIENT_ARRIVED",
                description=f"Patient {pid} is walk-in / ambulatory. Arrived at hospital.",
                patient_id=pid,
            )
            return {"status": "WALK_IN", "travel_time": 0.0}

        amb_env = {
            "patient": patient,
            "ambulances": env.get("ambulances", []),
            "simulation_time": sim_time,
        }
        percepts = self.ambulance_agent.perceive(amb_env)
        decision = self.ambulance_agent.decide(percepts)
        result = self.ambulance_agent.act(decision, amb_env)

        if result["status"] == "ALLOCATED":
            patient["assigned_ambulance_id"] = result["ambulance_id"]
            patient["workflow_state"] = WorkflowState.AMBULANCE_ASSIGNED.value
            patient["ambulance_dispatch_time"] = sim_time
            if pid in self.waiting_ambulances:
                self.waiting_ambulances.remove(pid)
        else:
            patient["workflow_state"] = WorkflowState.WAITING_FOR_AMBULANCE.value
            self.conflict_count += 1
            if pid not in self.waiting_ambulances:
                self.waiting_ambulances.append(pid)

        return result

    def request_doctor_allocation(
        self, patient: Dict[str, Any], env: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 3: Request Doctor from DoctorAgent."""
        sim_time = env.get("simulation_time", 0.0)
        pid = patient["id"]
        patient["doctor_request_time"] = sim_time

        doc_env = {
            "patient": patient,
            "doctors": env.get("doctors", []),
            "simulation_time": sim_time,
        }
        percepts = self.doctor_agent.perceive(doc_env)
        decision = self.doctor_agent.decide(percepts)
        result = self.doctor_agent.act(decision, doc_env)

        if result["status"] == "ALLOCATED":
            patient["assigned_doctor_id"] = result["doctor_id"]
            patient["doctor_assignment_time"] = sim_time
            patient["workflow_state"] = WorkflowState.DOCTOR_ASSIGNED.value
            if pid in self.waiting_doctors:
                self.waiting_doctors.remove(pid)
        else:
            patient["workflow_state"] = WorkflowState.WAITING_FOR_DOCTOR.value
            self.conflict_count += 1
            if pid not in self.waiting_doctors:
                self.waiting_doctors.append(pid)

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

        patient["diagnostic_request_time"] = sim_time
        diag_env = {
            "patient": patient,
            "diagnostic_resources": env.get("diagnostic_resources", []),
            "simulation_time": sim_time,
        }
        percepts = self.diagnostic_agent.perceive(diag_env)
        decision = self.diagnostic_agent.decide(percepts)
        result = self.diagnostic_agent.act(decision, diag_env)

        if result["status"] == "ALLOCATED":
            patient["assigned_diagnostic_id"] = result["resource_id"]
            patient["diagnostic_start_time"] = sim_time
            patient["workflow_state"] = WorkflowState.DIAGNOSTICS_IN_PROGRESS.value
            if pid in self.waiting_diagnostics:
                self.waiting_diagnostics.remove(pid)
        else:
            patient["workflow_state"] = WorkflowState.WAITING_FOR_DIAGNOSTIC.value
            self.conflict_count += 1
            if pid not in self.waiting_diagnostics:
                self.waiting_diagnostics.append(pid)

        return result

    def request_icu_allocation(
        self, patient: Dict[str, Any], env: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 5: Request ICU bed from ICUAgent."""
        sim_time = env.get("simulation_time", 0.0)
        pid = patient["id"]

        if not patient.get("requires_icu", False):
            return {"status": "NOT_REQUIRED"}

        patient["icu_request_time"] = sim_time
        icu_env = {
            "patient": patient,
            "icu_beds": env.get("icu_beds", []),
            "simulation_time": sim_time,
        }
        percepts = self.icu_agent.perceive(icu_env)
        decision = self.icu_agent.decide(percepts)
        result = self.icu_agent.act(decision, icu_env)

        if result["status"] == "ALLOCATED":
            patient["assigned_icu_bed_id"] = result["icu_bed_id"]
            patient["icu_reservation_time"] = sim_time
            patient["workflow_state"] = WorkflowState.ICU_ALLOCATED.value
            if pid in self.waiting_icu:
                self.waiting_icu.remove(pid)
        else:
            patient["workflow_state"] = WorkflowState.WAITING_FOR_ICU.value
            self.conflict_count += 1
            if pid not in self.waiting_icu:
                self.waiting_icu.append(pid)

        return result
