"""
Doctor Agent: Assigns suitable emergency physicians based on specialty and workload.
"""
from typing import Dict, Any, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.models.enums import ResourceStatus, MessageType, DoctorSpecialty


class DoctorAgent(BaseAgent):
    """
    Manages physician availability, specialty matching, workload balancing,
    and doctor assignment conflict resolution.
    """

    def __init__(self, agent_id: str = "AGENT-DOC", name: str = "DoctorAgent"):
        super().__init__(agent_id=agent_id, name=name, role="Medical Staffing Coordinator")

    def perceive(self, environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient required specialty and medical staff state."""
        patient = environment_state.get("patient", {})
        doctors = environment_state.get("doctors", [])
        return {
            "patient_id": patient.get("id"),
            "required_specialty": patient.get("required_specialty", DoctorSpecialty.GENERAL_MEDICINE.value),
            "priority": patient.get("priority", "P3"),
            "doctors": doctors,
        }

    def decide(self, percepts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Two-stage allocation:
        Stage 1: Match requested specialty & status == AVAILABLE.
        Stage 2: Rank eligible doctors by least workload (workload_count).
        """
        requested_spec = percepts.get("required_specialty")
        patient_id = percepts.get("patient_id")

        # Primary candidates: exact specialty match
        eligible = [
            doc for doc in percepts["doctors"]
            if doc.get("status") == ResourceStatus.AVAILABLE.value
            and doc.get("specialty") == requested_spec
        ]

        if not eligible:
            return {
                "action": "CONFLICT_WAITING",
                "patient_id": patient_id,
                "reason": f"No available physician for requested specialty '{requested_spec}'. Request queued.",
            }

        # Stage 2: Workload score (lower workload is better)
        # score = 100 - (workload_count * 10)
        scored = []
        for doc in eligible:
            workload = doc.get("workload_count", 0)
            score = 100.0 - (workload * 10.0)
            scored.append((score, doc["id"], doc))

        scored.sort(key=lambda x: (-x[0], x[1]))
        selected_doc = scored[0][2]

        return {
            "action": "ALLOCATE",
            "patient_id": patient_id,
            "doctor": selected_doc,
            "score": scored[0][0],
            "reason": f"Assigned {selected_doc['name']} ({selected_doc['specialty']}) based on specialty match and workload {selected_doc.get('workload_count', 0)}.",
        }

    def act(self, decision: Dict[str, Any], environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Assign doctor or emit conflict event."""
        sim_time = environment_state.get("simulation_time", 0.0)
        patient_id = decision.get("patient_id")
        action = decision.get("action")

        if action == "ALLOCATE":
            doc = decision["doctor"]
            doc["status"] = ResourceStatus.BUSY.value
            doc["current_patient_id"] = patient_id
            doc["workload_count"] = doc.get("workload_count", 0) + 1

            self.emit_event(
                simulation_time=sim_time,
                event_type="DOCTOR_ASSIGNED",
                description=f"Physician {doc['name']} ({doc['id']}) assigned to Patient {patient_id}.",
                patient_id=patient_id,
                resource_id=doc["id"],
                outcome="SUCCESS",
            )

            msg = self.send_message(
                receiver="HospitalCoordinator",
                message_type=MessageType.DOCTOR_ASSIGNED,
                patient_id=patient_id,
                resource_id=doc["id"],
                simulation_time=sim_time,
                payload={"doctor_id": doc["id"], "doctor_name": doc["name"], "specialty": doc["specialty"]},
            )

            return {
                "status": "ALLOCATED",
                "doctor_id": doc["id"],
                "doctor_name": doc["name"],
                "message": msg,
            }

        elif action == "CONFLICT_WAITING":
            self.emit_event(
                simulation_time=sim_time,
                event_type="RESOURCE_UNAVAILABLE",
                description=f"Doctor allocation conflict for Patient {patient_id}: {decision['reason']}",
                patient_id=patient_id,
                outcome="CONFLICT_WAITING",
                is_conflict=True,
            )

            msg = self.send_message(
                receiver="HospitalCoordinator",
                message_type=MessageType.RESOURCE_UNAVAILABLE,
                patient_id=patient_id,
                simulation_time=sim_time,
                payload={"resource_type": "DOCTOR", "reason": decision["reason"]},
            )

            return {"status": "WAITING", "reason": decision["reason"], "message": msg}

        return {"status": "SKIPPED"}

    def release_doctor(
        self, doctor_id: str, doctors: List[Dict[str, Any]], simulation_time: float
    ) -> Optional[Dict[str, Any]]:
        """Release physician back to available pool upon examination/treatment completion."""
        for doc in doctors:
            if doc["id"] == doctor_id:
                doc["status"] = ResourceStatus.AVAILABLE.value
                prev_patient = doc.get("current_patient_id")
                doc["current_patient_id"] = None

                self.emit_event(
                    simulation_time=simulation_time,
                    event_type="RESOURCE_RELEASED",
                    description=f"Doctor {doc['name']} ({doctor_id}) completed care and is now available.",
                    patient_id=prev_patient,
                    resource_id=doctor_id,
                    outcome="RELEASED",
                )
                self.send_message(
                    receiver="HospitalCoordinator",
                    message_type=MessageType.RESOURCE_RELEASED,
                    patient_id=prev_patient,
                    resource_id=doctor_id,
                    simulation_time=simulation_time,
                    payload={"resource_type": "DOCTOR"},
                )
                return doc
        return None
