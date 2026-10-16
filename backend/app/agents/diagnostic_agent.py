"""
Diagnostic Agent: Manages imaging, scans, laboratory equipment, and queueing.
"""
from typing import Dict, Any, List, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.models.enums import ResourceStatus, MessageType, DiagnosticCategory


class DiagnosticAgent(BaseAgent):
    """
    Allocates simulated diagnostic equipment (CT, MRI, X-Ray, Labs, Ultrasound)
    and handles equipment queuing and releases.
    """

    def __init__(self, agent_id: str = "AGENT-DIAG", name: str = "DiagnosticAgent"):
        super().__init__(agent_id=agent_id, name=name, role="Diagnostic Equipment Coordinator")

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

        eligible = [
            res for res in percepts["resources"]
            if res.get("status") == ResourceStatus.AVAILABLE.value
            and res.get("category") == category
        ]

        if not eligible:
            return {
                "action": "CONFLICT_WAITING",
                "patient_id": patient_id,
                "category": category,
                "reason": f"Diagnostic resource '{category}' is currently busy or unavailable. Request queued.",
            }

        # Stage 2: Shortest queue / duration
        eligible.sort(key=lambda r: (r.get("queue_length", 0), r.get("simulated_duration", 15.0), r["id"]))
        selected_res = eligible[0]
        duration = selected_res.get("simulated_duration", 15.0)

        return {
            "action": "ALLOCATE",
            "patient_id": patient_id,
            "resource": selected_res,
            "duration": duration,
            "reason": f"Allocated available {category} scanner ({selected_res['id']}). Duration: {duration} mins.",
        }

    def act(self, decision: Dict[str, Any], environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Reserve diagnostic equipment or emit conflict event."""
        sim_time = environment_state.get("simulation_time", 0.0)
        patient_id = decision.get("patient_id")
        action = decision.get("action")

        if action == "ALLOCATE":
            res = decision["resource"]
            duration = decision["duration"]
            res["status"] = ResourceStatus.BUSY.value
            res["current_patient_id"] = patient_id
            res["availability_timestamp"] = sim_time + duration

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
            self.emit_event(
                simulation_time=sim_time,
                event_type="RESOURCE_UNAVAILABLE",
                description=f"Diagnostic conflict for Patient {patient_id}: {decision['reason']}",
                patient_id=patient_id,
                outcome="CONFLICT_WAITING",
                is_conflict=True,
            )

            msg = self.send_message(
                receiver="HospitalCoordinator",
                message_type=MessageType.RESOURCE_UNAVAILABLE,
                patient_id=patient_id,
                simulation_time=sim_time,
                payload={"resource_type": "DIAGNOSTIC", "category": decision.get("category"), "reason": decision["reason"]},
            )

            return {"status": "WAITING", "reason": decision["reason"], "message": msg}

        return {"status": "SKIPPED"}

    def release_diagnostic(
        self, resource_id: str, resources: List[Dict[str, Any]], simulation_time: float
    ) -> Optional[Dict[str, Any]]:
        """Release diagnostic scanner back to service pool."""
        for res in resources:
            if res["id"] == resource_id:
                res["status"] = ResourceStatus.AVAILABLE.value
                prev_patient = res.get("current_patient_id")
                res["current_patient_id"] = None

                self.emit_event(
                    simulation_time=simulation_time,
                    event_type="RESOURCE_RELEASED",
                    description=f"Diagnostic resource {res['name']} completed scan and is now available.",
                    patient_id=prev_patient,
                    resource_id=resource_id,
                    outcome="RELEASED",
                )
                self.send_message(
                    receiver="HospitalCoordinator",
                    message_type=MessageType.RESOURCE_RELEASED,
                    patient_id=prev_patient,
                    resource_id=resource_id,
                    simulation_time=simulation_time,
                    payload={"resource_type": "DIAGNOSTIC"},
                )
                return res
        return None
