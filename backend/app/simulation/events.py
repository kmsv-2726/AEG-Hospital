"""
Simulation events and priority queue event model.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(order=True)
class SimEvent:
    """
    Discrete simulation event prioritized by simulation_time, then event_id.
    """
    time: float
    event_id: int
    event_type: str = field(compare=False)
    patient_id: Optional[str] = field(compare=False, default=None)
    resource_id: Optional[str] = field(compare=False, default=None)
    payload: Dict[str, Any] = field(compare=False, default_factory=dict)
