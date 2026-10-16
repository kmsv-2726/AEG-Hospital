"""
Baseline Comparison Evaluator: Compares FIFO vs Priority-Aware allocation strategies
under identical workloads, generating comparative metrics and evaluation charts data.
"""
import sys
import os
import json
import random
import copy

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.simulation.engine import SimulationEngine
from backend.app.simulation.scenarios import DEMO_PATIENTS, DEMO_RESOURCES
from backend.app.models.enums import AllocationStrategy, DoctorSpecialty, DiagnosticCategory, PriorityLevel


def generate_synthetic_workload(count: int, seed: int = 100):
    """Generate a reproducible synthetic emergency cohort of specified size."""
    random.seed(seed)
    patients = []
    specialties = [
        DoctorSpecialty.TRAUMA.value,
        DoctorSpecialty.CARDIOLOGY.value,
        DoctorSpecialty.GENERAL_MEDICINE.value,
    ]
    diagnostics = [None, DiagnosticCategory.XRAY.value, DiagnosticCategory.CT.value, DiagnosticCategory.BLOOD_TEST.value]
    categories = [
        ("Critical trauma", PriorityLevel.P1.value, DoctorSpecialty.TRAUMA.value, True, True),
        ("Critical cardiac", PriorityLevel.P1.value, DoctorSpecialty.CARDIOLOGY.value, True, True),
        ("High trauma", PriorityLevel.P2.value, DoctorSpecialty.TRAUMA.value, True, False),
        ("Moderate injury", PriorityLevel.P3.value, DoctorSpecialty.GENERAL_MEDICINE.value, True, False),
        ("Low severity", PriorityLevel.P4.value, DoctorSpecialty.GENERAL_MEDICINE.value, False, False),
    ]

    for i in range(count):
        cat_meta = random.choice(categories)
        p = {
            "id": f"P{i+1:03d}",
            "name": f"Synthetic Patient {i+1}",
            "age": random.randint(18, 85),
            "gender": random.choice(["Male", "Female"]),
            "condition_description": f"Simulated condition for emergency cohort {i+1}",
            "severity_category": cat_meta[0],
            "priority": cat_meta[1],
            "required_specialty": cat_meta[2],
            "requires_ambulance": cat_meta[3],
            "requires_icu": cat_meta[4],
            "required_diagnostic": random.choice(diagnostics),
            "arrival_time": round(i * 3.5, 1),
            "workflow_state": "REGISTERED",
        }
        patients.append(p)
    return patients


def evaluate_strategies(workload_sizes=(5, 20)):
    results = {}

    for size in workload_sizes:
        if size == 5:
            cohort = DEMO_PATIENTS
        else:
            cohort = generate_synthetic_workload(size, seed=42)

        results[f"workload_{size}"] = {}

        for strat in [AllocationStrategy.FIFO, AllocationStrategy.PRIORITY_AWARE]:
            engine = SimulationEngine(strategy=strat, seed=42)
            engine.load_scenario(cohort, DEMO_RESOURCES)
            metrics = engine.run_until_complete(max_steps=2000)

            # Separate wait times by priority
            p1_wait = []
            p4_wait = []
            for p in engine.patients.values():
                h_arr = p.get("hospital_arrival_time")
                doc_arr = p.get("doctor_assignment_time")
                if h_arr is not None and doc_arr is not None:
                    wait = max(0.0, doc_arr - h_arr)
                    if p.get("priority") == "P1":
                        p1_wait.append(wait)
                    elif p.get("priority") == "P4":
                        p4_wait.append(wait)

            avg_p1 = round(sum(p1_wait) / len(p1_wait), 2) if p1_wait else 0.0
            avg_p4 = round(sum(p4_wait) / len(p4_wait), 2) if p4_wait else 0.0

            results[f"workload_{size}"][strat.value] = {
                "strategy": strat.value,
                "total_patients": size,
                "completed_workflows": metrics.completed_workflows,
                "completion_rate": metrics.workflow_completion_rate,
                "resource_conflicts": metrics.resource_conflicts,
                "unresolved_requests": metrics.unresolved_requests,
                "average_waiting_time": metrics.average_waiting_time,
                "average_time_to_doctor": metrics.average_time_to_doctor,
                "p1_average_wait_to_doctor": avg_p1,
                "p4_average_wait_to_doctor": avg_p4,
                "ambulance_utilization": metrics.ambulance_utilization,
                "doctor_utilization": metrics.doctor_utilization,
                "diagnostic_utilization": metrics.diagnostic_utilization,
                "icu_utilization": metrics.icu_utilization,
                "simulation_duration": metrics.simulation_duration,
            }

    # Save to disk for frontend consumption
    output_path = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "simulation", "baseline_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("Baseline evaluation completed successfully!")
    print(f"Results exported to {output_path}")
    return results


if __name__ == "__main__":
    res = evaluate_strategies()
    print(json.dumps(res, indent=2))
