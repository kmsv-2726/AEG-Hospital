"""Tests for reproducible paired FIFO and priority evaluation."""
import json

from scripts.evaluate_baseline import evaluate_strategies, generate_synthetic_workload


def test_synthetic_workloads_are_seeded_and_balanced():
    workload = generate_synthetic_workload(5, seed=31)

    assert workload == generate_synthetic_workload(5, seed=31)
    assert workload != generate_synthetic_workload(5, seed=32)
    assert {patient["severity_category"] for patient in workload} == {
        "Critical trauma",
        "Critical cardiac",
        "High trauma",
        "Moderate injury",
        "Low severity",
    }


def test_evaluation_replays_identical_workloads_and_persists_summaries(tmp_path):
    output_path = tmp_path / "paired_results.json"
    results = evaluate_strategies(
        workload_sizes=(5,),
        seeds=(31, 32),
        output_path=str(output_path),
    )

    cohort = results["workload_5"]
    fifo_runs = cohort["FIFO"]["per_seed"]
    priority_runs = cohort["PRIORITY_AWARE"]["per_seed"]
    assert cohort["FIFO"]["runs"] == cohort["PRIORITY_AWARE"]["runs"] == 2
    assert [run["seed"] for run in fifo_runs] == [run["seed"] for run in priority_runs]
    assert [run["workload_fingerprint"] for run in fifo_runs] == [
        run["workload_fingerprint"] for run in priority_runs
    ]
    assert [run["resource_fingerprint"] for run in fifo_runs] == [
        run["resource_fingerprint"] for run in priority_runs
    ]
    assert all(run["total_patients"] == 5 for run in fifo_runs + priority_runs)
    assert json.loads(output_path.read_text(encoding="utf-8")) == results