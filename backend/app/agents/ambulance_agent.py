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
            "required_equipment": patient.get("required_equipment") or (
                ["ALS"] if patient.get("priority") == PriorityLevel.P1.value else []
            ),
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

        required_equipment = percepts.get("required_equipment", [])
        if isinstance(required_equipment, str):
            required_equipment = required_equipment.split(",")
        required_equipment = {item.strip().casefold() for item in required_equipment if item.strip()}
        candidates = []
        for ambulance in percepts["fleet"]:
            capabilities = {
                item.strip().casefold()
                for item in ambulance.get("equipment_capabilities", "").split(",")
                if item.strip()
            }
            reasons = []
            if ambulance.get("status") != ResourceStatus.AVAILABLE.value:
                reasons.append("not available")
            missing_equipment = required_equipment - capabilities
            if missing_equipment:
                reasons.append(f"missing equipment: {', '.join(sorted(missing_equipment))}")
            candidates.append({
                "resource_id": ambulance["id"],
                "available": ambulance.get("status") == ResourceStatus.AVAILABLE.value,
                "eligible": not reasons,
                "rejection_reasons": reasons,
                "distance_km": ambulance.get("base_distance_km", 5.0),
                "capabilities": sorted(capabilities),
            })

        eligible = [
            ambulance
            for ambulance, candidate in zip(percepts["fleet"], candidates)
            if candidate["eligible"]
        ]

        if not eligible:
            return {
                "action": "CONFLICT_WAITING",
                "patient_id": percepts["patient_id"],
                "candidates": candidates,
                "reason": (
                    "No available ambulance has the required equipment: "
                    f"{', '.join(sorted(required_equipment))}."
                    if required_equipment
                    else "All simulated ambulances are currently deployed or unavailable."
                ),
            }

        patient_priority = percepts.get("priority")
        scored_candidates = []
        for amb in eligible:
            distance = amb.get("base_distance_km", 5.0)
            capabilities = {
                item.strip().casefold()
                for item in amb.get("equipment_capabilities", "").split(",")
                if item.strip()
            }
            distance_score = -5.0 * distance
            urgency_bonus = (
                20.0
                if patient_priority == PriorityLevel.P1.value and "ventilator" in capabilities
                else 0.0
            )
            score = 100.0 + distance_score + urgency_bonus
            candidate = next(item for item in candidates if item["resource_id"] == amb["id"])
            candidate.update({
                "distance_score": distance_score,
                "urgency_bonus": urgency_bonus,
                "score": score,
            })
            scored_candidates.append((candidate["score"], amb["id"], amb))

        scored_candidates.sort(key=lambda item: (-item[0], item[1]))
        selected_amb = scored_candidates[0][2]
        travel_time = round(selected_amb.get("base_distance_km", 5.0) * 1.5, 1)
        ranked_candidates = [
            {
                **next(item for item in candidates if item["resource_id"] == ambulance["id"]),
                "rank": rank,
            }
            for rank, (_, _, ambulance) in enumerate(scored_candidates, start=1)
        ]

        return {
            "action": "ALLOCATE",
            "patient_id": percepts["patient_id"],
            "ambulance": selected_amb,
            "travel_time": travel_time,
            "score": scored_candidates[0][0],
            "candidates": sorted(
                [
                    *ranked_candidates,
                    *(item for item in candidates if not item["eligible"]),
                ],
                key=lambda item: item.get("rank", len(ranked_candidates) + 1),
            ),
            "reason": f"Selected closest suitable ambulance ({selected_amb['id']}) with travel time {travel_time}m.",
        }

    def act(self, decision: Dict[str, Any], environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ambulance dispatch or register conflict."""
        sim_time = environment_state.get("simulation_time", 0.0)
        patient_id = environment_state.get("patient", {}).get(
            "id", decision.get("patient_id")
        )
        action = decision.get("action")
        if action == "ALLOCATE" and not self.reserve_resource(
            decision["ambulance"], patient_id
        ):
            refreshed = self.decide(self.perceive(environment_state))
            if refreshed.get("action") == "ALLOCATE" and self.reserve_resource(
                refreshed["ambulance"], patient_id
            ):
                decision = refreshed
            else:
                decision = {
                    **refreshed,
                    "action": "CONFLICT_WAITING",
                    "reason": "Selected ambulance became unavailable; no other eligible unit remained.",
                }
                action = decision["action"]

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

    def release_ambulance(
        self,
        ambulance_id: str,
        fleet: List[Dict[str, Any]],
        simulation_time: float = 0.0,
        expected_patient_id: Optional[str] = None,
    ):
        """Release ambulance upon patient arrival at hospital."""
        sim_time = simulation_time
        for amb in fleet:
            if amb["id"] == ambulance_id:
                released_pid = amb.get("current_patient_id")
                if expected_patient_id and released_pid != expected_patient_id:
                    return None
                if not self.release_resource(amb, expected_patient_id or released_pid):
                    return None
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
