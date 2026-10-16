"""
ICU Agent: Manages intensive care beds, ventilator equipment, and critical admissions.
"""
from typing import Dict, Any, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.models.enums import ResourceStatus, MessageType, PriorityLevel


class ICUAgent(BaseAgent):
    """
    Manages simulated ICU bed allocation, ventilator capability matching,
    and ICU bed release handling.
    """

    def __init__(self, agent_id: str = "AGENT-ICU", name: str = "ICUAgent"):
        super().__init__(agent_id=agent_id, name=name, role="Intensive Care Unit Coordinator")

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
                "message": msg,
            }

        elif action == "CONFLICT_WAITING":
            self.emit_event(
                simulation_time=sim_time,
                event_type="RESOURCE_UNAVAILABLE",
                description=f"ICU bed conflict for Patient {patient_id}: {decision['reason']}",
                patient_id=patient_id,
                outcome="CONFLICT_WAITING",
                is_conflict=True,
            )

            msg = self.send_message(
                receiver="HospitalCoordinator",
                message_type=MessageType.RESOURCE_UNAVAILABLE,
                patient_id=patient_id,
                simulation_time=sim_time,
                payload={"resource_type": "ICU_BED", "reason": decision["reason"]},
            )

            return {"status": "WAITING", "reason": decision["reason"], "message": msg}

        return {"status": "SKIPPED"}

    def release_bed(
        self, bed_id: str, beds: List[Dict[str, Any]], simulation_time: float
    ) -> Optional[Dict[str, Any]]:
        """Release ICU bed back to available pool upon patient discharge or step-down."""
        for bed in beds:
            if bed["id"] == bed_id:
                bed["status"] = ResourceStatus.AVAILABLE.value
                prev_patient = bed.get("current_patient_id")
                bed["current_patient_id"] = None
                bed["release_timestamp"] = simulation_time

                self.emit_event(
                    simulation_time=simulation_time,
                    event_type="RESOURCE_RELEASED",
                    description=f"ICU Bed {bed_id} released and sanitized for subsequent admissions.",
                    patient_id=prev_patient,
                    resource_id=bed_id,
                    outcome="RELEASED",
                )
                self.send_message(
                    receiver="HospitalCoordinator",
                    message_type=MessageType.RESOURCE_RELEASED,
                    patient_id=prev_patient,
                    resource_id=bed_id,
                    simulation_time=simulation_time,
                    payload={"resource_type": "ICU_BED"},
                )
                return bed
        return None
