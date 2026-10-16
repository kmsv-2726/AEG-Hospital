"""
Automated unit and integration tests for OS Resource Management,
Autonomous Multi-Agent Message Bus, and Patient Orchestration Transcripts.
"""
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.simulation_service import sim_service
from backend.app.models.os_primitives import HospitalOSManager, ProcessState, CountingSemaphore, ResourceMutex
from backend.app.coordinator.message_bus import AgentMessageBus
from backend.app.models.enums import MessageType

client = TestClient(app)


def test_agent_message_bus():
    """Verify autonomous agent message dispatching and logging."""
    bus = AgentMessageBus()
    received = []

    def dummy_handler(msg):
        received.append(msg)
        return None

    bus.register_agent("AmbulanceAgent", dummy_handler)

    msg = bus.send_message(
        sender="HospitalCoordinator",
        receiver="AmbulanceAgent",
        message_type=MessageType.AMBULANCE_REQUEST,
        patient_id="P100",
        simulation_time=2.5,
        payload={"priority": "P1"},
    )

    assert msg.message_id.startswith("MSG-")
    assert len(bus.message_history) == 1
    assert len(bus.agent_inboxes["AmbulanceAgent"]) == 1

    bus.dispatch(msg)
    assert len(received) == 1
    assert received[0].patient_id == "P100"


def test_os_primitives_semaphore_and_mutex():
    """Verify counting semaphores and mutex locks."""
    # Counting Semaphore (e.g. ICU beds, capacity 2)
    sem = CountingSemaphore("Test_ICU_Sem", capacity=2)
    assert sem.acquire("P1", "BED-01") is True
    assert sem.acquire("P2", "BED-02") is True
    # Third request blocked
    assert sem.acquire("P3", "BED-03") is False
    assert len(sem.wait_queue) == 1
    assert sem.wait_queue[0] == "P3"

    # Release permit
    released = sem.release("P1")
    assert released == "BED-01"
    assert sem.value == 1

    # Resource Mutex (e.g. Trauma Doctor)
    mutex = ResourceMutex("DOC-01", "Doctor", "Dr. Vance")
    assert mutex.acquire("P1", current_time=0.0) is True
    assert mutex.acquire("P2", current_time=1.0) is False
    assert len(mutex.wait_queue) == 1

    assert mutex.release("P1", current_time=5.0) is True
    assert mutex.is_locked is False
    assert mutex.total_lock_time == 5.0


def test_os_manager_pcb_and_aging():
    """Verify Patient Process Control Block and dynamic priority aging."""
    mgr = HospitalOSManager()
    p_data = {"id": "P300", "name": "Patient Starvation Test", "priority": "P4"}
    pcb = mgr.register_patient_process(p_data, current_time=0.0)
    assert pcb.state == ProcessState.NEW
    assert pcb.numeric_priority == 4
    assert pcb.dynamic_priority == 4.0

    mgr.transition_process("P300", ProcessState.READY, current_time=0.0)
    assert "P300" in mgr.ready_queue

    # Advance time to 40 minutes -> aging should improve dynamic priority
    mgr.apply_aging(current_time=40.0)
    assert pcb.dynamic_priority < 4.0  # Priority aged (improved)


def test_api_os_status_and_orchestration():
    """Verify REST endpoints for OS metrics and patient AI orchestration."""
    # 1. Check OS status endpoint
    res_os = client.get("/api/os/status")
    assert res_os.status_code == 200
    os_data = res_os.json()
    assert "icu_semaphore" in os_data
    assert "ambulance_semaphore" in os_data
    assert "doctor_mutexes" in os_data
    assert "diagnostic_mutexes" in os_data
    assert "process_counts" in os_data

    # 2. Register emergency patient and inspect orchestration
    emergency_payload = {
        "id": "P777",
        "name": "Alex Mercer",
        "age": 32,
        "gender": "Male",
        "condition_description": "Multiple fractures, trauma priority",
        "severity_category": "High trauma",
        "priority": "P2",
        "requires_ambulance": True,
        "required_specialty": "Trauma",
        "required_diagnostic": "X-Ray",
        "requires_icu": False,
        "arrival_time": 5.0,
    }
    res_em = client.post("/api/emergency", json=emergency_payload)
    assert res_em.status_code == 201

    # 3. Check orchestration endpoint
    res_orch = client.get("/api/patients/P777/orchestration")
    assert res_orch.status_code == 200
    orch_data = res_orch.json()
    assert orch_data["patient"]["id"] == "P777"
    assert "orchestration_steps" in orch_data
    assert len(orch_data["orchestration_steps"]) >= 3
    assert "agent_messages" in orch_data
    assert "pcb" in orch_data
    assert orch_data["pcb"]["pid"] == "P777"

    # 4. Check agents endpoint reflects active/message data
    res_agents = client.get("/api/agents")
    assert res_agents.status_code == 200
    agents_list = res_agents.json()
    assert len(agents_list) == 6
    doc_agent = next(a for a in agents_list if a["name"] == "DoctorAgent")
    assert "active_patients" in doc_agent
    assert "recent_messages" in doc_agent
