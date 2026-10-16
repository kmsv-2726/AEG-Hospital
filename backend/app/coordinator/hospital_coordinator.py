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

    def sort_waiting_queue(self, queue: List[str], patients: Dict[str, Dict[str, Any]], current_time: float = 0.0) -> List[str]:
        """
        Sort waiting requests:
        - In FIFO mode: Sort by arrival_time / request_time.
        - In PRIORITY_AWARE mode: Sort by Dynamic OS Priority (considering aging) or base priority, then arrival_time.
        """
        if self.strategy == AllocationStrategy.FIFO:
            return sorted(queue, key=lambda pid: patients.get(pid, {}).get("arrival_time", 0.0))

        self.os_manager.apply_aging(current_time)
        priority_order = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
        return sorted(
            queue,
            key=lambda pid: (
                self.os_manager.pcbs[pid].dynamic_priority
                if pid in self.os_manager.pcbs
                else priority_order.get(patients.get(pid, {}).get("priority", "P3"), 3),
                patients.get(pid, {}).get("arrival_time", 0.0),
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
        patient["workflow_state"] = WorkflowState.REGISTERED.value

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
        patient["workflow_state"] = WorkflowState.TRIAGED.value
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
            patient["workflow_state"] = WorkflowState.ARRIVED.value
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
        result = self.ambulance_agent.act(decision, amb_env)

        if result["status"] == "ALLOCATED":
            patient["assigned_ambulance_id"] = result["ambulance_id"]
            patient["workflow_state"] = WorkflowState.AMBULANCE_ASSIGNED.value
            patient["ambulance_dispatch_time"] = sim_time
            self.os_manager.ambulance_semaphore.acquire(pid, result["ambulance_id"])
            if pid in self.waiting_ambulances:
                self.waiting_ambulances.remove(pid)
        else:
            patient["workflow_state"] = WorkflowState.WAITING_FOR_AMBULANCE.value
            self.conflict_count += 1
            self.os_manager.transition_process(pid, ProcessState.BLOCKED, sim_time, resource="Ambulance")
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
        result = self.doctor_agent.act(decision, doc_env)

        if result["status"] == "ALLOCATED":
            doc_id = result["doctor_id"]
            patient["assigned_doctor_id"] = doc_id
            patient["doctor_assignment_time"] = sim_time
            patient["workflow_state"] = WorkflowState.DOCTOR_ASSIGNED.value
            
            # OS Mutex Acquisition & Transition to RUNNING
            if doc_id in self.os_manager.doctor_mutexes:
                self.os_manager.doctor_mutexes[doc_id].acquire(pid, sim_time)
            self.os_manager.transition_process(pid, ProcessState.RUNNING, sim_time, resource=doc_id)

            if pid in self.waiting_doctors:
                self.waiting_doctors.remove(pid)
        else:
            patient["workflow_state"] = WorkflowState.WAITING_FOR_DOCTOR.value
            self.conflict_count += 1
            # OS Blocked Queue transition
            self.os_manager.transition_process(pid, ProcessState.BLOCKED, sim_time, resource=f"Doctor ({patient.get('required_specialty')})")
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
        result = self.diagnostic_agent.act(decision, diag_env)

        if result["status"] == "ALLOCATED":
            res_id = result["resource_id"]
            patient["assigned_diagnostic_id"] = res_id
            patient["diagnostic_start_time"] = sim_time
            patient["workflow_state"] = WorkflowState.DIAGNOSTICS_IN_PROGRESS.value
            
            # OS Scanner Mutex Acquisition
            if res_id in self.os_manager.diagnostic_mutexes:
                self.os_manager.diagnostic_mutexes[res_id].acquire(pid, sim_time)
            self.os_manager.transition_process(pid, ProcessState.RUNNING, sim_time, resource=res_id)

            if pid in self.waiting_diagnostics:
                self.waiting_diagnostics.remove(pid)
        else:
            patient["workflow_state"] = WorkflowState.WAITING_FOR_DIAGNOSTIC.value
            self.conflict_count += 1
            self.os_manager.transition_process(pid, ProcessState.BLOCKED, sim_time, resource=f"Scanner ({category})")
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
        result = self.icu_agent.act(decision, icu_env)

        if result["status"] == "ALLOCATED":
            bed_id = result["icu_bed_id"]
            patient["assigned_icu_bed_id"] = bed_id
            patient["icu_reservation_time"] = sim_time
            patient["workflow_state"] = WorkflowState.ICU_ALLOCATED.value

            # OS ICU Counting Semaphore Acquisition
            self.os_manager.icu_semaphore.acquire(pid, bed_id)
            self.os_manager.transition_process(pid, ProcessState.RUNNING, sim_time, resource=bed_id)

            if pid in self.waiting_icu:
                self.waiting_icu.remove(pid)
        else:
            patient["workflow_state"] = WorkflowState.WAITING_FOR_ICU.value
            self.conflict_count += 1
            self.os_manager.transition_process(pid, ProcessState.BLOCKED, sim_time, resource="ICU Bed")
            if pid not in self.waiting_icu:
                self.waiting_icu.append(pid)

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
