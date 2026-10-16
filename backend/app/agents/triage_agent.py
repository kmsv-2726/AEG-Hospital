"""
Triage Agent: Evaluates patient condition and assigns synthetic priority.
"""
from typing import Dict, Any, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.models.enums import PriorityLevel, MessageType


class TriageAgent(BaseAgent):
    """
    Assigns synthetic emergency priority according to predefined simulation rules.
    Purely deterministic rule-based evaluation without external LLMs.
    """

    def __init__(self, agent_id: str = "AGENT-TRIAGE", name: str = "TriageAgent"):
        super().__init__(agent_id=agent_id, name=name, role="Triage Coordinator")

    def perceive(self, environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient severity and symptoms from environment state."""
        patient_data = environment_state.get("patient", {})
        return {
            "patient_id": patient_data.get("id"),
            "severity_category": patient_data.get("severity_category", ""),
            "condition_description": patient_data.get("condition_description", ""),
            "arrival_time": patient_data.get("arrival_time", 0.0),
        }

    def decide(self, percepts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate deterministic triage rules:
        - Critical trauma / cardiac / arrest -> P1 (Critical)
        - High trauma / severe compound -> P2 (High)
        - Moderate injury / fracture -> P3 (Moderate)
        - Low severity / dehydration / minor -> P4 (Low)
        """
        severity = percepts.get("severity_category", "").lower()
        description = percepts.get("condition_description", "").lower()

        if any(term in severity or term in description for term in ["critical", "cardiac", "arrest", "bleeding", "shock"]):
            priority = PriorityLevel.P1
            reason = "Simulation rule matched critical emergency indicators (P1)."
        elif any(term in severity or term in description for term in ["high", "severe", "compound", "fracture with compromise"]):
            priority = PriorityLevel.P2
            reason = "Simulation rule matched high-priority urgent trauma indicators (P2)."
        elif any(term in severity or term in description for term in ["moderate", "injury", "wrist", "laceration"]):
            priority = PriorityLevel.P3
            reason = "Simulation rule matched moderate non-life-threatening category (P3)."
        else:
            priority = PriorityLevel.P4
            reason = "Simulation rule assigned low-severity ambulatory priority (P4)."

        return {
            "patient_id": percepts.get("patient_id"),
            "priority": priority,
            "reason": reason,
        }

    def act(self, decision: Dict[str, Any], environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Record triage event and send message to HospitalCoordinator."""
        sim_time = environment_state.get("simulation_time", 0.0)
        patient_id = decision["patient_id"]
        priority = decision["priority"]
        reason = decision["reason"]

        self.emit_event(
            simulation_time=sim_time,
            event_type="TRIAGE_COMPLETED",
            description=f"Patient {patient_id} assigned {priority.value}: {reason}",
            patient_id=patient_id,
            outcome="SUCCESS",
        )

        msg = self.send_message(
            receiver="HospitalCoordinator",
            message_type=MessageType.TRIAGE_COMPLETED,
            patient_id=patient_id,
            simulation_time=sim_time,
            payload={"priority": priority.value, "reason": reason},
        )

        return {
            "status": "TRIAGE_COMPLETED",
            "patient_id": patient_id,
            "priority": priority.value,
            "reason": reason,
            "message": msg,
        }
