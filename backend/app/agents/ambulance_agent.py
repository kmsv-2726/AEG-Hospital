"""
Ambulance Agent: Allocates and dispatches simulated emergency ambulances.
"""
from typing import Dict, Any, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.models.enums import ResourceStatus, MessageType, PriorityLevel


class AmbulanceAgent(BaseAgent):
    """
    Manages ambulance availability, eligibility constraints, utility ranking,
    dispatch timing, and conflict resolution.
    """

    def __init__(self, agent_id: str = "AGENT-AMB", name: str = "AmbulanceAgent"):
        super().__init__(agent_id=agent_id, name=name, role="Ambulance Fleet Dispatcher")

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

        # Stage 2: Utility Score calculation
        # score = 100 - (base_distance_km * 5) + (20 if ventilator and priority is P1)
        patient_priority = percepts.get("priority")
        scored_candidates = []
        for amb in eligible:
            distance = amb.get("base_distance_km", 5.0)
            capabilities = amb.get("equipment_capabilities", "")
            score = 100.0 - (distance * 5.0)
            if patient_priority == PriorityLevel.P1.value and "Ventilator" in capabilities:
                score += 20.0
            scored_candidates.append((score, amb["id"], amb))

        # Highest score first, tie-break by ID
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

            # Update local resource object
            amb["status"] = ResourceStatus.BUSY.value
            amb["current_patient_id"] = patient_id
            amb["availability_timestamp"] = sim_time + travel_time

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
                payload={"travel_time": travel_time, "ambulance_id": amb["id"]},
            )

            return {
                "status": "ALLOCATED",
                "ambulance_id": amb["id"],
                "travel_time": travel_time,
                "message": msg,
            }

        elif action == "CONFLICT_WAITING":
            self.emit_event(
                simulation_time=sim_time,
                event_type="RESOURCE_UNAVAILABLE",
                description=f"No ambulance available for Patient {patient_id}. Request queued.",
                patient_id=patient_id,
                outcome="CONFLICT_WAITING",
                is_conflict=True,
            )

            msg = self.send_message(
                receiver="HospitalCoordinator",
                message_type=MessageType.RESOURCE_UNAVAILABLE,
                patient_id=patient_id,
                simulation_time=sim_time,
                payload={"resource_type": "AMBULANCE", "reason": decision["reason"]},
            )

            return {"status": "WAITING", "reason": decision["reason"], "message": msg}

        return {"status": "SKIPPED"}

    def release_ambulance(
        self, ambulance_id: str, fleet: List[Dict[str, Any]], simulation_time: float
    ) -> Optional[Dict[str, Any]]:
        """Release ambulance back to available pool upon hospital arrival."""
        for amb in fleet:
            if amb["id"] == ambulance_id:
                amb["status"] = ResourceStatus.AVAILABLE.value
                prev_patient = amb.get("current_patient_id")
                amb["current_patient_id"] = None
                amb["total_dispatches"] = amb.get("total_dispatches", 0) + 1

                self.emit_event(
                    simulation_time=simulation_time,
                    event_type="RESOURCE_RELEASED",
                    description=f"Ambulance {ambulance_id} completed transit and returned to service.",
                    patient_id=prev_patient,
                    resource_id=ambulance_id,
                    outcome="RELEASED",
                )
                self.send_message(
                    receiver="HospitalCoordinator",
                    message_type=MessageType.RESOURCE_RELEASED,
                    patient_id=prev_patient,
                    resource_id=ambulance_id,
                    simulation_time=simulation_time,
                    payload={"resource_type": "AMBULANCE"},
                )
                return amb
        return None
