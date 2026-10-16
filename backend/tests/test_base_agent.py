"""
Unit tests for BaseAgent class.
"""
from typing import Dict, Any
from backend.app.agents.base_agent import BaseAgent
from backend.app.models.enums import MessageType


class MockAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="MOCK-01", name="MockAgent", role="Testing Agent")

    def perceive(self, environment_state: Dict[str, Any]) -> Dict[str, Any]:
        return {"item_count": len(environment_state.get("items", []))}

    def decide(self, percepts: Dict[str, Any]) -> Dict[str, Any]:
        if percepts["item_count"] > 0:
            return {"action": "PROCESS", "count": percepts["item_count"]}
        return {"action": "WAIT"}

    def act(self, decision: Dict[str, Any], environment_state: Dict[str, Any]) -> Dict[str, Any]:
        self.emit_event(
            simulation_time=1.0,
            event_type="MOCK_ACTION",
            description=f"Executed {decision['action']}",
        )
        return {"status": "SUCCESS", "decision": decision}


def test_base_agent_lifecycle():
    agent = MockAgent()
    status = agent.get_status()
    assert status["name"] == "MockAgent"
    assert status["status"] == "IDLE"

    # Test perceive -> decide -> act
    env = {"items": ["task_a", "task_b"]}
    percepts = agent.perceive(env)
    assert percepts["item_count"] == 2

    decision = agent.decide(percepts)
    assert decision["action"] == "PROCESS"

    result = agent.act(decision, env)
    assert result["status"] == "SUCCESS"
    assert len(agent.event_log) == 1
    assert "MOCK_ACTION" in agent.last_action


def test_base_agent_messaging():
    agent = MockAgent()
    msg = agent.send_message(
        receiver="HospitalCoordinator",
        message_type=MessageType.TRIAGE_COMPLETED,
        patient_id="P001",
        simulation_time=2.5,
        payload={"priority": "P1"},
    )
    assert msg.sender == "MockAgent"
    assert msg.receiver == "HospitalCoordinator"
    assert len(agent.outbox) == 1
    assert "Sent TRIAGE_COMPLETED" in agent.last_message
