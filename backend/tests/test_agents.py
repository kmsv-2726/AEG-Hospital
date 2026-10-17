"""
Comprehensive unit tests for the five specialized agents.
"""
from backend.app.agents.triage_agent import TriageAgent
from backend.app.agents.ambulance_agent import AmbulanceAgent
from backend.app.agents.doctor_agent import DoctorAgent
from backend.app.agents.diagnostic_agent import DiagnosticAgent
from backend.app.agents.icu_agent import ICUAgent
from backend.app.models.enums import PriorityLevel, ResourceStatus, DoctorSpecialty, DiagnosticCategory


def test_triage_agent_rules():
    agent = TriageAgent()

    # P1 Critical
    env_p1 = {"patient": {"id": "P001", "severity_category": "Critical trauma", "condition_description": "Shock and hemorrhage"}}
    dec_p1 = agent.decide(agent.perceive(env_p1))
    assert dec_p1["priority"] == PriorityLevel.P1

    # P2 High
    env_p2 = {"patient": {"id": "P002", "severity_category": "High trauma", "condition_description": "Compound leg fracture"}}
    dec_p2 = agent.decide(agent.perceive(env_p2))
    assert dec_p2["priority"] == PriorityLevel.P2

    # P3 Moderate
    env_p3 = {"patient": {"id": "P003", "severity_category": "Moderate injury", "condition_description": "Sprained wrist and laceration"}}
    dec_p3 = agent.decide(agent.perceive(env_p3))
    assert dec_p3["priority"] == PriorityLevel.P3

    # P4 Low
    env_p4 = {"patient": {"id": "P004", "severity_category": "Low severity", "condition_description": "Mild fever and dehydration"}}
    dec_p4 = agent.decide(agent.perceive(env_p4))
    assert dec_p4["priority"] == PriorityLevel.P4


def test_ambulance_agent_allocation_and_conflict():
    agent = AmbulanceAgent()

    fleet = [
        {"id": "AMB-01", "call_sign": "Alpha", "status": ResourceStatus.AVAILABLE.value, "base_distance_km": 8.0, "equipment_capabilities": "BLS,ALS,Ventilator"},
        {"id": "AMB-02", "call_sign": "Bravo", "status": ResourceStatus.AVAILABLE.value, "base_distance_km": 2.0, "equipment_capabilities": "BLS"},
    ]

    # Test allocation
    env = {"patient": {"id": "P001", "priority": "P1", "requires_ambulance": True, "required_equipment": ["ALS"]}, "ambulances": fleet, "simulation_time": 5.0}
    decision = agent.decide(agent.perceive(env))
    assert decision["action"] == "ALLOCATE"
    assert decision["ambulance"]["id"] == "AMB-01"

    act_result = agent.act(decision, env)
    assert act_result["status"] == "ALLOCATED"
    assert fleet[0]["status"] == ResourceStatus.BUSY.value
    stale_result = agent.act(
        decision,
        {
            "patient": {"id": "P099", "priority": "P1", "requires_ambulance": True},
            "ambulances": fleet,
            "simulation_time": 5.0,
        },
    )
    assert stale_result["status"] == "WAITING"
    assert fleet[0]["current_patient_id"] == "P001"

    # Mark second busy to test conflict
    fleet[1]["status"] = ResourceStatus.BUSY.value
    env_busy = {"patient": {"id": "P002", "priority": "P1", "requires_ambulance": True}, "ambulances": fleet, "simulation_time": 6.0}
    decision_busy = agent.decide(agent.perceive(env_busy))
    assert decision_busy["action"] == "CONFLICT_WAITING"

    act_conflict = agent.act(decision_busy, env_busy)
    assert act_conflict["status"] == "WAITING"

    # Test release
    assert agent.release_ambulance(
        "AMB-01", fleet, simulation_time=15.0, expected_patient_id="P099"
    ) is None
    assert fleet[0]["current_patient_id"] == "P001"
    released = agent.release_ambulance("AMB-01", fleet, simulation_time=15.0)
    assert released is not None
    assert fleet[0]["status"] == ResourceStatus.AVAILABLE.value


