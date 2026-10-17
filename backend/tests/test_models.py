"""
Tests for domain models, enums, and schemas.
"""
from backend.app.models.enums import (
    PriorityLevel,
    WorkflowState,
    DoctorSpecialty,
    DiagnosticCategory,
    ResourceStatus,
    MessageType,
    AllocationStrategy,
)
from backend.app.schemas.hospital_schemas import (
    PatientCreate,
    AgentMessageSchema,
    SimulationEventSchema,
    MetricsSummary,
)
from pydantic import ValidationError
from backend.app.models.entities import (
    PatientModel,
    AmbulanceModel,
    DoctorModel,
    DiagnosticResourceModel,
    ICUBedModel,
    AgentMessageModel,
)


def test_enums():
    assert PriorityLevel.P1.value == "P1"
    assert WorkflowState.TRIAGED.value == "TRIAGED"
    assert DoctorSpecialty.TRAUMA.value == "Trauma"
    assert DiagnosticCategory.CT.value == "CT"
    assert ResourceStatus.AVAILABLE.value == "AVAILABLE"
    assert MessageType.AMBULANCE_REQUEST.value == "AMBULANCE_REQUEST"
    assert AllocationStrategy.FIFO.value == "FIFO"


def test_patient_pydantic_schema():
    patient = PatientCreate(
        id="P001",
        name="Alex Smith",
        age=32,
        gender="Male",
        condition_description="Severe blunt trauma after motor collision",
        severity_category="Critical trauma",
        priority=PriorityLevel.P1,
        requires_ambulance=True,
        required_specialty=DoctorSpecialty.TRAUMA,
        required_diagnostic=DiagnosticCategory.XRAY,
        requires_icu=True,
        arrival_time=0.0,
    )
    assert patient.id == "P001"
    assert patient.priority == PriorityLevel.P1
    assert patient.required_specialty == DoctorSpecialty.TRAUMA


def test_patient_optional_inputs_are_validated_and_normalized():
    patient = PatientCreate(
        id="CLI-CASE-01",
        name="Synthetic Case",
        condition_description="Synthetic case details",
        severity_category="Unclassified",
        emergency_type="General emergency",
        chief_complaint="Reported concern",
        blood_pressure=" 120 / 80 ",
        required_equipment=[" ALS ", "", "ALS"],
    )

    assert patient.blood_pressure == "120/80"
    assert patient.required_equipment == ["ALS"]
    with pytest.raises(ValidationError):
        PatientCreate(
            id="CLI-CASE-02",
            name="Invalid Blood Pressure",
            condition_description="Synthetic case details",
            severity_category="Unclassified",
            blood_pressure="not-a-value",
        )


def test_agent_message_schema():
    msg = AgentMessageSchema(
        message_id="MSG-001",
        sender="TriageAgent",
        receiver="HospitalCoordinator",
        message_type=MessageType.TRIAGE_COMPLETED,
        patient_id="P001",
        simulation_time=0.0,
        payload={"priority": "P1"},
    )
    assert msg.sender == "TriageAgent"
    assert msg.message_type == MessageType.TRIAGE_COMPLETED
    assert msg.payload["priority"] == "P1"


def test_metrics_summary_default():
    metrics = MetricsSummary(
        strategy="PRIORITY_AWARE",
        total_patients=5,
        completed_workflows=5,
        workflow_completion_rate=100.0,
    )
    assert metrics.workflow_completion_rate == 100.0
    assert metrics.average_waiting_time is None
