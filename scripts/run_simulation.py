"""
Standalone CLI demonstration script for the Smart Hospital Multi-Agent Emergency Response System.
Executes the deterministic emergency demonstration scenario and displays agent actions,
conflict resolution, and performance evaluation metrics.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.simulation.engine import SimulationEngine
from backend.app.simulation.scenarios import DEMO_PATIENTS, DEMO_RESOURCES
from backend.app.models.enums import AllocationStrategy


def run_demonstration(strategy: AllocationStrategy = AllocationStrategy.PRIORITY_AWARE):
    print("=" * 75)
    print("SMART HOSPITAL EMERGENCY RESPONSE SYSTEM USING MULTI-AGENT AI")
    print(f"Executing Deterministic Academic Simulation [Strategy: {strategy.value}]")
    print("=" * 75)

    engine = SimulationEngine(strategy=strategy, seed=42)
    engine.load_scenario(DEMO_PATIENTS, DEMO_RESOURCES)

    print(f"\n[INIT] Scenario loaded with {len(DEMO_PATIENTS)} emergency patients:")
    for p in DEMO_PATIENTS:
        print(f"  • {p['id']} - {p['name']} ({p['severity_category']}): Priority {p['priority']}, Requires: {p['required_specialty']}, X-Ray: {p['required_diagnostic'] or 'None'}, ICU: {p['requires_icu']}")

    print("\n[SIMULATION] Executing event-driven multi-agent simulation...")
    metrics = engine.run_until_complete(max_steps=500)

    print("\n" + "-" * 75)
    print("CHRONOLOGICAL AGENT EVENT TIMELINE (FIRST 15 EVENTS):")
    print("-" * 75)
    for evt in engine.all_events[:15]:
        conflict_flag = " [!] CONFLICT DETECTED" if evt.is_conflict else ""
        print(f"[{evt.simulation_time:5.1f}m] [{evt.agent:20s}] {evt.event_type:22s} -> {evt.description}{conflict_flag}")

    print("\n" + "=" * 75)
    print("FINAL PERFORMANCE EVALUATION METRICS:")
    print("=" * 75)
    print(f"• Total Patients:                   {metrics.total_patients}")
    print(f"• Completed Workflows:              {metrics.completed_workflows} ({metrics.workflow_completion_rate}%)")
    print(f"• Total Resource Conflicts Logged:  {metrics.resource_conflicts}")
    print(f"• Unresolved Requests:              {metrics.unresolved_requests}")
    print(f"• Average Waiting Time:             {metrics.average_waiting_time} mins")
    print(f"• Average Ambulance Response Time:  {metrics.average_ambulance_response_time} mins")
    print(f"• Average Time to Doctor:           {metrics.average_time_to_doctor} mins")
    print(f"• Average Time to Diagnostics:      {metrics.average_time_to_diagnostics} mins")
    print(f"• Average Time to ICU:              {metrics.average_time_to_icu} mins")
    print(f"• Ambulance Fleet Utilization:      {metrics.ambulance_utilization}%")
    print(f"• Doctor Workload Utilization:      {metrics.doctor_utilization}%")
    print(f"• Diagnostic Resource Utilization:  {metrics.diagnostic_utilization}%")
    print(f"• ICU Bed Utilization:              {metrics.icu_utilization}%")
    print(f"• Total Simulation Elapsed Time:    {metrics.simulation_duration} mins")
    print("=" * 75)
    print("Academic simulation executed successfully with ZERO external AI API keys.\n")
    return metrics


if __name__ == "__main__":
    run_demonstration()
