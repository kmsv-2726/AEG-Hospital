"""
FastAPI REST API integration tests using FastAPI TestClient.
"""
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.simulation_service import sim_service

# Initialize service for test runner
sim_service.initialize()
client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_get_patients():
    response = client.get("/api/patients")
    assert response.status_code == 200
    patients = response.json()
    assert isinstance(patients, list)
    assert len(patients) >= 5


def test_api_get_resources():
    response = client.get("/api/resources")
    assert response.status_code == 200
    data = response.json()
    assert "ambulances" in data
    assert "doctors" in data
    assert "diagnostic_resources" in data
    assert "icu_beds" in data
    assert "counts" in data
    assert len(data["ambulances"]) == 3
    assert len(data["doctors"]) == 4


def test_api_get_agents():
    response = client.get("/api/agents")
    assert response.status_code == 200
    agents = response.json()
    assert len(agents) == 6  # 1 Coordinator + 5 specialized agents
    names = [a["name"] for a in agents]
    assert "HospitalCoordinator" in names
    assert "TriageAgent" in names
    assert "AmbulanceAgent" in names
    assert "DoctorAgent" in names
    assert "DiagnosticAgent" in names
    assert "ICUAgent" in names


def test_api_simulation_lifecycle():
    # 1. Reset simulation
    res_reset = client.post("/api/simulation/reset", json={"preserve_scenario": True})
    assert res_reset.status_code == 200

    # 2. Start simulation
    res_start = client.post("/api/simulation/start", json={"strategy": "PRIORITY_AWARE"})
    assert res_start.status_code == 200
    metrics = res_start.json()
    assert metrics["completed_workflows"] >= 5
    assert metrics["workflow_completion_rate"] == 100.0

    # 3. Check events
    res_events = client.get("/api/events")
    assert res_events.status_code == 200
    events = res_events.json()
    assert len(events) > 0

    # 4. Check metrics endpoint
    res_metrics = client.get("/api/metrics")
    assert res_metrics.status_code == 200
    assert res_metrics.json()["strategy"] == "PRIORITY_AWARE"


def test_api_post_emergency():
    emergency_payload = {
        "id": "P999",
        "name": "Emergency Patient X",
        "age": 45,
        "gender": "Female",
        "condition_description": "Sudden onset chest pain with diaphoresis",
        "severity_category": "Critical cardiac",
        "priority": "P1",
        "requires_ambulance": True,
        "required_specialty": "Cardiology",
        "required_diagnostic": None,
        "requires_icu": True,
        "arrival_time": 10.0,
    }
    response = client.post("/api/emergency", json=emergency_payload)
    assert response.status_code == 201
    created = response.json()
    assert created["id"] == "P999"
    assert created["priority"] == "P1"


def test_api_get_baseline():
    response = client.get("/api/baseline")
    assert response.status_code == 200
    data = response.json()
    assert "workload_5" in data
    assert "workload_20" in data
    assert "FIFO" in data["workload_20"]
    assert "PRIORITY_AWARE" in data["workload_20"]
