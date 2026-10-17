"""
Diagnostic Agent: Manages imaging, scans, laboratory equipment, and queueing.
Enhanced with autonomous message handling, active scanner state, and queue tracking.
"""
from typing import Dict, Any, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.models.enums import ResourceStatus, MessageType, DiagnosticCategory
from backend.app.schemas.hospital_schemas import AgentMessageSchema


class DiagnosticAgent(BaseAgent):
    """
    Allocates simulated diagnostic equipment (CT, MRI, X-Ray, Labs, Ultrasound)
    and handles equipment queuing and releases.
    """

    def __init__(self, agent_id: str = "AGENT-DIAG", name: str = "DiagnosticAgent"):
        super().__init__(agent_id=agent_id, name=name, role="Diagnostic Equipment Coordinator")
        self.diagnostic_assignments: Dict[str, str] = {}  # patient_id -> resource_id

    def handle_message(self, message: AgentMessageSchema, environment_state: Dict[str, Any]) -> Optional[AgentMessageSchema]:
        """Autonomously process incoming diagnostic scanner requests."""
        if message.message_type == MessageType.DIAGNOSTIC_REQUEST:
            patient_data = message.payload.get("patient", {"id": message.patient_id, "required_diagnostic": message.payload.get("category")})
            resources = environment_state.get("diagnostic_resources", [])
            env = {"patient": patient_data, "diagnostic_resources": resources, "simulation_time": message.simulation_time}
            percepts = self.perceive(env)
            decision = self.decide(percepts)
            res = self.act(decision, env)
            return res.get("message")
        return None

    def perceive(self, environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract requested scan/test category and equipment status."""
        patient = environment_state.get("patient", {})
        resources = environment_state.get("diagnostic_resources", [])
        return {
            "patient_id": patient.get("id"),
            "required_diagnostic": patient.get("required_diagnostic"),
            "priority": patient.get("priority", "P3"),
            "resources": resources,
        }

    def decide(self, percepts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Two-stage allocation:
        Stage 1: Match requested diagnostic category and status == AVAILABLE.
        Stage 2: Select equipment with shortest queue or duration.
        """
        category = percepts.get("required_diagnostic")
        patient_id = percepts.get("patient_id")

        if not category:
            return {"action": "NOT_REQUIRED", "patient_id": patient_id}

        candidates = []
        eligible = []
        for resource in percepts["resources"]:
            reasons = []
            if resource.get("status") != ResourceStatus.AVAILABLE.value:
                reasons.append("not available")
            if resource.get("category") != category:
                reasons.append(f"diagnostic mismatch: {resource.get('category')}")
            duration = resource.get("simulated_duration", 15.0)
            queue_length = resource.get("queue_length", 0)
            estimated_completion = duration * (queue_length + 1)
            score = -estimated_completion
            item = {
                "resource_id": resource["id"],
                "category": resource.get("category"),
                "available": resource.get("status") == ResourceStatus.AVAILABLE.value,
                "eligible": not reasons,
                "rejection_reasons": reasons,
                "queue_length": queue_length,
                "processing_minutes": duration,
                "estimated_completion_minutes": estimated_completion,
                "score": score if not reasons else None,
            }
            candidates.append(item)
            if not reasons:
                eligible.append((score, resource.get("queue_length", 0), duration, resource["id"], resource, item))

        if not eligible:
            return {
                "action": "CONFLICT_WAITING",
                "patient_id": patient_id,
                "category": category,
                "candidates": candidates,
                "reason": f"Diagnostic resource '{category}' is currently busy or unavailable. Request queued.",
            }

        eligible.sort(key=lambda item: (-item[0], item[1], item[2], item[3]))
        ranked = [
            {**candidate, "rank": rank}
            for rank, (*_, candidate) in enumerate(eligible, start=1)
        ]
        selected_res = eligible[0][4]
        duration = selected_res.get("simulated_duration", 15.0)

        return {
            "action": "ALLOCATE",
            "patient_id": patient_id,
            "resource": selected_res,
            "duration": duration,
            "candidates": [*ranked, *(item for item in candidates if not item["eligible"])],
            "reason": (
                f"Selected {category} unit {selected_res['id']} by minimum estimated completion "
                f"time ({duration:g} × (queue {selected_res.get('queue_length', 0)} + 1) minutes); "
                "ties use queue length, processing time, then resource ID."
            ),
        }

    def act(self, decision: Dict[str, Any], environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Reserve diagnostic equipment or emit conflict event."""
        sim_time = environment_state.get("simulation_time", 0.0)
        patient_id = environment_state.get("patient", {}).get(
            "id", decision.get("patient_id")
        )
        action = decision.get("action")
        if action == "ALLOCATE" and not self.reserve_resource(
            decision["resource"], patient_id
        ):
            refreshed = self.decide(self.perceive(environment_state))
            if refreshed.get("action") == "ALLOCATE" and self.reserve_resource(
                refreshed["resource"], patient_id
            ):
                decision = refreshed
            else:
                decision = {
                    **refreshed,
                    "action": "CONFLICT_WAITING",
                    "reason": "Selected diagnostic unit became unavailable; no other eligible unit remained.",
                }
                action = decision["action"]

        if action == "ALLOCATE":
            res = decision["resource"]
            duration = decision["duration"]
            res["status"] = ResourceStatus.BUSY.value
            res["current_patient_id"] = patient_id
            res["availability_timestamp"] = sim_time + duration

            self.diagnostic_assignments[patient_id] = res["id"]
            if patient_id not in self.active_patients:
                self.active_patients.append(patient_id)
            self.current_process_id = patient_id
            self.status = "SCANNING"

            self.emit_event(
                simulation_time=sim_time,
                event_type="DIAGNOSTIC_ASSIGNED",
                description=f"Resource {res['name']} ({res['id']}) booked for Patient {patient_id}. Duration: {duration} mins.",
                patient_id=patient_id,
                resource_id=res["id"],
                outcome="SUCCESS",
            )

            msg = self.send_message(
                receiver="HospitalCoordinator",
                message_type=MessageType.DIAGNOSTIC_ASSIGNED,
                patient_id=patient_id,
                resource_id=res["id"],
                simulation_time=sim_time,
                payload={"diagnostic_id": res["id"], "duration": duration, "category": res["category"]},
            )

            return {
                "status": "ALLOCATED",
                "resource_id": res["id"],
                "duration": duration,
                "message": msg,
            }

        elif action == "CONFLICT_WAITING":
            self.status = "WAITING_RESOURCE"
            self.emit_event(
                simulation_time=sim_time,
                event_type="RESOURCE_CONFLICT",
                description=f"Diagnostic queue formed for Patient {patient_id}: {decision.get('reason')}",
                patient_id=patient_id,
                outcome="WAITING",
                is_conflict=True,
            )

            msg = self.send_message(
                receiver="HospitalCoordinator",
                message_type=MessageType.RESOURCE_UNAVAILABLE,
                patient_id=patient_id,
                simulation_time=sim_time,
                payload={"resource_type": "diagnostic", "category": decision.get("category"), "reason": decision.get("reason")},
            )

            return {
                "status": "WAITING",
                "reason": decision.get("reason"),
                "message": msg,
            }

        return {"status": "NOT_REQUIRED"}

    def release_diagnostic(
        self,
        resource_id: str,
        resources: List[Dict[str, Any]],
        simulation_time: float = 0.0,
        expected_patient_id: Optional[str] = None,
    ):
        """Release diagnostic scanner equipment upon scan completion."""
        sim_time = simulation_time
        for res in resources:
            if res["id"] == resource_id:
                released_pid = res.get("current_patient_id")
                if expected_patient_id and released_pid != expected_patient_id:
                    return None
                if not self.release_resource(res, expected_patient_id or released_pid):
                    return None
                res["availability_timestamp"] = sim_time
                if released_pid and released_pid in self.active_patients:
                    self.active_patients.remove(released_pid)
                if released_pid in self.diagnostic_assignments:
                    del self.diagnostic_assignments[released_pid]

                self.emit_event(
                    simulation_time=sim_time,
                    event_type="RESOURCE_RELEASED",
                    description=f"Scanner {res['name']} ({resource_id}) scan complete and sanitized.",
                    patient_id=released_pid,
                    resource_id=resource_id,
                    outcome="SUCCESS",
                )

                self.send_message(
                    receiver="HospitalCoordinator",
                    message_type=MessageType.RESOURCE_RELEASED,
                    patient_id=released_pid,
                    resource_id=resource_id,
                    simulation_time=sim_time,
                    payload={"resource_type": "diagnostic", "resource_id": resource_id},
                )
                break

        self.status = "SCANNING" if self.active_patients else "IDLE"
        self.current_process_id = self.active_patients[0] if self.active_patients else None