def test_ambulance_selection_uses_urgency_bonus_and_explains_candidates():
    agent = AmbulanceAgent()
    fleet = [
        {
            "id": "AMB-NEAR",
            "status": ResourceStatus.AVAILABLE.value,
            "base_distance_km": 1.0,
            "equipment_capabilities": "BLS,ALS",
        },
        {
            "id": "AMB-VENT",
            "status": ResourceStatus.AVAILABLE.value,
            "base_distance_km": 3.0,
            "equipment_capabilities": "BLS,ALS,Ventilator",
        },
        {
            "id": "AMB-BUSY",
            "status": ResourceStatus.BUSY.value,
            "base_distance_km": 0.5,
            "equipment_capabilities": "BLS,ALS,Ventilator",
        },
    ]
    patient = {
        "id": "P-URGENT",
        "priority": "P1",
        "requires_ambulance": True,
        "required_equipment": ["ALS"],
    }
    decision = agent.decide(agent.perceive({"patient": patient, "ambulances": fleet}))

    assert decision["ambulance"]["id"] == "AMB-VENT"
    candidates = {candidate["resource_id"]: candidate for candidate in decision["candidates"]}
    assert candidates["AMB-VENT"]["score"] == 105.0
    assert candidates["AMB-VENT"]["rank"] == 1
    assert candidates["AMB-NEAR"]["score"] == 95.0
    assert candidates["AMB-BUSY"]["eligible"] is False
    assert candidates["AMB-BUSY"]["rejection_reasons"] == ["not available"]

    patient["priority"] = "P3"
    ordinary_decision = agent.decide(
        agent.perceive({"patient": patient, "ambulances": fleet})
    )
    assert ordinary_decision["ambulance"]["id"] == "AMB-NEAR"


def test_ambulance_stale_candidate_falls_back_and_ties_use_resource_id():
    agent = AmbulanceAgent()
    fleet = [
        {"id": "AMB-B", "status": "AVAILABLE", "base_distance_km": 2.0, "equipment_capabilities": "ALS,BLS"},
        {"id": "AMB-A", "status": "AVAILABLE", "base_distance_km": 2.0, "equipment_capabilities": "ALS,BLS"},
        {"id": "AMB-INCOMPATIBLE", "status": "AVAILABLE", "base_distance_km": 0.1, "equipment_capabilities": "BLS"},
    ]
    patient = {"id": "P-FIRST", "priority": "P2", "requires_ambulance": True, "required_equipment": ["ALS"]}
    decision = agent.decide(agent.perceive({"patient": patient, "ambulances": fleet}))
    assert decision["ambulance"]["id"] == "AMB-A"

    decision["ambulance"]["status"] = "BUSY"
    decision["ambulance"]["current_patient_id"] = "P-OTHER"
    fallback = agent.act(
        decision,
        {
            "patient": {**patient, "id": "P-SECOND"},
            "ambulances": fleet,
            "simulation_time": 1.0,
        },
    )
    assert fallback["status"] == "ALLOCATED"
    assert fallback["ambulance_id"] == "AMB-B"
    assert fleet[0]["current_patient_id"] == "P-SECOND"
    assert fleet[1]["current_patient_id"] == "P-OTHER"

    equipment_specific = agent.decide(agent.perceive({
        "patient": {"id": "P-THIRD", "priority": "P3", "requires_ambulance": True, "required_equipment": ["BLS"]},
        "ambulances": [
            {"id": "AMB-10", "status": "AVAILABLE", "base_distance_km": 4.0, "equipment_capabilities": "BLS"},
            {"id": "AMB-11", "status": "AVAILABLE", "base_distance_km": 1.0, "equipment_capabilities": "ALS,BLS"},
        ],
    }))
    assert equipment_specific["ambulance"]["id"] == "AMB-11"


