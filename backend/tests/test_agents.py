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
        {"id": "AMB-01", "call_sign": "Alpha", "status": ResourceStatus.AVAILABLE.value, "base_distance_km": 3.0, "equipment_capabilities": "BLS,ALS,Ventilator"},
        {"id": "AMB-02", "call_sign": "Bravo", "status": ResourceStatus.AVAILABLE.value, "base_distance_km": 6.0, "equipment_capabilities": "BLS"},
    ]

    # Test allocation
    env = {"patient": {"id": "P001", "priority": "P1", "requires_ambulance": True}, "ambulances": fleet, "simulation_time": 5.0}
    decision = agent.decide(agent.perceive(env))
    assert decision["action"] == "ALLOCATE"
    assert decision["ambulance"]["id"] == "AMB-01"

    act_result = agent.act(decision, env)
    assert act_result["status"] == "ALLOCATED"
    assert fleet[0]["status"] == ResourceStatus.BUSY.value

    # Mark second busy to test conflict
    fleet[1]["status"] = ResourceStatus.BUSY.value
    env_busy = {"patient": {"id": "P002", "priority": "P1", "requires_ambulance": True}, "ambulances": fleet, "simulation_time": 6.0}
    decision_busy = agent.decide(agent.perceive(env_busy))
    assert decision_busy["action"] == "CONFLICT_WAITING"

    act_conflict = agent.act(decision_busy, env_busy)
    assert act_conflict["status"] == "WAITING"

    # Test release
    released = agent.release_ambulance("AMB-01", fleet, simulation_time=15.0)
    assert released is not None
    assert fleet[0]["status"] == ResourceStatus.AVAILABLE.value


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

    # Test release doctor
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

    # Release
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

    # Release
    agent.release_bed("ICU-02", beds, simulation_time=30.0)
    assert beds[1]["status"] == ResourceStatus.AVAILABLE.value
