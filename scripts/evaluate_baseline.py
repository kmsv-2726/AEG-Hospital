"""
Baseline Comparison Evaluator: Compares FIFO vs Priority-Aware allocation strategies
under identical workloads, generating comparative metrics and evaluation charts data.
"""
import sys
import os
import json
import random
import statistics
import hashlib
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.simulation.engine import SimulationEngine
from backend.app.simulation.scenarios import DEMO_RESOURCES
from backend.app.models.enums import AllocationStrategy, DoctorSpecialty, DiagnosticCategory, PriorityLevel


def generate_synthetic_workload(count: int, seed: int = 100):
    """Generate a reproducible synthetic emergency cohort of specified size."""
    rng = random.Random(seed)
    patients = []
    diagnostics = [None, DiagnosticCategory.XRAY.value, DiagnosticCategory.CT.value, DiagnosticCategory.BLOOD_TEST.value]
    categories = [
        ("Critical trauma", PriorityLevel.P1.value, DoctorSpecialty.TRAUMA.value, True, True),
        ("Critical cardiac", PriorityLevel.P1.value, DoctorSpecialty.CARDIOLOGY.value, True, True),
        ("High trauma", PriorityLevel.P2.value, DoctorSpecialty.TRAUMA.value, True, False),
        ("Moderate injury", PriorityLevel.P3.value, DoctorSpecialty.GENERAL_MEDICINE.value, True, False),
        ("Low severity", PriorityLevel.P4.value, DoctorSpecialty.GENERAL_MEDICINE.value, False, False),
    ]

    category_sequence = []
    while len(category_sequence) < count:
        category_cycle = categories.copy()
        rng.shuffle(category_cycle)
        category_sequence.extend(category_cycle)

    for i, cat_meta in enumerate(category_sequence[:count]):
        p = {
            "id": f"P{i+1:03d}",
            "name": f"Synthetic Patient {i+1}",
            "age": rng.randint(18, 85),
            "gender": rng.choice(["Male", "Female"]),
            "condition_description": f"Simulated condition for emergency cohort {i+1}",
            "severity_category": cat_meta[0],
            "priority": cat_meta[1],
            "required_specialty": cat_meta[2],
            "requires_ambulance": cat_meta[3],
            "requires_icu": cat_meta[4],
            "required_diagnostic": rng.choice(diagnostics),
            "arrival_time": round(i * 3.5, 1),
            "workflow_state": "REGISTERED",
        }
        patients.append(p)
    return patients


def _aggregate_runs(runs: List[Dict[str, object]], strategy: AllocationStrategy, seed_list: Sequence[int]):
    numeric_fields = (
        "completed_workflows",
        "completion_rate",
        "successful_resource_assignments",
        "delayed_patients",
        "resource_conflicts",
        "unresolved_requests",
        "average_waiting_time",
        "average_ambulance_wait",
        "average_ambulance_response_time",
        "average_time_to_doctor",
        "average_time_to_diagnostics",
        "average_time_to_icu",
        "p1_average_wait_to_doctor",
        "p2_average_wait_to_doctor",
        "p3_average_wait_to_doctor",
        "p4_average_wait_to_doctor",
        "ambulance_utilization",
        "doctor_utilization",
        "diagnostic_utilization",
        "icu_utilization",
        "simulation_duration",
    )
    summary: Dict[str, object] = {
        "strategy": strategy.value,
        "runs": len(runs),
        "seeds": list(seed_list),
        "total_patients": runs[0]["total_patients"] if runs else 0,
        "per_seed": runs,
        "standard_deviation": {},
    }
    deviations = summary["standard_deviation"]
    for field in numeric_fields:
        values = [run[field] for run in runs if run[field] is not None]
        summary[field] = round(statistics.mean(values), 2) if values else None
        deviations[field] = round(statistics.pstdev(values), 2) if len(values) > 1 else 0.0
    return summary


