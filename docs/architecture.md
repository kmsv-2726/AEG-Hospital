# System Architecture Specification
## Priority-Aware Multi-Agent Hospital Emergency Coordination and Resource Scheduling Simulator

### 1. High-Level System Architecture

The application is engineered as a cooperative, decentralized **Multi-Agent System (MAS)** where five specialized resource agents collaborate under a centralized **Hospital Coordinator** to optimize emergency patient throughput and manage scarce clinical resources.

```mermaid
graph TD
    UI["Vite + React Dashboard"] <-->|"REST API (HTTP / JSON)"| API["FastAPI Backend Layer"]
    API <--> SS["SimulationService (State Manager)"]
    SS <--> DB[("SQLite Database via SQLAlchemy")]
    SS <--> DES["Discrete-Event Simulation Engine"]

    subgraph "Cooperative Multi-Agent System (MAS)"
        COORD["Hospital Coordinator Agent"]
        TRIAGE["Triage Agent"]
        AMB["Ambulance Agent"]
        DOC["Doctor Agent"]
        DIAG["Diagnostic Agent"]
        ICU["ICU Agent"]

        COORD <-->|"Structured Messages"| TRIAGE
        COORD <-->|"Dispatch Requests"| AMB
        COORD <-->|"Staffing Allocation"| DOC
        COORD <-->|"Imaging Requests"| DIAG
        COORD <-->|"Bed Reservations"| ICU
    end

    DES <--> COORD
```

---

### 2. Multi-Agent Communication Protocol

The coordinator calls specialist agents synchronously and records typed structured messages for each handoff:
- **Message Fields:** `message_id`, `sender`, `receiver`, `message_type`, `patient_id`, `resource_id`, `simulation_time`, `correlation_id`, `payload`, `status`.
- **Communication Pattern:** Coordinator-mediated direct calls with message-bus logging; the bus is not an asynchronous execution engine.

```mermaid
sequenceDiagram
    autonumber
    actor P as Emergency Patient
    participant HC as Hospital Coordinator
    participant TA as Triage Agent
    participant AA as Ambulance Agent
    participant DA as Doctor Agent
    participant DIA as Diagnostic Agent
    participant IA as ICU Agent

    P->>HC: PATIENT_REGISTERED (Arrival)
    HC->>TA: TRIAGE_REQUEST(Symptoms, Trauma Category)
    TA-->>HC: TRIAGE_COMPLETED(Priority P1-P4)
    HC->>AA: AMBULANCE_REQUEST(Priority, Capabilities)
    alt Ambulance Available
        AA-->>HC: AMBULANCE_ASSIGNED(Ambulance ID, ETA)
        Note over AA,HC: Transit to Hospital (Simulated Duration)
        AA-->>HC: RESOURCE_RELEASED(Ambulance ID Available)
    else Fleet Busy
        AA-->>HC: RESOURCE_UNAVAILABLE(Request Queued)
    end
    HC->>DA: DOCTOR_REQUEST(Specialty Required)
    alt Doctor Available
        DA-->>HC: DOCTOR_ASSIGNED(Doctor ID)
    else Specialty Busy (e.g. Trauma Conflict)
        DA-->>HC: RESOURCE_UNAVAILABLE(Enters Waiting Queue)
    end
    opt Diagnostic Scan Required
        HC->>DIA: DIAGNOSTIC_REQUEST(CT / MRI / X-Ray)
        DIA-->>HC: DIAGNOSTIC_ASSIGNED / QUEUED
    end
    opt ICU Critical Admission Required
        HC->>IA: ICU_REQUEST(Ventilator Preference)
        IA-->>HC: ICU_RESERVED / QUEUED
    end
    Note over HC,DA: Simulated examination ends
    HC->>DA: RESOURCE_RELEASED(Doctor Freed)
    opt ICU Bed Freed
        HC->>IA: RESOURCE_RELEASED(Bed Sanitized)
    end
    HC-->>P: PATIENT_DISCHARGED
```

---

### 3. Patient Workflow State Machine (FSM)

The workflow advances through strict validated state transitions:

