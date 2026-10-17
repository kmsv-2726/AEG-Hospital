"""
Tests for metrics calculation logic.
"""
from backend.app.simulation.metrics import calculate_simulation_metrics


def test_metrics_empty_observations():
    # If no patients arrived, waiting time must be None (not 0)
    metrics = calculate_simulation_metrics(
        patients=[],
        ambulances=[],
        doctors=[],
        diagnostic_resources=[],
        icu_beds=[],
        conflict_count=0,
        simulation_duration=0.0,
    )
    assert metrics.average_waiting_time is None
    assert metrics.average_ambulance_response_time is None
    assert metrics.workflow_completion_rate == 0.0
    assert metrics.total_patients == 0


def test_metrics_calculation_accuracy():
    patients = [
        {
            "id": "P001",
            "workflow_state": "COMPLETED",
            "requires_ambulance": True,
            "arrival_time": 0.0,
            "ambulance_dispatch_time": 2.0,
            "hospital_arrival_time": 6.0,
            "doctor_request_time": 6.0,
            "doctor_assignment_time": 10.0,
            "diagnostic_request_time": 10.0,
            "diagnostic_start_time": 12.0,
            "requires_icu": True,
            "icu_request_time": 15.0,
            "icu_reservation_time": 17.0,
        }
    ]
    ambulances = [{"id": "AMB-01", "total_busy_time": 6.0}]
    doctors = [{"id": "DOC-01", "total_busy_time": 10.0}]
    diagnostics = [{"id": "DIAG-01", "total_busy_time": 5.0}]
    icu_beds = [{"id": "ICU-01", "total_busy_time": 15.0}]

    metrics = calculate_simulation_metrics(
        patients=patients,
        ambulances=ambulances,
        doctors=doctors,
        diagnostic_resources=diagnostics,
        icu_beds=icu_beds,
        conflict_count=1,
        simulation_duration=50.0,
    )

    assert metrics.total_patients == 1
    assert metrics.completed_workflows == 1
    assert metrics.workflow_completion_rate == 100.0
    assert metrics.average_ambulance_response_time == 6.0
    assert metrics.average_ambulance_wait == 2.0
    assert metrics.average_time_to_doctor == 4.0
    assert metrics.average_time_to_diagnostics == 2.0
    assert metrics.average_time_to_icu == 2.0
    assert metrics.average_waiting_time == 2.5
    assert metrics.resource_conflicts == 1
