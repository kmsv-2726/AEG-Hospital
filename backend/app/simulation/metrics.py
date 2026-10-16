"""
Metrics calculation engine for evaluation and baseline comparisons.
"""
from typing import Dict, Any, List, Optional
from backend.app.schemas.hospital_schemas import MetricsSummary


def calculate_simulation_metrics(
    patients: List[Dict[str, Any]],
    ambulances: List[Dict[str, Any]],
    doctors: List[Dict[str, Any]],
    diagnostic_resources: List[Dict[str, Any]],
    icu_beds: List[Dict[str, Any]],
    conflict_count: int,
    simulation_duration: float,
    strategy: str = "PRIORITY_AWARE",
) -> MetricsSummary:
    """
    Computes all academic metrics defined in Section 27 of the specification:
    1. Average waiting time across completed resource requests.
    2. Average ambulance response time (arrival at scene/hospital - emergency request time).
    3. Average time to doctor (doctor assignment time - hospital arrival time).
    4. Average time to diagnostics (diagnostic start time - diagnostic request time).
    5. Average time to ICU (ICU reservation time - ICU request time).
    6. Resource utilization % for ambulances, doctors, diagnostics, and ICU beds.
    7. Unresolved requests count.
    8. Resource conflicts count.
    9. Workflow completion rate.
    """
    total_patients = len(patients)
    completed_patients = [p for p in patients if p.get("workflow_state") in ("COMPLETED", "DISCHARGED")]
    completed_count = len(completed_patients)

    # 1. Ambulance Response Times
    # response_time = ambulance_arrival_time - emergency_request_time
    response_times = []
    for p in patients:
        if p.get("requires_ambulance") and p.get("hospital_arrival_time") is not None:
            # Emergency request time is arrival_time
            req_time = p.get("arrival_time", 0.0)
            arr_time = p.get("hospital_arrival_time")
            response_times.append(arr_time - req_time)

    avg_response_time = (sum(response_times) / len(response_times)) if response_times else None

    # 2. Time to Doctor
    # time_to_doctor = doctor_assignment_time - hospital_arrival_time
    doctor_times = []
    for p in patients:
        if p.get("doctor_assignment_time") is not None and p.get("hospital_arrival_time") is not None:
            diff = max(0.0, p["doctor_assignment_time"] - p["hospital_arrival_time"])
            doctor_times.append(diff)

    avg_time_to_doctor = (sum(doctor_times) / len(doctor_times)) if doctor_times else None

    # 3. Time to Diagnostics
    # time_to_diagnostics = diagnostic_start_time - diagnostic_request_time
    diagnostic_times = []
    for p in patients:
        if p.get("diagnostic_start_time") is not None and p.get("diagnostic_request_time") is not None:
            diff = max(0.0, p["diagnostic_start_time"] - p["diagnostic_request_time"])
            diagnostic_times.append(diff)

    avg_time_to_diagnostics = (sum(diagnostic_times) / len(diagnostic_times)) if diagnostic_times else None

    # 4. Time to ICU
    # time_to_ICU = ICU_reservation_time - ICU_request_time
    icu_times = []
    for p in patients:
        if p.get("requires_icu") and p.get("icu_reservation_time") is not None and p.get("icu_request_time") is not None:
            diff = max(0.0, p["icu_reservation_time"] - p["icu_request_time"])
            icu_times.append(diff)

    avg_time_to_icu = (sum(icu_times) / len(icu_times)) if icu_times else None

    # Aggregate Waiting Times (all queues combined)
    all_wait_times = doctor_times + diagnostic_times + icu_times
    avg_waiting_time = (sum(all_wait_times) / len(all_wait_times)) if all_wait_times else None

    # Resource Utilization %: busy_time / total_available_time * 100
    safe_sim_duration = max(simulation_duration, 1.0)

    # Ambulances
    total_amb_avail = len(ambulances) * safe_sim_duration
    total_amb_busy = sum(amb.get("total_busy_time", 0.0) for amb in ambulances)
    amb_util = min(100.0, round((total_amb_busy / total_amb_avail) * 100, 2)) if total_amb_avail > 0 else 0.0

    # Doctors
    total_doc_avail = len(doctors) * safe_sim_duration
    total_doc_busy = sum(doc.get("total_busy_time", 0.0) for doc in doctors)
    doc_util = min(100.0, round((total_doc_busy / total_doc_avail) * 100, 2)) if total_doc_avail > 0 else 0.0

    # Diagnostics
    total_diag_avail = len(diagnostic_resources) * safe_sim_duration
    total_diag_busy = sum(diag.get("total_busy_time", 0.0) for diag in diagnostic_resources)
    diag_util = min(100.0, round((total_diag_busy / total_diag_avail) * 100, 2)) if total_diag_avail > 0 else 0.0

    # ICU Beds
    total_icu_avail = len(icu_beds) * safe_sim_duration
    total_icu_busy = sum(bed.get("total_busy_time", 0.0) for bed in icu_beds)
    icu_util = min(100.0, round((total_icu_busy / total_icu_avail) * 100, 2)) if total_icu_avail > 0 else 0.0

    # Unresolved Requests
    unresolved_count = sum(
        1 for p in patients
        if p.get("workflow_state") in (
            "WAITING_FOR_AMBULANCE",
            "WAITING_FOR_DOCTOR",
            "WAITING_FOR_DIAGNOSTIC",
            "WAITING_FOR_ICU",
            "REGISTERED",
        )
    )

    # Completion Rate
    completion_rate = round((completed_count / total_patients * 100.0), 2) if total_patients > 0 else 0.0

    return MetricsSummary(
        average_waiting_time=round(avg_waiting_time, 2) if avg_waiting_time is not None else None,
        average_ambulance_response_time=round(avg_response_time, 2) if avg_response_time is not None else None,
        average_time_to_doctor=round(avg_time_to_doctor, 2) if avg_time_to_doctor is not None else None,
        average_time_to_diagnostics=round(avg_time_to_diagnostics, 2) if avg_time_to_diagnostics is not None else None,
        average_time_to_icu=round(avg_time_to_icu, 2) if avg_time_to_icu is not None else None,
        ambulance_utilization=amb_util,
        doctor_utilization=doc_util,
        diagnostic_utilization=diag_util,
        icu_utilization=icu_util,
        unresolved_requests=unresolved_count,
        resource_conflicts=conflict_count,
        workflow_completion_rate=completion_rate,
        total_patients=total_patients,
        completed_workflows=completed_count,
        strategy=strategy,
        simulation_duration=round(simulation_duration, 2),
        detailed_observations={
            "response_times": response_times,
            "doctor_times": doctor_times,
            "diagnostic_times": diagnostic_times,
            "icu_times": icu_times,
        },
    )
