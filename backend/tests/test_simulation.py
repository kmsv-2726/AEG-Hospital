"""
Tests for Discrete-Event Simulation Engine and FSM state validation.
"""
import pytest
import copy
from backend.app.simulation.engine import SimulationEngine
from backend.app.simulation.scenarios import DEMO_PATIENTS, DEMO_RESOURCES
from backend.app.models.enums import AllocationStrategy, WorkflowState
from backend.app.workflows.patient_workflow import PatientWorkflowFSM, WorkflowTransitionError
from backend.app.coordinator.hospital_coordinator import HospitalCoordinator


def test_workflow_fsm_validations():
    # Valid transition
    assert PatientWorkflowFSM.can_transition(WorkflowState.REGISTERED, WorkflowState.TRIAGED)
    assert PatientWorkflowFSM.can_transition(WorkflowState.TRIAGED, WorkflowState.AMBULANCE_ASSIGNED)
    assert PatientWorkflowFSM.can_transition(WorkflowState.AMBULANCE_ASSIGNED, WorkflowState.IN_TRANSIT)

    # Invalid jump
    assert not PatientWorkflowFSM.can_transition(WorkflowState.REGISTERED, WorkflowState.COMPLETED)
    assert not PatientWorkflowFSM.can_transition(WorkflowState.TRIAGED, WorkflowState.ADMITTED)
    assert not PatientWorkflowFSM.can_transition(WorkflowState.WAITING_FOR_ICU, WorkflowState.TREATMENT_SIMULATED)
    with pytest.raises(WorkflowTransitionError):
        PatientWorkflowFSM.validate_transition(WorkflowState.REGISTERED, WorkflowState.COMPLETED, "P001")


def test_runtime_rejects_and_logs_invalid_transition():
    coordinator = HospitalCoordinator()
    patient = {"id": "P900", "workflow_state": WorkflowState.REGISTERED.value}

    with pytest.raises(WorkflowTransitionError):
        coordinator.transition_patient(patient, WorkflowState.COMPLETED, 0.0)

    assert patient["workflow_state"] == WorkflowState.REGISTERED.value
    assert coordinator.event_log[-1].event_type == "WORKFLOW_TRANSITION_REJECTED"
    assert coordinator.event_log[-1].outcome == "REJECTED"


def test_simulation_engine_complete_run():
    engine = SimulationEngine(strategy=AllocationStrategy.PRIORITY_AWARE)
    engine.load_scenario(DEMO_PATIENTS, DEMO_RESOURCES)
    metrics = engine.run_until_complete(max_steps=500)

    assert metrics.total_patients == 5
    assert metrics.completed_workflows == 5
    assert metrics.workflow_completion_rate == 100.0
    assert metrics.resource_conflicts > 0
    assert metrics.unresolved_requests == 0
    assert metrics.average_waiting_time is not None
    assert len(engine.all_events) > 10


def test_simulation_reproducibility():
    """Verify that running two independent engines from the same state yields identical metrics."""
    engine1 = SimulationEngine(strategy=AllocationStrategy.PRIORITY_AWARE, seed=42)
    engine1.load_scenario(DEMO_PATIENTS, DEMO_RESOURCES)
    metrics1 = engine1.run_until_complete()

    engine2 = SimulationEngine(strategy=AllocationStrategy.PRIORITY_AWARE, seed=42)
    engine2.load_scenario(DEMO_PATIENTS, DEMO_RESOURCES)
    metrics2 = engine2.run_until_complete()

    assert metrics1.average_waiting_time == metrics2.average_waiting_time
    assert metrics1.resource_conflicts == metrics2.resource_conflicts
    assert metrics1.simulation_duration == metrics2.simulation_duration


def test_doctor_is_released_at_exam_completion():
    patient = copy.deepcopy(DEMO_PATIENTS[-1])
    engine = SimulationEngine(strategy=AllocationStrategy.PRIORITY_AWARE)
    engine.load_scenario([patient], DEMO_RESOURCES)

    engine.step()
    engine.step()
    doctor_id = engine.patients[patient["id"]]["assigned_doctor_id"]
    doctor = next(item for item in engine.doctors if item["id"] == doctor_id)
    assert doctor["status"] == "BUSY"

    engine.step()

    assert doctor["status"] == "AVAILABLE"
    assert engine.patients[patient["id"]]["workflow_state"] == WorkflowState.TREATMENT_SIMULATED.value
