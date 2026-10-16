"""
ICU Agent: Manages intensive care beds, ventilator equipment, and critical admissions.
Enhanced with autonomous message handling, active critical monitoring state, and bed reservations.
"""
from typing import Dict, Any, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.models.enums import ResourceStatus, MessageType, PriorityLevel
from backend.app.schemas.hospital_schemas import AgentMessageSchema


class ICUAgent(BaseAgent):
    """
    Manages simulated ICU bed allocation, ventilator capability matching,
    and ICU bed release handling.
    """

    def __init__(self, agent_id: str = "AGENT-ICU", name: str = "ICUAgent"):
        super().__init__(agent_id=agent_id, name=name, role="Intensive Care Unit Coordinator")
        self.bed_assignments: Dict[str, str] = {}  # patient_id -> bed_id

    def handle_message(self, message: AgentMessageSchema, environment_state: Dict[str, Any]) -> Optional[AgentMessageSchema]:
        """Autonomously process incoming ICU critical admission requests."""
        if message.message_type == MessageType.ICU_REQUEST:
            patient_data = message.payload.get("patient", {"id": message.patient_id, "priority": message.payload.get("priority", "P1")})
            beds = environment_state.get("icu_beds", [])
            env = {"patient": patient_data, "icu_beds": beds, "simulation_time": message.simulation_time}
            percepts = self.perceive(env)
            decision = self.decide(percepts)
            res = self.act(decision, env)
            return res.get("message")
        return None

    def perceive(self, environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient critical needs and ICU bed availability."""
        patient = environment_state.get("patient", {})
        beds = environment_state.get("icu_beds", [])
        return {
            "patient_id": patient.get("id"),
            "requires_icu": patient.get("requires_icu", False),
            "priority": patient.get("priority", "P3"),
            "beds": beds,
        }

    def decide(self, percepts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Two-stage allocation:
        Stage 1: Match requires_icu & status == AVAILABLE.
        Stage 2: Prioritize ventilator-equipped beds for critical (P1) patients.
        """
        if not percepts.get("requires_icu"):
            return {"action": "NOT_REQUIRED", "patient_id": percepts["patient_id"]}

        patient_id = percepts["patient_id"]
        priority = percepts.get("priority")

        eligible = [
            b for b in percepts["beds"]
            if b.get("status") == ResourceStatus.AVAILABLE.value
        ]

        if not eligible:
            return {
                "action": "CONFLICT_WAITING",
                "patient_id": patient_id,
                "reason": "All ICU beds are currently occupied. Request queued for next available bed.",
            }

        # If P1, prefer ventilator beds
        if priority == PriorityLevel.P1.value:
            vent_beds = [b for b in eligible if b.get("has_ventilator")]
            if vent_beds:
                eligible = vent_beds

        eligible.sort(key=lambda b: b["id"])
        selected_bed = eligible[0]

        return {
            "action": "ALLOCATE",
            "patient_id": patient_id,
            "bed": selected_bed,
            "reason": f"Allocated ICU bed {selected_bed['id']} (Ventilator: {selected_bed.get('has_ventilator', False)}).",
        }

    def act(self, decision: Dict[str, Any], environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Reserve ICU bed or emit conflict event."""
        sim_time = environment_state.get("simulation_time", 0.0)
        patient_id = decision.get("patient_id")
        action = decision.get("action")

        if action == "ALLOCATE":
            bed = decision["bed"]
            bed["status"] = ResourceStatus.BUSY.value
            bed["current_patient_id"] = patient_id
            bed["reservation_timestamp"] = sim_time

            self.bed_assignments[patient_id] = bed["id"]
            if patient_id not in self.active_patients:
                self.active_patients.append(patient_id)
            self.current_process_id = patient_id
            self.status = "MONITORING_ICU"

            self.emit_event(
                simulation_time=sim_time,
                event_type="ICU_RESERVED",
                description=f"ICU Bed {bed['id']} reserved for critical Patient {patient_id}.",
                patient_id=patient_id,
                resource_id=bed["id"],
                outcome="SUCCESS",
            )

            msg = self.send_message(
                receiver="HospitalCoordinator",
                message_type=MessageType.ICU_RESERVED,
                patient_id=patient_id,
                resource_id=bed["id"],
                simulation_time=sim_time,
                payload={"icu_bed_id": bed["id"], "unit_name": bed.get("unit_name")},
            )

            return {
                "status": "ALLOCATED",
                "icu_bed_id": bed["id"],
                "unit_name": bed.get("unit_name"),
                "message": msg,
            }

        elif action == "CONFLICT_WAITING":
            self.status = "WAITING_RESOURCE"
            self.emit_event(
                simulation_time=sim_time,
                event_type="RESOURCE_CONFLICT",
                description=f"ICU saturation for critical Patient {patient_id}: {decision.get('reason')}",
                patient_id=patient_id,
                outcome="WAITING",
                is_conflict=True,
            )

            msg = self.send_message(
                receiver="HospitalCoordinator",
                message_type=MessageType.RESOURCE_UNAVAILABLE,
                patient_id=patient_id,
                simulation_time=sim_time,
                payload={"resource_type": "icu_bed", "reason": decision.get("reason")},
            )

            return {
                "status": "WAITING",
                "reason": decision.get("reason"),
                "message": msg,
            }

        return {"status": "NOT_REQUIRED"}

    def release_bed(self, bed_id: str, beds: List[Dict[str, Any]], simulation_time: float = 0.0):
        """Release and sanitize ICU bed upon patient discharge or step-down."""
        sim_time = simulation_time
        for bed in beds:
            if bed["id"] == bed_id:
                released_pid = bed.get("current_patient_id")
                bed["status"] = ResourceStatus.AVAILABLE.value
                bed["current_patient_id"] = None
                bed["release_timestamp"] = sim_time
                if released_pid and released_pid in self.active_patients:
                    self.active_patients.remove(released_pid)
                if released_pid in self.bed_assignments:
                    del self.bed_assignments[released_pid]

                self.emit_event(
                    simulation_time=sim_time,
                    event_type="RESOURCE_RELEASED",
                    description=f"ICU Bed {bed['id']} sanitized and returned to critical care inventory.",
                    patient_id=released_pid,
                    resource_id=bed_id,
                    outcome="SUCCESS",
                )

                self.send_message(
                    receiver="HospitalCoordinator",
                    message_type=MessageType.RESOURCE_RELEASED,
                    patient_id=released_pid,
                    resource_id=bed_id,
                    simulation_time=sim_time,
                    payload={"resource_type": "icu_bed", "bed_id": bed_id},
                )
                break

        self.status = "MONITORING_ICU" if self.active_patients else "IDLE"
        self.current_process_id = self.active_patients[0] if self.active_patients else None
