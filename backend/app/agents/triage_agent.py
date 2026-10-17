"""
Triage Agent: Evaluates patient condition and assigns synthetic priority.
Enhanced with autonomous message handling and status progression.
"""
from typing import Dict, Any, Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.models.enums import PriorityLevel, MessageType
from backend.app.schemas.hospital_schemas import AgentMessageSchema


class TriageAgent(BaseAgent):
    """
    Assigns synthetic emergency priority according to predefined simulation rules.
    Purely deterministic rule-based evaluation without external LLMs.
    """

    def __init__(self, agent_id: str = "AGENT-TRIAGE", name: str = "TriageAgent"):
        super().__init__(agent_id=agent_id, name=name, role="Triage Coordinator")

    def handle_message(self, message: AgentMessageSchema, environment_state: Dict[str, Any]) -> Optional[AgentMessageSchema]:
        """Autonomously react to incoming triage requests."""
        if message.message_type in (MessageType.TRIAGE_REQUEST, MessageType.PATIENT_REGISTERED):
            patient_data = message.payload.get("patient", {})
            if not patient_data and message.patient_id:
                patient_data = {"id": message.patient_id, "severity_category": message.payload.get("severity_category", "")}
            env = {"patient": patient_data, "simulation_time": message.simulation_time}
            percepts = self.perceive(env)
            decision = self.decide(percepts)
            res = self.act(decision, env)
            return res.get("message")
        return None

    def perceive(self, environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patient severity and symptoms from environment state."""
        patient_data = environment_state.get("patient", {})
        pid = patient_data.get("id")
        self.current_process_id = pid
        self.status = "TRIAGING"
        if pid and pid not in self.active_patients:
            self.active_patients.append(pid)

        return {
            "patient_id": pid,
            "severity_category": patient_data.get("severity_category", ""),
            "emergency_type": patient_data.get("emergency_type") or "",
            "condition_description": patient_data.get("condition_description", ""),
            "chief_complaint": patient_data.get("chief_complaint", ""),
            "symptoms": patient_data.get("symptoms", ""),
            "heart_rate": patient_data.get("heart_rate"),
            "oxygen_saturation": patient_data.get("oxygen_saturation"),
            "blood_pressure": patient_data.get("blood_pressure"),
            "triage_mode": patient_data.get("triage_mode", "AUTO"),
            "provided_priority": patient_data.get("priority", "P3"),
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
        description = " ".join((
            percepts.get("emergency_type") or "",
            percepts.get("condition_description") or "",
            percepts.get("chief_complaint") or "",
            percepts.get("symptoms") or "",
        )).lower()

        if percepts.get("triage_mode") == "PROVIDED":
            priority = PriorityLevel(percepts.get("provided_priority", "P3"))
            return {
                "patient_id": percepts.get("patient_id"),
                "priority": priority,
                "reason": "Priority was explicitly provided by the operator; deterministic symptom rules were not used.",
                "requires_review": False,
                "mode": "PROVIDED",
            }

        if any(term in severity or term in description for term in ["critical", "cardiac", "arrest", "bleeding", "shock"]):
            priority = PriorityLevel.P1
            reason = "Deterministic clinical rule matched critical emergency indicators (P1)."
        elif any(term in severity or term in description for term in ["high", "severe", "compound", "fracture with compromise"]):
            priority = PriorityLevel.P2
            reason = "Deterministic clinical rule matched high-priority urgent trauma indicators (P2)."
        elif any(term in severity or term in description for term in ["moderate", "injury", "wrist", "laceration"]):
            priority = PriorityLevel.P3
            reason = "Deterministic clinical rule matched moderate non-life-threatening category (P3)."
        elif any(term in severity or term in description for term in ["low", "minor", "mild", "dehydration", "fever"]):
            priority = PriorityLevel.P4
            reason = "Deterministic synthetic rule matched the configured low-severity category (P4)."
        else:
            priority = PriorityLevel.P3
            reason = "No configured category rule matched. Provisional P3 is assigned for simulation ordering; human assessment is required."

        return {
            "patient_id": percepts.get("patient_id"),
            "priority": priority,
            "reason": reason,
            "requires_review": "No configured category rule matched" in reason,
            "mode": "AUTO",
        }

    def act(self, decision: Dict[str, Any], environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Record triage event and send message to HospitalCoordinator and downstream agents."""
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

        # Autonomous structured notification to coordinator
        msg = self.send_message(
            receiver="HospitalCoordinator",
            message_type=MessageType.TRIAGE_COMPLETED,
            patient_id=patient_id,
            simulation_time=sim_time,
            payload={
                "priority": priority.value,
                "reason": reason,
                "requires_review": decision.get("requires_review", False),
                "triage_mode": decision.get("mode", "AUTO"),
            },
        )

        self.status = "IDLE"
        if patient_id in self.active_patients:
            self.active_patients.remove(patient_id)

        return {
            "status": "TRIAGE_COMPLETED",
            "patient_id": patient_id,
            "priority": priority.value,
            "reason": reason,
            "requires_review": decision.get("requires_review", False),
            "mode": decision.get("mode", "AUTO"),
            "message": msg,
        }
