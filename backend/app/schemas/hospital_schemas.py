"""
Pydantic schemas for data validation and API request/response serialization.
"""
from __future__ import annotations
import re
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from backend.app.models.enums import (
    PriorityLevel,
    WorkflowState,
    DoctorSpecialty,
    DiagnosticCategory,
    ResourceStatus,
    MessageType,
    AllocationStrategy,
)


class SimulationEventSchema(BaseModel):
    id: Optional[int] = None
    simulation_time: float
    event_type: str
    agent: str
    patient_id: Optional[str] = None
    resource_id: Optional[str] = None
    description: str
    outcome: str = "SUCCESS"
    is_conflict: bool = False

    model_config = ConfigDict(from_attributes=True)


class PatientBase(BaseModel):
    id: str = Field(..., description="Unique patient identifier, e.g. P001")
    name: str = Field(..., description="Synthetic patient full name")
    age: int = Field(default=35, ge=0, le=120)
    gender: str = Field(default="Unknown")
    condition_description: str = Field(..., description="Reported symptoms / condition")
    emergency_type: Optional[str] = Field(default=None, max_length=100)
    chief_complaint: Optional[str] = Field(default=None, max_length=255)
    symptoms: Optional[str] = Field(default=None, max_length=1000)
    heart_rate: Optional[int] = Field(default=None, ge=0, le=300)
    oxygen_saturation: Optional[float] = Field(default=None, ge=0, le=100)
    blood_pressure: Optional[str] = Field(default=None, max_length=32)
    severity_category: str = Field(..., description="e.g. Critical trauma, Cardiac arrest")
    priority: PriorityLevel = Field(default=PriorityLevel.P3)
    triage_mode: Literal["AUTO", "PROVIDED"] = "AUTO"
    requires_ambulance: bool = Field(default=True)
    required_equipment: List[str] = Field(default_factory=list, max_length=8)
    required_specialty: DoctorSpecialty = Field(default=DoctorSpecialty.GENERAL_MEDICINE)
    required_diagnostic: Optional[DiagnosticCategory] = Field(default=None)
    requires_icu: bool = Field(default=False)
    required_icu_equipment: List[str] = Field(default_factory=list, max_length=4)
    requires_ventilator: bool = Field(default=False)
    arrival_time: float = Field(default=0.0, ge=0.0)

    @field_validator("blood_pressure")
    @classmethod
    def validate_blood_pressure(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not value.strip():
            return None
        match = re.fullmatch(r"\s*(\d{2,3})\s*/\s*(\d{2,3})\s*", value)
        if not match:
            raise ValueError("Blood pressure must use systolic/diastolic format, e.g. 120/80")
        systolic, diastolic = (int(part) for part in match.groups())
        if not 40 <= systolic <= 300 or not 20 <= diastolic <= 200:
            raise ValueError("Blood pressure values are outside the supported synthetic input range")
        return f"{systolic}/{diastolic}"

    @field_validator("required_equipment", "required_icu_equipment")
    @classmethod
    def normalize_equipment(cls, values: List[str]) -> List[str]:
        return list(dict.fromkeys(value.strip() for value in values if value.strip()))


class PatientCreate(PatientBase):
    pass


class PatientRead(PatientBase):
    workflow_state: WorkflowState
    triage_reason: Optional[str] = None
    triage_requires_review: bool = False
    assigned_ambulance_id: Optional[str] = None
    assigned_doctor_id: Optional[str] = None
    assigned_diagnostic_id: Optional[str] = None
    assigned_icu_bed_id: Optional[str] = None
    hospital_arrival_time: Optional[float] = None
    ambulance_dispatch_time: Optional[float] = None
    doctor_request_time: Optional[float] = None
    doctor_assignment_time: Optional[float] = None
    diagnostic_request_time: Optional[float] = None
    diagnostic_start_time: Optional[float] = None
    diagnostic_end_time: Optional[float] = None
    icu_request_time: Optional[float] = None
    icu_reservation_time: Optional[float] = None
    treatment_start_time: Optional[float] = None
    completion_time: Optional[float] = None
    waiting_duration: float = 0.0
    decision_trace: List[Dict[str, Any]] = Field(default_factory=list)
    orchestration_events: Optional[List[SimulationEventSchema]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AmbulanceRead(BaseModel):
    id: str
    call_sign: str
    status: ResourceStatus
    simulated_location: str
    base_distance_km: float
    equipment_capabilities: str
    current_patient_id: Optional[str] = None
    availability_timestamp: float
    total_busy_time: float
    total_dispatches: int

    model_config = ConfigDict(from_attributes=True)


class DoctorRead(BaseModel):
    id: str
    name: str
    specialty: DoctorSpecialty
    status: ResourceStatus
    workload_count: int
    current_patient_id: Optional[str] = None
    availability_timestamp: float
    total_busy_time: float

    model_config = ConfigDict(from_attributes=True)


class DiagnosticResourceRead(BaseModel):
    id: str
    name: str
    category: DiagnosticCategory
    status: ResourceStatus
    queue_length: int
    simulated_duration: float
    current_patient_id: Optional[str] = None
    availability_timestamp: float
    total_busy_time: float

    model_config = ConfigDict(from_attributes=True)


class ICUBedRead(BaseModel):
    id: str
    unit_name: str
    status: ResourceStatus
    has_ventilator: bool
    has_monitoring: bool = True
    current_patient_id: Optional[str] = None
    reservation_timestamp: Optional[float] = None
    release_timestamp: Optional[float] = None
    total_busy_time: float

    model_config = ConfigDict(from_attributes=True)


class ResourceSummary(BaseModel):
    ambulances: List[AmbulanceRead]
    doctors: List[DoctorRead]
    diagnostic_resources: List[DiagnosticResourceRead]
    icu_beds: List[ICUBedRead]
    counts: Dict[str, Dict[str, int]]


class AgentMessageSchema(BaseModel):
    message_id: str
    sender: str
    receiver: str
    message_type: MessageType
    patient_id: Optional[str] = None
    resource_id: Optional[str] = None
    simulation_time: float = 0.0
    correlation_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: str = "PROCESSED"

    model_config = ConfigDict(from_attributes=True)



class AgentStatusRead(BaseModel):
    name: str
    role: str
    status: str
    last_action: Optional[str] = None
    last_message: Optional[str] = None
    pending_count: int = 0
    assigned_resources: List[str] = Field(default_factory=list)
    active_patients: List[str] = Field(default_factory=list)
    current_process_id: Optional[str] = None
    inbox_count: int = 0
    recent_messages: List[AgentMessageSchema] = Field(default_factory=list)


class SimulationStartRequest(BaseModel):
    strategy: AllocationStrategy = AllocationStrategy.PRIORITY_AWARE
    step_delay_ms: int = Field(default=0, ge=0)


class SimulationResetRequest(BaseModel):
    preserve_scenario: bool = True


class MetricsSummary(BaseModel):
    average_waiting_time: Optional[float] = None
    average_ambulance_wait: Optional[float] = None
    average_ambulance_response_time: Optional[float] = None
    average_time_to_doctor: Optional[float] = None
    average_time_to_diagnostics: Optional[float] = None
    average_time_to_icu: Optional[float] = None
    ambulance_utilization: float = 0.0
    doctor_utilization: float = 0.0
    diagnostic_utilization: float = 0.0
    icu_utilization: float = 0.0
    unresolved_requests: int = 0
    resource_conflicts: int = 0
    workflow_completion_rate: float = 0.0
    total_patients: int = 0
    completed_workflows: int = 0
    strategy: str = "PRIORITY_AWARE"
    simulation_duration: float = 0.0
    detailed_observations: Dict[str, Any] = Field(default_factory=dict)


class OSManagerStatusRead(BaseModel):
    process_counts: Dict[str, int]
    total_processes: int
    ready_queue_length: int
    ready_queue_pids: List[str]
    average_turnaround_time: float
    average_waiting_time: float
    doctor_cpu_utilization_pct: float
    diagnostic_io_utilization_pct: float
    icu_semaphore: Dict[str, Any]
    ambulance_semaphore: Dict[str, Any]
    doctor_mutexes: List[Dict[str, Any]]
    diagnostic_mutexes: List[Dict[str, Any]]
    pcbs: List[Dict[str, Any]]


class OrchestrationStep(BaseModel):
    agent: str
    action: str
    timestamp: float
    description: str
    status: str
    details: Dict[str, Any] = Field(default_factory=dict)


class PatientOrchestrationResponse(BaseModel):
    patient: PatientRead
    pcb: Optional[Dict[str, Any]] = None
    orchestration_steps: List[OrchestrationStep] = Field(default_factory=list)
    agent_messages: List[AgentMessageSchema] = Field(default_factory=list)
    events: List[SimulationEventSchema] = Field(default_factory=list)

