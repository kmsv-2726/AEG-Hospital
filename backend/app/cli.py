"""Interactive terminal client for the shared hospital simulation service."""
from __future__ import annotations

import json
import re
from typing import Callable, Iterable, Optional

from backend.app.models.enums import DiagnosticCategory, DoctorSpecialty, PriorityLevel
from backend.app.schemas.hospital_schemas import PatientCreate
from backend.app.services.simulation_service import SimulationService
from scripts.evaluate_baseline import evaluate_strategies

InputFunction = Callable[[str], str]
OutputFunction = Callable[[str], None]


def _ask_text(
    prompt: str,
    input_fn: InputFunction,
    output_fn: OutputFunction,
    *,
    required: bool = False,
    default: Optional[str] = None,
) -> Optional[str]:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        value = input_fn(f"{prompt}{suffix}: ").strip()
        if not value and default is not None:
            return default
        if value or not required:
            return value or None
        output_fn("A value is required.")


def _ask_number(
    prompt: str,
    input_fn: InputFunction,
    output_fn: OutputFunction,
    *,
    minimum: float,
    maximum: float,
    default: Optional[float] = None,
    integer: bool = False,
    optional: bool = False,
):
    while True:
        suffix = f" [{default:g}]" if default is not None else ""
        raw_value = input_fn(f"{prompt}{suffix}: ").strip()
        if not raw_value:
            if default is not None:
                return int(default) if integer else default
            if optional:
                return None
            output_fn("A value is required.")
            continue
        try:
            value = int(raw_value) if integer else float(raw_value)
        except ValueError:
            output_fn("Enter a valid number.")
            continue
        if not minimum <= value <= maximum:
            output_fn(f"Enter a value from {minimum:g} to {maximum:g}.")
            continue
        return value


def _ask_yes_no(prompt: str, input_fn: InputFunction, output_fn: OutputFunction, default: str = "n") -> bool:
    while True:
        answer = input_fn(f"{prompt} [y/n, default {default}]: ").strip().casefold()
        if not answer:
            answer = default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        output_fn("Enter y or n.")


def _ask_blood_pressure(
    input_fn: InputFunction, output_fn: OutputFunction
) -> Optional[str]:
    while True:
        value = _ask_text("Blood pressure (optional, e.g. 120/80)", input_fn, output_fn)
        if value is None:
            return None
        match = re.fullmatch(r"(\d{2,3})\s*/\s*(\d{2,3})", value)
        if match and 40 <= int(match.group(1)) <= 300 and 20 <= int(match.group(2)) <= 200:
            return f"{int(match.group(1))}/{int(match.group(2))}"
        output_fn("Enter systolic/diastolic pressure (for example, 120/80), or leave blank.")


def _next_cli_patient_id(existing_ids: Iterable[str]) -> str:
    used_ids = set(existing_ids)
    index = 1
    while f"CLI-{index:03d}" in used_ids:
        index += 1
    return f"CLI-{index:03d}"