```mermaid
stateDiagram-v2
    [*] --> REGISTERED
    REGISTERED --> TRIAGED : Rule-Based Urgency Evaluation
    TRIAGED --> WAITING_FOR_AMBULANCE : Fleet Contention
    TRIAGED --> AMBULANCE_ASSIGNED : Available Unit Found
    TRIAGED --> ARRIVED : Ambulatory / Walk-In
    WAITING_FOR_AMBULANCE --> AMBULANCE_ASSIGNED : Unit Freed & Reassigned
    AMBULANCE_ASSIGNED --> IN_TRANSIT : Dispatch En Route
    IN_TRANSIT --> ARRIVED : Scene Arrival & Transport
    ARRIVED --> ADMITTED : Hospital Reception
    ADMITTED --> WAITING_FOR_DOCTOR : Specialty Busy
    ADMITTED --> DOCTOR_ASSIGNED : Physician Allocated
    WAITING_FOR_DOCTOR --> DOCTOR_ASSIGNED : Physician Finished Prior Care
    DOCTOR_ASSIGNED --> WAITING_FOR_DIAGNOSTIC : Scanner Busy
    DOCTOR_ASSIGNED --> DIAGNOSTICS_IN_PROGRESS : Scanner Allocated
    DOCTOR_ASSIGNED --> WAITING_FOR_ICU : ICU Beds Full
    DOCTOR_ASSIGNED --> ICU_ALLOCATED : Critical Bed Reserved
    DOCTOR_ASSIGNED --> TREATMENT_SIMULATED : Non-Diagnostic/Standard Bed
    WAITING_FOR_DIAGNOSTIC --> DIAGNOSTICS_IN_PROGRESS : Scanner Freed
    DIAGNOSTICS_IN_PROGRESS --> DIAGNOSTICS_COMPLETED : Scan Finished
    DIAGNOSTICS_COMPLETED --> WAITING_FOR_ICU : ICU Full
    DIAGNOSTICS_COMPLETED --> ICU_ALLOCATED : Bed Reserved
    DIAGNOSTICS_COMPLETED --> TREATMENT_SIMULATED : Care Pathway
    WAITING_FOR_ICU --> ICU_ALLOCATED : Bed Stepped Down / Released
    ICU_ALLOCATED --> TREATMENT_SIMULATED : Intensive Management
    TREATMENT_SIMULATED --> COMPLETED : Clinical Goals Met
    COMPLETED --> DISCHARGED : Discharge Summary
    DISCHARGED --> [*]
```

---

### 4. Mathematical Decision & Ranking Models

#### A. Ambulance Selection Score
Eligible ambulances must be available and contain all required equipment (P1 defaults to ALS if no requirement is supplied). Eligible ambulances are scored as:
$$\text{Score}_{\text{amb}} = 100 - (\text{Distance}_{\text{km}} \times 5.0) + \mathbf{1}_{\{P = \text{P1} \land \text{Ventilator} \in \text{Caps}\}} \times 20.0$$
*Maximum score wins; ties use ascending Ambulance ID. Simulated travel time is 1.5 minutes per kilometer.*

#### B. Doctor Staffing Score
Candidates must be available and match the requested specialty. The severity factor changes how strongly historical assignment workload is penalized:
$$\text{Score}_{\text{doc}} = 100 - (\text{WorkloadCount} \times 10 \times \text{PriorityFactor})$$
with factors P1=0.50, P2=0.75, P3=1.00 and P4=1.25. Highest score wins; ties use ascending Doctor ID. The priority factor affects comparative workload balancing only; it is not a clinical judgment.

#### C. Diagnostic and ICU Selection
Diagnostics require an exact available category match. Candidates rank by `-simulated_duration × (queue_length + 1)`, then ascending queue length, duration and resource ID. This is negative estimated completion time; higher is better. Queue length is synchronized from coordinator waiting requests. ICU beds first pass availability and required ventilator/monitoring checks, then receive a 20-point preference bonus for a ventilator-equipped bed when priority is P1; ties use ascending bed ID. Each resource agent revalidates and atomically reserves its choice, retrying one refreshed candidate ranking if the selected unit was concurrently taken.

#### D. Waiting Queue Priority Comparison
- **FIFO Strategy:** Orders waiting candidates strictly by arrival timestamp:
    $$\text{Key}_{\text{FIFO}} = (t_{\text{request}}, \text{patient ID})$$
- **Priority-Aware Strategy:** Orders critical life-threats first:
    $$\text{Key}_{\text{Priority}} = (\text{AgingAdjustedPriority}, t_{\text{request}}, \text{patient ID})$$
    Base numeric priorities are P1=1 through P4=4; priority is reduced by 0.05 per waiting minute to a floor of 1. Request time is stage-specific and stable patient ID breaks remaining ties. The same coordinator/resource-agent APIs are used by the web service and CLI.

---

### 5. Database Schema & Entities

The relational database is persisted in SQLite using SQLAlchemy ORM:
- **`patients`**: Tracks demographic data, assigned resources, priority, workflow state, and exact simulation milestone timestamps.
- **`ambulances`**: Call sign, status, base distance, equipment capabilities, and total busy time.
- **`doctors`**: Physician name, medical specialty, status, current assignment, workload count, and total busy time.
- **`diagnostic_resources`**: Scanner category (CT, MRI, X-Ray, Lab, Ultrasound), status, queue length, simulated duration.
- **`icu_beds`**: Unit name, status, ventilator capability, reservation/release timestamps.
- **`simulation_events`**: Chronological event logs with conflict flags and outcomes.
- **`agent_messages`**: Outbox/inbox structured communication logs with correlation IDs.
- **`simulation_runs`**: Historical run records, execution metrics JSON, and comparison data.
