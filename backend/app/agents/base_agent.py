"""
Base Agent class defining the standardized intelligent agent lifecycle and communication interface.
Enhanced with autonomous message processing, inboxes, and process tracking.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from threading import Lock
import uuid
from backend.app.schemas.hospital_schemas import AgentMessageSchema, SimulationEventSchema
from backend.app.models.enums import MessageType


class BaseAgent(ABC):
    """
    Abstract Base Class for all specialized agents in the Smart Hospital MAS.
    Implements PEAS foundation: Percepts, Actions, Goals, Environment interactions.
    Now equipped with an autonomous message queue and process tracking.
    """

    def __init__(self, agent_id: str, name: str, role: str):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.status: str = "IDLE"  # IDLE, ACTIVE, BUSY, WAITING, EXAMINING, etc.
        self.last_action: Optional[str] = None
        self.last_message: Optional[str] = None
        self.current_process_id: Optional[str] = None
        self.active_patients: List[str] = []
        self.pending_requests: List[Dict[str, Any]] = []
        self.event_log: List[SimulationEventSchema] = []
        self.inbox: List[AgentMessageSchema] = []
        self.outbox: List[AgentMessageSchema] = []
        self.message_bus: Optional[Any] = None
        self._resource_lock = Lock()

    def reserve_resource(self, resource: Dict[str, Any], patient_id: str) -> bool:
        """Atomically reserve an available resource for one patient."""
        with self._resource_lock:
            if resource.get("status") != "AVAILABLE":
                return False
            resource["status"] = "BUSY"
            resource["current_patient_id"] = patient_id
            return True

    def release_resource(self, resource: Dict[str, Any], patient_id: Optional[str]) -> bool:
        """Atomically release a resource only when the patient owns it."""
        with self._resource_lock:
            if (
                resource.get("status") != "BUSY"
                or resource.get("current_patient_id") != patient_id
            ):
                return False
            resource["status"] = "AVAILABLE"
            resource["current_patient_id"] = None
            return True

    def set_message_bus(self, message_bus: Any):
        """Attach message bus and register reactive listener."""
        self.message_bus = message_bus
        if message_bus:
            message_bus.register_agent(self.name, self.handle_message_wrapper)

    def handle_message_wrapper(self, message: AgentMessageSchema) -> Optional[AgentMessageSchema]:
        """Entry wrapper for incoming messages from the message bus."""
        self.inbox.append(message)
        self.last_message = f"Received {message.message_type.value} from {message.sender}"
        return self.handle_message(message, {})

    def get_status(self) -> Dict[str, Any]:
        """Return agent status dictionary for monitoring."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "status": self.status,
            "last_action": self.last_action,
            "last_message": self.last_message,
            "pending_count": len(self.pending_requests),
            "inbox_count": len(self.inbox),
            "active_patients": list(self.active_patients),
            "current_process_id": self.current_process_id,
        }

    def emit_event(
        self,
        simulation_time: float,
        event_type: str,
        description: str,
        patient_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        outcome: str = "SUCCESS",
        is_conflict: bool = False,
    ) -> SimulationEventSchema:
        """Create and record an explainable simulation event."""
        event = SimulationEventSchema(
            simulation_time=simulation_time,
            event_type=event_type,
            agent=self.name,
            patient_id=patient_id,
            resource_id=resource_id,
            description=description,
            outcome=outcome,
            is_conflict=is_conflict,
        )
        self.event_log.append(event)
        self.last_action = f"{event_type}: {description}"
        return event

    def send_message(
        self,
        receiver: str,
        message_type: MessageType,
        patient_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        simulation_time: float = 0.0,
        correlation_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> AgentMessageSchema:
        """Construct a structured message, send to message bus if attached, and enqueue in outbox."""
        msg_id = f"MSG-{uuid.uuid4().hex[:8].upper()}"
        msg = AgentMessageSchema(
            message_id=msg_id,
            sender=self.name,
            receiver=receiver,
            message_type=message_type,
            patient_id=patient_id,
            resource_id=resource_id,
            simulation_time=simulation_time,
            correlation_id=correlation_id or msg_id,
            payload=payload or {},
            status="PENDING",
        )
        self.outbox.append(msg)
        self.last_message = f"Sent {message_type.value} to {receiver} for {patient_id or 'N/A'}"
        
        if self.message_bus:
            self.message_bus.send_message(
                sender=self.name,
                receiver=receiver,
                message_type=message_type,
                patient_id=patient_id,
                resource_id=resource_id,
                simulation_time=simulation_time,
                correlation_id=msg.correlation_id,
                payload=payload,
                message_id=msg.message_id,
            )

        return msg

    @abstractmethod
    def perceive(self, environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect environmental state and extract relevant percepts."""
        pass

    @abstractmethod
    def decide(self, percepts: Dict[str, Any]) -> Dict[str, Any]:
        """Execute deterministic rule-based or utility-ranked decision logic."""
        pass

    @abstractmethod
    def act(self, decision: Dict[str, Any], environment_state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the decided action on the shared environment."""
        pass

    def handle_message(
        self, message: AgentMessageSchema, environment_state: Dict[str, Any]
    ) -> Optional[AgentMessageSchema]:
        """Receive an incoming structured message and route to internal handling logic."""
        self.last_message = f"Received {message.message_type.value} from {message.sender}"
        return None
