"""Non-interactive tests for terminal registration and rendering."""
from backend.app.cli import collect_patient, display_patient_result
from backend.app.cli import run_cli
from backend.app.services.simulation_service import sim_service


def test_collect_patient_reprompts_and_builds_valid_automatic_triage_case():
    answers = iter([
        "", "Ravi Kumar", "abc", "45", "Male", "Cardiac emergency",
        "Chest pain", "Sweating", "301", "120", "92", "oops", "150/95",
        "Auto", "y", "Cardiac Equipment, ALS", "Cardiology", "y", "CT",
        "y", "ventilator, monitoring", "",
    ])
    messages = []
    patient = collect_patient(
        existing_ids={"CLI-001"},
        current_time=5.0,
        input_fn=lambda _prompt: next(answers),
        output_fn=messages.append,
    )

    assert patient.id == "CLI-002"
    assert patient.age == 45
    assert patient.emergency_type == "Cardiac emergency"
    assert patient.heart_rate == 120
    assert patient.oxygen_saturation == 92
    assert patient.blood_pressure == "150/95"
    assert patient.triage_mode == "AUTO"
    assert patient.required_equipment == ["Cardiac Equipment", "ALS"]
    assert patient.requires_ventilator is True
    assert patient.arrival_time == 5.0
    assert any("valid number" in message for message in messages)
    assert any("systolic/diastolic" in message for message in messages)


def test_display_patient_result_uses_actual_trace_and_assignments():
    output = []
    display_patient_result({
        "id": "CLI-004",
        "name": "Synthetic Patient",
        "age": 45,
        "priority": "P1",
        "workflow_state": "WAITING_FOR_DOCTOR",
        "triage_reason": "Unmatched input; human review required.",
        "decision_trace": [{
            "sequence": 1,
            "agent": "TriageAgent",
            "action": "CLASSIFY",
            "status": "REVIEW_REQUIRED",
            "description": "Unmatched input; human review required.",
            "details": {"priority": "P3"},
        }],
    }, output.append)

    text = "\n".join(output)
    assert "WAITING_FOR_DOCTOR" in text
    assert "REVIEW_REQUIRED" in text
    assert "Ambulance: not assigned" in text


def test_cli_registers_patient_and_keeps_shared_resource_state():
    sim_service.initialize()
    sim_service.reset_simulation()
    answers = iter([
        "1", "CLI Patient", "31", "Unknown", "Walk-in", "Mild headache", "",
        "", "", "", "Low severity", "n", "", "General Medicine", "n", "n", "",
        "2", "3", "7",
    ])
    output = []

    run_cli(sim_service, input_fn=lambda _prompt: next(answers), output_fn=output.append)

    patient = sim_service.engine.patients["CLI-001"]
    assert patient["workflow_state"] in {"DOCTOR_ASSIGNED", "TREATMENT_SIMULATED", "COMPLETED", "DISCHARGED"}
    assert patient["decision_trace"]
    assert any("Ambulance" in line for line in output)
    assert any("Decision trace saved successfully" in line for line in output)