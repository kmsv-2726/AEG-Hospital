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

    def release_doctor(self, doctor_id: str, doctors: List[Dict[str, Any]], simulation_time: float = 0.0):
        """Release physician upon patient examination / treatment completion."""
        sim_time = simulation_time
        for doc in doctors:
            if doc["id"] == doctor_id:
                released_pid = doc.get("current_patient_id")
                doc["status"] = ResourceStatus.AVAILABLE.value
                doc["current_patient_id"] = None
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