def collect_patient(
    existing_ids: Iterable[str],
    current_time: float,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> PatientCreate:
    """Prompt and validate synthetic patient input, returning the API schema."""
    name = _ask_text("Patient name", input_fn, output_fn, required=True)
    age = _ask_number("Patient age", input_fn, output_fn, minimum=0, maximum=120, integer=True)
    gender = _ask_text("Gender (optional)", input_fn, output_fn, default="Unknown")
    emergency_type = _ask_text("Emergency type (optional)", input_fn, output_fn)
    chief_complaint = _ask_text("Chief complaint (optional)", input_fn, output_fn)
    symptoms = _ask_text("Symptoms (optional)", input_fn, output_fn)
    heart_rate = _ask_number("Heart rate (optional)", input_fn, output_fn, minimum=0, maximum=300, integer=True, optional=True)
    oxygen_saturation = _ask_number("Oxygen saturation % (optional)", input_fn, output_fn, minimum=0, maximum=100, optional=True)
    blood_pressure = _ask_blood_pressure(input_fn, output_fn)

    triage_input = _ask_text(
        "Severity category, P1-P4, or Auto",
        input_fn,
        output_fn,
        default="Auto",
    )
    normalized_triage = (triage_input or "Auto").strip()
    try:
        provided_priority = PriorityLevel(normalized_triage.upper())
    except ValueError:
        provided_priority = None

    triage_mode = "PROVIDED" if provided_priority else "AUTO"
    priority = provided_priority or PriorityLevel.P3
    if provided_priority:
        severity_category = "Operator-provided priority"
    elif normalized_triage.casefold() == "auto":
        severity_category = "Unclassified"
    else:
        severity_category = normalized_triage

    requires_ambulance = _ask_yes_no("Requires ambulance dispatch?", input_fn, output_fn, "y")
    required_equipment_text = _ask_text(
        "Required ambulance capabilities (comma-separated, optional)", input_fn, output_fn
    )
    required_equipment = [
        item.strip() for item in (required_equipment_text or "").split(",") if item.strip()
    ]

    specialties = [item.value for item in DoctorSpecialty]
    output_fn("Doctor specialties: " + ", ".join(specialties))
    specialty = _ask_text(
        "Required doctor specialty", input_fn, output_fn, default=DoctorSpecialty.GENERAL_MEDICINE.value
    )
    while specialty not in specialties:
        output_fn("Select a listed specialty exactly.")
        specialty = _ask_text("Required doctor specialty", input_fn, output_fn, required=True)

    diagnostic = None
    if _ask_yes_no("Requires a diagnostic test?", input_fn, output_fn, "n"):
        diagnostics = [item.value for item in DiagnosticCategory]
        output_fn("Diagnostic tests: " + ", ".join(diagnostics))
        diagnostic = _ask_text("Required diagnostic test", input_fn, output_fn, required=True)
        while diagnostic not in diagnostics:
            output_fn("Select a listed diagnostic test exactly.")
            diagnostic = _ask_text("Required diagnostic test", input_fn, output_fn, required=True)

    requires_icu = _ask_yes_no("Requires ICU care?", input_fn, output_fn, "n")
    required_icu_equipment = []
    requires_ventilator = False
    if requires_icu:
        equipment = _ask_text(
            "Required ICU equipment (ventilator, monitoring; comma-separated, optional)",
            input_fn,
            output_fn,
        )
        required_icu_equipment = [
            item.strip().casefold()
            for item in (equipment or "").split(",")
            if item.strip()
        ]
        requires_ventilator = "ventilator" in required_icu_equipment

    arrival_time = _ask_number(
        "Simulated arrival time in minutes",
        input_fn,
        output_fn,
        minimum=current_time,
        maximum=1_000_000,
        default=current_time,
    )
    summary = "; ".join(
        item for item in (emergency_type, chief_complaint, symptoms) if item
    ) or "Synthetic emergency; details not supplied"

    return PatientCreate(
        id=_next_cli_patient_id(existing_ids),
        name=name,
        age=age,
        gender=gender or "Unknown",
        condition_description=summary,
        emergency_type=emergency_type,
        chief_complaint=chief_complaint,
        symptoms=symptoms,
        heart_rate=heart_rate,
        oxygen_saturation=oxygen_saturation,
        blood_pressure=blood_pressure,
        severity_category=severity_category,
        priority=priority,
        triage_mode=triage_mode,
        requires_ambulance=requires_ambulance,
        required_equipment=required_equipment,
        required_specialty=specialty,
        required_diagnostic=diagnostic,
        requires_icu=requires_icu,
        required_icu_equipment=required_icu_equipment,
        requires_ventilator=requires_ventilator,
        arrival_time=arrival_time,
    )


def display_patient_result(patient: dict, output_fn: OutputFunction = print) -> None:
    """Print actual patient assignments and recorded agent decisions."""
    output_fn(f"\nPatient ID: {patient['id']}")
    output_fn(f"Name: {patient['name']}")
    output_fn(f"Age: {patient['age']}")
    output_fn(
        "Emergency: "
        + str(
            patient.get("emergency_type")
            or patient.get("chief_complaint")
            or patient.get("condition_description", "Not provided")
        )
    )
    output_fn(f"Triage: {patient.get('priority')} - {patient.get('triage_reason', 'see recorded triage decision')}")
    output_fn("\nORCHESTRATION TRACE")
    for entry in patient.get("decision_trace", []):
        output_fn(
            f"[{entry.get('sequence')}] {entry.get('agent')} | {entry.get('action')} | "
            f"{entry.get('status')} | {entry.get('description')}"
        )
        candidates = entry.get("details", {}).get("candidates", [])
        for candidate in candidates:
            score = candidate.get("score")
            score_text = f" score={score}" if score is not None else ""
            reasons = ", ".join(candidate.get("rejection_reasons", []))
            output_fn(
                f"    {candidate.get('rank', '-')}. {candidate.get('resource_id')}"
                f" eligible={candidate.get('eligible')}{score_text}"
                f"{'; ' + reasons if reasons else ''}"
            )
    output_fn("\nFINAL RESULT")
    output_fn(f"Patient status: {patient.get('workflow_state')}")
    output_fn(f"Ambulance: {patient.get('assigned_ambulance_id') or 'not assigned'}")
    output_fn(f"Doctor: {patient.get('assigned_doctor_id') or 'not assigned'}")
    output_fn(f"Diagnostics: {patient.get('assigned_diagnostic_id') or 'not required/not assigned'}")
    output_fn(f"ICU bed: {patient.get('assigned_icu_bed_id') or 'not required/not assigned'}")
    output_fn(f"Decision trace entries: {len(patient.get('decision_trace', []))}")


def _display_resources(service: SimulationService, output_fn: OutputFunction) -> None:
    resources = service.get_resources()
    for group in ("ambulances", "doctors", "diagnostic_resources", "icu_beds"):
        output_fn(f"\n{group.replace('_', ' ').title()}")
        for item in resources[group]:
            output_fn(
                f"  {item['id']}: {item['status']}"
                f" owner={item.get('current_patient_id') or '-'}"
                f" capabilities={item.get('equipment_capabilities', item.get('category', item.get('specialty', '')))}"
            )


def _display_patients(service: SimulationService, output_fn: OutputFunction) -> None:
    patients = sorted(service.get_patients(), key=lambda patient: (patient.get("arrival_time", 0), patient["id"]))
    if not patients:
        output_fn("No patients are registered.")
        return
    for patient in patients:
        output_fn(
            f"{patient['id']} | {patient['priority']} | {patient['workflow_state']} | "
            f"{patient['name']} | ambulance={patient.get('assigned_ambulance_id') or '-'} "
            f"doctor={patient.get('assigned_doctor_id') or '-'}"
        )


def run_cli(
    service: Optional[SimulationService] = None,
    input_fn: InputFunction = input,
    output_fn: OutputFunction = print,
) -> None:
    service = service or SimulationService()
    if not getattr(service, "initialized", False):
        service.initialize()

    while True:
        output_fn(
            "\nAEG Hospital Emergency Simulator\n"
            "1. Register a new emergency\n"
            "2. View available hospital resources\n"
            "3. View active patients and assignments\n"
            "4. View latest orchestration decision trace\n"
            "5. Run FIFO vs intelligent-allocation evaluation\n"
            "6. Reset simulation to clean demo state\n"
            "7. Exit"
        )
        choice = input_fn("Select an option: ").strip()
        if choice == "1":
            patient = collect_patient(
                service.engine.patients.keys(),
                service.engine.current_time,
                input_fn,
                output_fn,
            )
            result = service.add_emergency_patient(patient)
            display_patient_result(result, output_fn)
            output_fn("Decision trace saved successfully.")
        elif choice == "2":
            _display_resources(service, output_fn)
        elif choice == "3":
            _display_patients(service, output_fn)
        elif choice == "4":
            patients = list(service.engine.patients.values())
            patient = next((item for item in reversed(patients) if item.get("decision_trace")), None)
            if patient:
                display_patient_result(patient, output_fn)
            else:
                output_fn("No orchestration trace is available yet.")
        elif choice == "5":
            results = evaluate_strategies()
            for cohort, strategies in results.items():
                output_fn(f"\n{cohort}")
                for policy, summary in strategies.items():
                    output_fn(
                        f"  {policy}: runs={summary['runs']} "
                        f"mean_wait={summary['average_waiting_time']} "
                        f"P1_doctor_wait={summary['p1_average_wait_to_doctor']} "
                        f"conflicts={summary['resource_conflicts']} "
                        f"completion={summary['completion_rate']}%"
                    )
        elif choice == "6":
            if _ask_yes_no("Reset all simulated patients, resources and traces?", input_fn, output_fn, "n"):
                service.reset_simulation()
                output_fn("Simulation reset to the standard synthetic demonstration scenario.")
        elif choice == "7":
            output_fn("Simulation session ended.")
            return
        else:
            output_fn("Select a menu option from 1 to 7.")


def main() -> None:
    try:
        run_cli()
    except (KeyboardInterrupt, EOFError):
        print("\nSimulation session ended.")


if __name__ == "__main__":
    main()
