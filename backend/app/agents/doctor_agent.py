"""
Doctor Agent: Assigns suitable emergency physicians based on specialty and workload.
Enhanced with autonomous message handling, active clinical state, and specialty load balancing.
"""
from typing import Dict, Any, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.models.enums import ResourceStatus, MessageType, DoctorSpecialty
from backend.app.schemas.hospital_schemas import AgentMessageSchema


class DoctorAgent(BaseAgent):
    """
    Manages physician availability, specialty matching, workload balancing,
    and doctor assignment conflict resolution.
    """

    def __init__(self, agent_id: str = "AGENT-DOC", name: str = "DoctorAgent"):
        super().__init__(agent_id=agent_id, name=name, role="Medical Staffing Coordinator")
        self.doctor_assignments: Dict[str, str] = {}  # patient_id -> doctor_id

    def handle_message(self, message: AgentMessageSchema, environment_state: Dict[str, Any]) -> Optional[AgentMessageSchema]:
        """Autonomously process incoming physician allocation requests."""
        if message.message_type == MessageType.DOCTOR_REQUEST:
            patient_data = message.payload.get("patient", {"id": message.patient_id, "required_specialty": message.payload.get("specialty")})
            doctors = environment_state.get("doctors", [])
            env = {"patient": patient_data, "doctors": doctors, "simulation_time": message.simulation_time}
            percepts = self.perceive(env)
            decision = self.decide(percepts)
            res = self.act(decision, env)
            return res.get("message")
        return None

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
        priority = percepts.get("priority", "P3")
        workload_penalty_factor = {"P1": 0.5, "P2": 0.75, "P3": 1.0, "P4": 1.25}.get(priority, 1.0)
        candidates = []
        eligible = []
        for doctor in percepts["doctors"]:
            reasons = []
            if doctor.get("status") != ResourceStatus.AVAILABLE.value:
                reasons.append("not available")
            if doctor.get("specialty") != requested_spec:
                reasons.append(f"specialty mismatch: {doctor.get('specialty')}")
            workload = doctor.get("workload_count", 0)
            score = round(100.0 - workload * 10.0 * workload_penalty_factor, 2)
            item = {
                "resource_id": doctor["id"],
                "name": doctor.get("name"),
                "specialty": doctor.get("specialty"),
                "available": doctor.get("status") == ResourceStatus.AVAILABLE.value,
                "eligible": not reasons,
                "rejection_reasons": reasons,
                "workload_count": workload,
                "workload_penalty_factor": workload_penalty_factor,
                "score": score if not reasons else None,
            }
            candidates.append(item)
            if not reasons:
                eligible.append((score, doctor["id"], doctor, item))

        if not eligible:
            return {
                "action": "CONFLICT_WAITING",
                "patient_id": patient_id,
                "candidates": candidates,
                "reason": f"No available physician for requested specialty '{requested_spec}'. Request queued.",
            }

        eligible.sort(key=lambda item: (-item[0], item[1]))
        ranked = []
        for rank, (_, _, _, item) in enumerate(eligible, start=1):
            ranked.append({**item, "rank": rank})
        candidates_by_id = {item["resource_id"]: item for item in candidates}
        candidates = [*ranked, *(item for item in candidates if not item["eligible"])]
        selected_doc = eligible[0][2]

        return {
            "action": "ALLOCATE",
            "patient_id": patient_id,
            "doctor": selected_doc,
            "score": eligible[0][0],
            "candidates": candidates,
            "reason": (
                f"Selected {selected_doc['name']} ({selected_doc['specialty']}) with "
                f"score 100 - workload {selected_doc.get('workload_count', 0)} × 10 × "
                f"priority factor {workload_penalty_factor} = {eligible[0][0]}; "
                "ties use ascending doctor ID."
            ),
        }

    def act(self, decision: Dict[str, Any], environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Assign doctor or emit conflict event."""
        sim_time = environment_state.get("simulation_time", 0.0)
        patient_id = environment_state.get("patient", {}).get(
            "id", decision.get("patient_id")
        )
        action = decision.get("action")
        if action == "ALLOCATE" and not self.reserve_resource(
            decision["doctor"], patient_id
        ):
            refreshed = self.decide(self.perceive(environment_state))
            if refreshed.get("action") == "ALLOCATE" and self.reserve_resource(
                refreshed["doctor"], patient_id
            ):
                decision = refreshed
            else:
                decision = {
                    **refreshed,
                    "action": "CONFLICT_WAITING",
                    "reason": "Selected doctor became unavailable; no other eligible doctor remained.",
                }
                action = decision["action"]

        if action == "ALLOCATE":
            doc = decision["doctor"]
            doc["status"] = ResourceStatus.BUSY.value
            doc["current_patient_id"] = patient_id
            doc["workload_count"] = doc.get("workload_count", 0) + 1

            self.doctor_assignments[patient_id] = doc["id"]
            if patient_id not in self.active_patients:
                self.active_patients.append(patient_id)
            self.current_process_id = patient_id
            self.status = "EXAMINING"

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
                "specialty": doc["specialty"],
                "message": msg,
            }

        elif action == "CONFLICT_WAITING":
            self.status = "WAITING_RESOURCE"
            self.emit_event(
                simulation_time=sim_time,
                event_type="RESOURCE_CONFLICT",
                description=f"Physician shortage for Patient {patient_id}: {decision.get('reason')}",
                patient_id=patient_id,
                outcome="WAITING",
                is_conflict=True,
            )

            msg = self.send_message(
                receiver="HospitalCoordinator",
                message_type=MessageType.RESOURCE_UNAVAILABLE,
                patient_id=patient_id,
                simulation_time=sim_time,
                payload={"resource_type": "doctor", "reason": decision.get("reason")},
            )

            return {
                "status": "WAITING",
                "reason": decision.get("reason"),
                "message": msg,
            }

        return {"status": "ERROR"}

    def release_doctor(
        self,
        doctor_id: str,
        doctors: List[Dict[str, Any]],
        simulation_time: float = 0.0,
        expected_patient_id: Optional[str] = None,
    ):
        """Release physician upon patient examination / treatment completion."""
        sim_time = simulation_time
        for doc in doctors:
            if doc["id"] == doctor_id:
                released_pid = doc.get("current_patient_id")
                if expected_patient_id and released_pid != expected_patient_id:
                    return None
                if not self.release_resource(doc, expected_patient_id or released_pid):
                    return None
                doc["availability_timestamp"] = sim_time
                if released_pid and released_pid in self.active_patients:
                    self.active_patients.remove(released_pid)
                if released_pid in self.doctor_assignments:
                    del self.doctor_assignments[released_pid]

                self.emit_event(
                    simulation_time=sim_time,
                    event_type="RESOURCE_RELEASED",
                    description=f"Physician {doc['name']} ({doctor_id}) completed treatment and returned to service.",
                    patient_id=released_pid,
                    resource_id=doctor_id,
                    outcome="SUCCESS",
                )

                self.send_message(
                    receiver="HospitalCoordinator",
                    message_type=MessageType.RESOURCE_RELEASED,
                    patient_id=released_pid,
                    resource_id=doctor_id,
                    simulation_time=sim_time,
                    payload={"resource_type": "doctor", "doctor_id": doctor_id},
                )
                break

        self.status = "EXAMINING" if self.active_patients else "IDLE"
        self.current_process_id = self.active_patients[0] if self.active_patients else None
