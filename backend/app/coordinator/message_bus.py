"""
Autonomous Multi-Agent Message Bus (MAS Backbone).
Provides:
- Asynchronous and event-driven message dispatching between agents
- Inboxes and outboxes for decentralized agent communication
- Message logging and causal trace tracking (correlation_id)
- Peer-to-peer and broadcast messaging patterns
"""
from typing import Dict, Any, List, Optional, Callable
import uuid
from backend.app.schemas.hospital_schemas import AgentMessageSchema
from backend.app.models.enums import MessageType


class AgentMessageBus:
    """
    Decentralized message broker enabling autonomous communication between:
    - TriageAgent
    - AmbulanceAgent
    - DoctorAgent
    - DiagnosticAgent
    - ICUAgent
    - HospitalCoordinator
    """
    def __init__(self):
        self.subscribers: Dict[str, List[Callable[[AgentMessageSchema], Optional[AgentMessageSchema]]]] = {}
        self.message_history: List[AgentMessageSchema] = []
        self.agent_inboxes: Dict[str, List[AgentMessageSchema]] = {}

    def register_agent(self, agent_name: str, message_handler: Callable[[AgentMessageSchema], Optional[AgentMessageSchema]]):
        """Register an agent's reactive message handler."""
        if agent_name not in self.subscribers:
            self.subscribers[agent_name] = []
        self.subscribers[agent_name].append(message_handler)
        if agent_name not in self.agent_inboxes:
            self.agent_inboxes[agent_name] = []

    def send_message(
        self,
        sender: str,
        receiver: str,
        message_type: MessageType,
        patient_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        simulation_time: float = 0.0,
        correlation_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> AgentMessageSchema:
        """Construct, log, and route an agent message."""
        msg_id = f"MSG-{uuid.uuid4().hex[:8].upper()}"
        msg = AgentMessageSchema(
            message_id=msg_id,
            sender=sender,
            receiver=receiver,
            message_type=message_type,
            patient_id=patient_id,
            resource_id=resource_id,
            simulation_time=simulation_time,
            correlation_id=correlation_id or msg_id,
            payload=payload or {},
            status="DELIVERED",
        )
        self.message_history.append(msg)

        # Place into receiver's inbox
        if receiver in self.agent_inboxes:
            self.agent_inboxes[receiver].append(msg)
        elif receiver == "*":
            # Broadcast to all inboxes
            for inbox in self.agent_inboxes.values():
                inbox.append(msg)

        return msg

    def dispatch(self, message: AgentMessageSchema) -> List[AgentMessageSchema]:
        """
        Deliver message to registered agent handler(s) and collect any resulting response messages.
        """
        responses = []
        handlers = []

        if message.receiver == "*":
            for h_list in self.subscribers.values():
                handlers.extend(h_list)
        elif message.receiver in self.subscribers:
            handlers = self.subscribers[message.receiver]

        for handler in handlers:
            try:
                res = handler(message)
                if res and isinstance(res, AgentMessageSchema):
                    responses.append(res)
                    self.message_history.append(res)
            except Exception as e:
                print(f"[MessageBus Error] Handler exception for {message.receiver}: {e}")

        return responses

    def get_messages_for_patient(self, patient_id: str) -> List[AgentMessageSchema]:
        """Retrieve full chronological conversation transcript for a given patient."""
        return [m for m in self.message_history if m.patient_id == patient_id]

    def clear(self):
        """Reset message bus state."""
        self.message_history.clear()
        for inbox in self.agent_inboxes.values():
            inbox.clear()
