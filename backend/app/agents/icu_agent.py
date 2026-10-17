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
            "requires_ventilator": patient.get("requires_ventilator", False),
            "required_icu_equipment": patient.get("required_icu_equipment", []),
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
        required_equipment = {
            item.strip().casefold()
            for item in percepts.get("required_icu_equipment", [])
            if item.strip()
        }
        if percepts.get("requires_ventilator"):
            required_equipment.add("ventilator")

        candidates = []
        eligible = []
        for bed in percepts["beds"]:
            reasons = []
            if bed.get("status") != ResourceStatus.AVAILABLE.value:
                reasons.append("not available")
            capabilities = set()
            if bed.get("has_ventilator"):
                capabilities.add("ventilator")
            if bed.get("has_monitoring", True):
                capabilities.add("monitoring")
            missing = required_equipment - capabilities
            if missing:
                reasons.append(f"missing equipment: {', '.join(sorted(missing))}")
            urgency_bonus = 20.0 if priority == PriorityLevel.P1.value and "ventilator" in capabilities else 0.0
            item = {
                "resource_id": bed["id"],
                "available": bed.get("status") == ResourceStatus.AVAILABLE.value,
                "eligible": not reasons,
                "rejection_reasons": reasons,
                "capabilities": sorted(capabilities),
                "urgency_bonus": urgency_bonus if not reasons else None,
                "score": urgency_bonus if not reasons else None,
            }
            candidates.append(item)
            if not reasons:
                eligible.append((urgency_bonus, bed["id"], bed, item))

        if not eligible:
            return {
                "action": "CONFLICT_WAITING",
                "patient_id": patient_id,
                "candidates": candidates,
                "reason": "No available ICU bed satisfies the configured equipment requirements. Request queued.",
            }

        eligible.sort(key=lambda item: (-item[0], item[1]))
        ranked = [
            {**candidate, "rank": rank}
            for rank, (_, _, _, candidate) in enumerate(eligible, start=1)
        ]
        selected_bed = eligible[0][2]

        return {
            "action": "ALLOCATE",
            "patient_id": patient_id,
            "bed": selected_bed,
            "candidates": [*ranked, *(item for item in candidates if not item["eligible"])],
            "reason": (
                f"Selected bed {selected_bed['id']} among beds meeting equipment requirements; "
                f"P1 ventilator preference bonus={eligible[0][0]:g}; ties use bed ID."
            ),
        }

    def act(self, decision: Dict[str, Any], environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Reserve ICU bed or emit conflict event."""
        sim_time = environment_state.get("simulation_time", 0.0)
        patient_id = environment_state.get("patient", {}).get(
            "id", decision.get("patient_id")
        )
        action = decision.get("action")
        if action == "ALLOCATE" and not self.reserve_resource(
            decision["bed"], patient_id
        ):
            refreshed = self.decide(self.perceive(environment_state))
            if refreshed.get("action") == "ALLOCATE" and self.reserve_resource(
                refreshed["bed"], patient_id
            ):
                decision = refreshed
            else:
                decision = {
                    **refreshed,
                    "action": "CONFLICT_WAITING",
                    "reason": "Selected ICU bed became unavailable; no other eligible bed remained.",
                }
                action = decision["action"]

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

    def release_bed(
        self,
        bed_id: str,
        beds: List[Dict[str, Any]],
        simulation_time: float = 0.0,
        expected_patient_id: Optional[str] = None,
    ):
        """Release and sanitize ICU bed upon patient discharge or step-down."""
        sim_time = simulation_time
        for bed in beds:
            if bed["id"] == bed_id:
                released_pid = bed.get("current_patient_id")
                if expected_patient_id and released_pid != expected_patient_id:
                    return None
                if not self.release_resource(bed, expected_patient_id or released_pid):
                    return None
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