def evaluate_strategies(
    workload_sizes=(5, 20),
    seeds=(42, 43, 44, 45, 46),
    output_path: Optional[str] = None,
):
    results = {}

    for size in workload_sizes:
        results[f"workload_{size}"] = {}
        strategy_runs = {strategy: [] for strategy in (AllocationStrategy.FIFO, AllocationStrategy.PRIORITY_AWARE)}

        for seed in seeds:
            cohort = generate_synthetic_workload(size, seed=seed)
            workload_fingerprint = hashlib.sha256(
                json.dumps(cohort, sort_keys=True).encode("utf-8")
            ).hexdigest()
            resource_fingerprint = hashlib.sha256(
                json.dumps(DEMO_RESOURCES, sort_keys=True).encode("utf-8")
            ).hexdigest()
            for strategy in strategy_runs:
                engine = SimulationEngine(strategy=strategy, seed=seed)
                engine.load_scenario(cohort, DEMO_RESOURCES)
                metrics = engine.run_until_complete(max_steps=2000)

                priority_waits = {f"P{level}": [] for level in range(1, 5)}
                for patient in engine.patients.values():
                    hospital_arrival = patient.get("hospital_arrival_time")
                    doctor_assignment = patient.get("doctor_assignment_time")
                    if hospital_arrival is not None and doctor_assignment is not None:
                        wait = max(0.0, doctor_assignment - hospital_arrival)
                        priority_waits.setdefault(patient.get("priority"), []).append(wait)

                successful_assignments = sum(
                    patient.get(field) is not None
                    for patient in engine.patients.values()
                    for field in (
                        "assigned_ambulance_id",
                        "assigned_doctor_id",
                        "assigned_diagnostic_id",
                        "assigned_icu_bed_id",
                    )
                )
                delayed_patients = sum(
                    patient.get("workflow_state", "").startswith("WAITING_")
                    for patient in engine.patients.values()
                )

                strategy_runs[strategy].append({
                    "seed": seed,
                    "workload_fingerprint": workload_fingerprint,
                    "resource_fingerprint": resource_fingerprint,
                    "strategy": strategy.value,
                    "total_patients": size,
                    "completed_workflows": metrics.completed_workflows,
                    "completion_rate": metrics.workflow_completion_rate,
                    "successful_resource_assignments": successful_assignments,
                    "delayed_patients": delayed_patients,
                    "resource_conflicts": metrics.resource_conflicts,
                    "unresolved_requests": metrics.unresolved_requests,
                    "average_waiting_time": metrics.average_waiting_time,
                    "average_ambulance_wait": metrics.average_ambulance_wait,
                    "average_ambulance_response_time": metrics.average_ambulance_response_time,
                    "average_time_to_doctor": metrics.average_time_to_doctor,
                    "average_time_to_diagnostics": metrics.average_time_to_diagnostics,
                    "average_time_to_icu": metrics.average_time_to_icu,
                    **{
                        f"{priority.lower()}_average_wait_to_doctor": (
                            round(sum(waits) / len(waits), 2) if waits else None
                        )
                        for priority, waits in priority_waits.items()
                    },
                    "ambulance_utilization": metrics.ambulance_utilization,
                    "doctor_utilization": metrics.doctor_utilization,
                    "diagnostic_utilization": metrics.diagnostic_utilization,
                    "icu_utilization": metrics.icu_utilization,
                    "simulation_duration": metrics.simulation_duration,
                })

        for strategy, runs in strategy_runs.items():
            results[f"workload_{size}"][strategy.value] = _aggregate_runs(runs, strategy, seeds)

    # Save to disk for frontend consumption
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "..", "backend", "app", "simulation", "baseline_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("Baseline evaluation completed successfully!")
    print(f"Results exported to {output_path}")
    return results


if __name__ == "__main__":
    results = evaluate_strategies()
    for workload, strategies in results.items():
        for summary in strategies.values():
            print(
                f"{workload} {summary['strategy']}: "
                f"{summary['runs']} runs, "
                f"mean wait={summary['average_waiting_time']} min, "
                f"P1 doctor wait={summary['p1_average_wait_to_doctor']} min, "
                f"conflicts={summary['resource_conflicts']}, "
                f"completion={summary['completion_rate']}%"
            )
