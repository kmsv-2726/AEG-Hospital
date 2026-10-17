"""
Unit and integration tests for HospitalCoordinator.
"""
from backend.app.coordinator.hospital_coordinator import HospitalCoordinator
from backend.app.models.enums import AllocationStrategy, WorkflowState, ResourceStatus
from backend.app.models.os_primitives import ProcessState


def test_coordinator_patient_registration_and_triage():
    coord = HospitalCoordinator(strategy=AllocationStrategy.PRIORITY_AWARE)
    patient = {
        "id": "P001",
        "name": "Alex Smith",
        "severity_category": "Critical trauma",
        "condition_description": "Hypovolemic shock, multiple trauma",
        "requires_ambulance": True,
        "required_specialty": "Trauma",
        "arrival_time": 0.0,
    }
    env = {"simulation_time": 0.0}
    triage_result = coord.handle_patient_registration(patient, env)

    assert triage_result["priority"] == "P1"
    assert patient["workflow_state"] == WorkflowState.TRIAGED.value
    assert coord.os_manager.pcbs["P001"].base_priority == "P1"
    assert coord.os_manager.pcbs["P001"].numeric_priority == 1
    assert patient["decision_trace"][0]["agent"] == "TriageAgent"
    assert len(coord.event_log) >= 2


def test_coordinator_queue_sorting():
    coord_prio = HospitalCoordinator(strategy=AllocationStrategy.PRIORITY_AWARE)
    coord_fifo = HospitalCoordinator(strategy=AllocationStrategy.FIFO)

    patients = {
        "P001": {"id": "P001", "priority": "P3", "arrival_time": 1.0},
        "P002": {"id": "P002", "priority": "P1", "arrival_time": 3.0},
        "P003": {"id": "P003", "priority": "P2", "arrival_time": 2.0},
    }

    queue = ["P001", "P002", "P003"]

    # Priority-Aware: P1 (P002) -> P2 (P003) -> P3 (P001)
    prio_sorted = coord_prio.sort_waiting_queue(queue, patients)
    assert prio_sorted == ["P002", "P003", "P001"]

    # FIFO: P001 (1.0) -> P003 (2.0) -> P002 (3.0)
    fifo_sorted = coord_fifo.sort_waiting_queue(queue, patients)
    assert fifo_sorted == ["P001", "P003", "P002"]

    request_times = {
        "P001": {"priority": "P3", "arrival_time": 0.0, "doctor_request_time": 4.0},
        "P002": {"priority": "P1", "arrival_time": 1.0, "doctor_request_time": 2.0},
        "P003": {"priority": "P1", "arrival_time": 2.0, "doctor_request_time": 2.0},
    }
    assert coord_fifo.sort_waiting_queue(
        queue, request_times, request_time_field="doctor_request_time"
    ) == ["P002", "P003", "P001"]


def test_coordinator_doctor_conflict_and_waiting():
    coord = HospitalCoordinator()
    doctors = [
        {"id": "DOC-01", "name": "Dr. Vance", "specialty": "Trauma", "status": ResourceStatus.AVAILABLE.value, "workload_count": 0}
    ]
    p1 = {"id": "P001", "priority": "P1", "required_specialty": "Trauma", "arrival_time": 0.0, "workflow_state": WorkflowState.ADMITTED.value}
    p2 = {"id": "P002", "priority": "P2", "required_specialty": "Trauma", "arrival_time": 1.0, "workflow_state": WorkflowState.ADMITTED.value}

    env = {"doctors": doctors, "simulation_time": 2.0}

    # P1 gets doctor
    res1 = coord.request_doctor_allocation(p1, env)
    assert res1["status"] == "ALLOCATED"
    assert p1["workflow_state"] == WorkflowState.DOCTOR_ASSIGNED.value
    assert doctors[0]["status"] == ResourceStatus.BUSY.value

    # P2 requests same doctor -> conflict!
    res2 = coord.request_doctor_allocation(p2, env)
    assert res2["status"] == "WAITING"
    assert p2["workflow_state"] == WorkflowState.WAITING_FOR_DOCTOR.value
    assert "P002" in coord.waiting_doctors
    assert coord.conflict_count == 1


def test_failed_retry_preserves_original_waiting_age():
    coord = HospitalCoordinator()
    patient = {
        "id": "P090",
        "priority": "P4",
        "required_specialty": "Trauma",
        "workflow_state": WorkflowState.WAITING_FOR_DOCTOR.value,
        "arrival_time": 0.0,
    }
    coord.os_manager.register_patient_process(patient, current_time=0.0)
    coord.os_manager.transition_process("P090", ProcessState.READY, current_time=0.0)
    coord.os_manager.transition_process(
        "P090", ProcessState.BLOCKED, current_time=2.0, resource="Doctor (Trauma)"
    )
    coord.waiting_doctors.append("P090")

    result = coord.request_doctor_allocation(
        patient, {"doctors": [], "simulation_time": 10.0}
    )
    coord.os_manager.apply_aging(current_time=10.0)

    assert result["status"] == "WAITING"
    assert coord.os_manager.pcbs["P090"].last_state_change_time == 2.0
    assert coord.os_manager.pcbs["P090"].dynamic_priority == 3.6
