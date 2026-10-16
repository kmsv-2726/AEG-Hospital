"""
Ambulance Agent: Allocates and dispatches simulated emergency ambulances.
Enhanced with autonomous message handling, active state, and fleet dispatch tracking.
"""
from typing import Dict, Any, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.models.enums import ResourceStatus, MessageType, PriorityLevel
from backend.app.schemas.hospital_schemas import AgentMessageSchema


class AmbulanceAgent(BaseAgent):
    """
    Manages ambulance availability, eligibility constraints, utility ranking,
    dispatch timing, and conflict resolution.
    """

    def __init__(self, agent_id: str = "AGENT-AMB", name: str = "AmbulanceAgent"):
        super().__init__(agent_id=agent_id, name=name, role="Ambulance Fleet Dispatcher")
        self.assigned_ambulances: Dict[str, str] = {}  # patient_id -> ambulance_id

    def handle_message(self, message: AgentMessageSchema, environment_state: Dict[str, Any]) -> Optional[AgentMessageSchema]:
        """Autonomously process incoming ambulance dispatch requests."""
        if message.message_type == MessageType.AMBULANCE_REQUEST:
            patient_data = message.payload.get("patient", {"id": message.patient_id, "priority": message.payload.get("priority", "P3")})
            fleet = environment_state.get("ambulances", [])
            env = {"patient": patient_data, "ambulances": fleet, "simulation_time": message.simulation_time}
            percepts = self.perceive(env)
            decision = self.decide(percepts)
            res = self.act(decision, env)
            return res.get("message")
        return None

    def perceive(self, environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract requested patient details and fleet availability."""
        patient = environment_state.get("patient", {})
        fleet = environment_state.get("ambulances", [])
        return {
            "patient_id": patient.get("id"),
            "priority": patient.get("priority", "P3"),
            "requires_ambulance": patient.get("requires_ambulance", True),
            "fleet": fleet,
        }

    def decide(self, percepts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Two-stage allocation:
        Stage 1: Eligibility (status == AVAILABLE).
        Stage 2: Utility Scoring based on distance and capabilities.
        """
        if not percepts.get("requires_ambulance"):
            return {"action": "NOT_REQUIRED", "patient_id": percepts["patient_id"]}

        eligible = [
            amb for amb in percepts["fleet"]
            if amb.get("status") == ResourceStatus.AVAILABLE.value
        ]

        if not eligible:
            return {
                "action": "CONFLICT_WAITING",
                "patient_id": percepts["patient_id"],
                "reason": "All simulated ambulances are currently deployed or unavailable.",
            }

        patient_priority = percepts.get("priority")
        scored_candidates = []
        for amb in eligible:
            distance = amb.get("base_distance_km", 5.0)
            capabilities = amb.get("equipment_capabilities", "")
            score = 100.0 - (distance * 5.0)
            if patient_priority == PriorityLevel.P1.value and "Ventilator" in capabilities:
                score += 20.0
            scored_candidates.append((score, amb["id"], amb))

        scored_candidates.sort(key=lambda item: (-item[0], item[1]))
        selected_amb = scored_candidates[0][2]
        travel_time = round(selected_amb.get("base_distance_km", 5.0) * 1.5, 1)

        return {
            "action": "ALLOCATE",
            "patient_id": percepts["patient_id"],
            "ambulance": selected_amb,
            "travel_time": travel_time,
            "score": scored_candidates[0][0],
            "reason": f"Selected closest suitable ambulance ({selected_amb['id']}) with travel time {travel_time}m.",
        }

    def act(self, decision: Dict[str, Any], environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ambulance dispatch or register conflict."""
        sim_time = environment_state.get("simulation_time", 0.0)
        patient_id = decision.get("patient_id")
        action = decision.get("action")

        if action == "ALLOCATE":
            amb = decision["ambulance"]
            travel_time = decision["travel_time"]

            amb["status"] = ResourceStatus.BUSY.value
            amb["current_patient_id"] = patient_id
            amb["availability_timestamp"] = sim_time + travel_time
            amb["total_dispatches"] = amb.get("total_dispatches", 0) + 1

            self.assigned_ambulances[patient_id] = amb["id"]
            if patient_id not in self.active_patients:
                self.active_patients.append(patient_id)
            self.current_process_id = patient_id
            self.status = "DISPATCHING"

            self.emit_event(
                simulation_time=sim_time,
                event_type="AMBULANCE_ASSIGNED",
                description=f"Ambulance {amb['id']} dispatched for Patient {patient_id}. ETA: {travel_time} mins.",
                patient_id=patient_id,
                resource_id=amb["id"],
                outcome="SUCCESS",
            )

            msg = self.send_message(
                receiver="HospitalCoordinator",
                message_type=MessageType.AMBULANCE_ASSIGNED,
                patient_id=patient_id,
                resource_id=amb["id"],
                simulation_time=sim_time,
                payload={"ambulance_id": amb["id"], "travel_time": travel_time, "score": decision.get("score")},
            )

            return {
                "status": "ALLOCATED",
                "ambulance_id": amb["id"],
                "travel_time": travel_time,
                "score": decision.get("score"),
                "message": msg,
            }

        elif action == "CONFLICT_WAITING":
            self.status = "WAITING_RESOURCE"
            self.emit_event(
                simulation_time=sim_time,
                event_type="RESOURCE_CONFLICT",
                description=f"Ambulance contention for Patient {patient_id}: {decision.get('reason')}",
                patient_id=patient_id,
                outcome="WAITING",
                is_conflict=True,
            )

            msg = self.send_message(
                receiver="HospitalCoordinator",
                message_type=MessageType.RESOURCE_UNAVAILABLE,
                patient_id=patient_id,
                simulation_time=sim_time,
                payload={"resource_type": "ambulance", "reason": decision.get("reason")},
            )

            return {
                "status": "WAITING",
                "reason": decision.get("reason"),
                "message": msg,
            }

        return {"status": "NOT_REQUIRED", "travel_time": 0.0}

    def release_ambulance(self, ambulance_id: str, fleet: List[Dict[str, Any]], simulation_time: float = 0.0):
        """Release ambulance upon patient arrival at hospital."""
        sim_time = simulation_time
        for amb in fleet:
            if amb["id"] == ambulance_id:
                released_pid = amb.get("current_patient_id")
                amb["status"] = ResourceStatus.AVAILABLE.value
                amb["current_patient_id"] = None
                amb["availability_timestamp"] = sim_time
                if released_pid and released_pid in self.active_patients:
                    self.active_patients.remove(released_pid)
                if released_pid in self.assigned_ambulances:
                    del self.assigned_ambulances[released_pid]

                self.emit_event(
                    simulation_time=sim_time,
                    event_type="RESOURCE_RELEASED",
                    description=f"Ambulance {ambulance_id} completed transit and returned to service.",
                    patient_id=released_pid,
                    resource_id=ambulance_id,
                    outcome="SUCCESS",
                )

                self.send_message(
                    receiver="HospitalCoordinator",
                    message_type=MessageType.RESOURCE_RELEASED,
                    patient_id=released_pid,
                    resource_id=ambulance_id,
                    simulation_time=sim_time,
                    payload={"resource_type": "ambulance", "ambulance_id": ambulance_id},
                )
                self.status = "BUSY" if self.active_patients else "IDLE"
                self.current_process_id = self.active_patients[0] if self.active_patients else None
                return amb

        self.status = "BUSY" if self.active_patients else "IDLE"
        self.current_process_id = self.active_patients[0] if self.active_patients else None
        return None