def test_doctor_agent_specialty_and_workload():
    agent = DoctorAgent()

    doctors = [
        {"id": "DOC-01", "name": "Dr. Vance", "specialty": "Trauma", "status": ResourceStatus.AVAILABLE.value, "workload_count": 2},
        {"id": "DOC-02", "name": "Dr. Kim", "specialty": "Trauma", "status": ResourceStatus.AVAILABLE.value, "workload_count": 0},
        {"id": "DOC-03", "name": "Dr. Sarah", "specialty": "General Medicine", "status": ResourceStatus.AVAILABLE.value, "workload_count": 0},
    ]

    # Patient requires Trauma -> should pick Dr. Kim because workload is 0 vs 2
    env = {"patient": {"id": "P001", "required_specialty": "Trauma", "priority": "P1"}, "doctors": doctors, "simulation_time": 2.0}
    decision = agent.decide(agent.perceive(env))
    assert decision["action"] == "ALLOCATE"
    assert decision["doctor"]["id"] == "DOC-02"

    act_res = agent.act(decision, env)
    assert act_res["doctor_id"] == "DOC-02"
    assert doctors[1]["workload_count"] == 1
    assert doctors[1]["status"] == ResourceStatus.BUSY.value
    stale_result = agent.act(
        decision,
        {
            "patient": {"id": "P099", "required_specialty": "Trauma"},
            "doctors": doctors,
            "simulation_time": 2.0,
        },
    )
    assert stale_result["status"] == "ALLOCATED"
    assert stale_result["doctor_id"] == "DOC-01"
    assert doctors[1]["current_patient_id"] == "P001"
    assert doctors[0]["current_patient_id"] == "P099"

    # Test release doctor
    assert agent.release_doctor(
        "DOC-02", doctors, simulation_time=10.0, expected_patient_id="P099"
    ) is None
    assert doctors[1]["current_patient_id"] == "P001"
    agent.release_doctor("DOC-02", doctors, simulation_time=10.0)
    assert doctors[1]["status"] == ResourceStatus.AVAILABLE.value


def test_diagnostic_agent():
    agent = DiagnosticAgent()
    resources = [
        {"id": "DIAG-CT-01", "name": "CT-1", "category": "CT", "status": ResourceStatus.AVAILABLE.value, "queue_length": 0, "simulated_duration": 15.0},
        {"id": "DIAG-XRAY-01", "name": "X-Ray-1", "category": "X-Ray", "status": ResourceStatus.AVAILABLE.value, "queue_length": 0, "simulated_duration": 10.0},
    ]

    env = {"patient": {"id": "P001", "required_diagnostic": "CT"}, "diagnostic_resources": resources, "simulation_time": 0.0}
    decision = agent.decide(agent.perceive(env))
    assert decision["action"] == "ALLOCATE"
    assert decision["resource"]["id"] == "DIAG-CT-01"

    act_res = agent.act(decision, env)
    assert act_res["status"] == "ALLOCATED"
    assert resources[0]["status"] == ResourceStatus.BUSY.value
    stale_result = agent.act(
        decision,
        {
            "patient": {"id": "P099", "required_diagnostic": "CT"},
            "diagnostic_resources": resources,
            "simulation_time": 0.0,
        },
    )
    assert stale_result["status"] == "WAITING"
    assert resources[0]["current_patient_id"] == "P001"

    # Release
    assert agent.release_diagnostic(
        "DIAG-CT-01", resources, simulation_time=15.0, expected_patient_id="P099"
    ) is None
    assert resources[0]["current_patient_id"] == "P001"
    agent.release_diagnostic("DIAG-CT-01", resources, simulation_time=15.0)
    assert resources[0]["status"] == ResourceStatus.AVAILABLE.value


def test_icu_agent():
    agent = ICUAgent()
    beds = [
        {"id": "ICU-01", "unit_name": "Bay 1", "status": ResourceStatus.AVAILABLE.value, "has_ventilator": False},
        {"id": "ICU-02", "unit_name": "Bay 2", "status": ResourceStatus.AVAILABLE.value, "has_ventilator": True},
    ]

    # P1 patient should prefer ventilator bed (ICU-02)
    env = {"patient": {"id": "P001", "requires_icu": True, "priority": "P1"}, "icu_beds": beds, "simulation_time": 0.0}
    decision = agent.decide(agent.perceive(env))
    assert decision["action"] == "ALLOCATE"
    assert decision["bed"]["id"] == "ICU-02"

    act_res = agent.act(decision, env)
    assert act_res["status"] == "ALLOCATED"
    assert beds[1]["status"] == ResourceStatus.BUSY.value
    stale_result = agent.act(
        decision,
        {
            "patient": {"id": "P099", "requires_icu": True, "priority": "P1"},
            "icu_beds": beds,
            "simulation_time": 0.0,
        },
    )
    assert stale_result["status"] == "ALLOCATED"
    assert stale_result["icu_bed_id"] == "ICU-01"
    assert beds[1]["current_patient_id"] == "P001"
    assert beds[0]["current_patient_id"] == "P099"

    # Release
    assert agent.release_bed(
        "ICU-02", beds, simulation_time=30.0, expected_patient_id="P099"
    ) is None
    assert beds[1]["current_patient_id"] == "P001"
    agent.release_bed("ICU-02", beds, simulation_time=30.0)
    assert beds[1]["status"] == ResourceStatus.AVAILABLE.value
