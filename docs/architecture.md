# System Architecture Specification
## Smart Hospital Emergency Response System Using Multi-Agent AI

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

Agents communicate via typed structured messages complying with the protocol defined in Section 17:
- **Message Fields:** `message_id`, `sender`, `receiver`, `message_type`, `patient_id`, `resource_id`, `simulation_time`, `correlation_id`, `payload`, `status`.
- **Communication Pattern:** Event-driven message dispatching mediated by the Hospital Coordinator.

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
    Note over HC,DA: Emergency Care Completed
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
Eligible ambulances ($S_{status} = \text{AVAILABLE}$) are scored as:
$$\text{Score}_{\text{amb}} = 100 - (\text{Distance}_{\text{km}} \times 5.0) + \mathbf{1}_{\{P = \text{P1} \land \text{Ventilator} \in \text{Caps}\}} \times 20.0$$
*Candidate with the maximum score is chosen; ties broken deterministically by Ambulance ID.*

#### B. Doctor Staffing Score
Eligible physicians with specialty matching patient requirement:
$$\text{Score}_{\text{doc}} = 100.0 - (\text{WorkloadCount} \times 10.0)$$
*Physician with the lowest prior workload is selected to balance clinical burn-out.*

#### C. Waiting Queue Priority Comparison (Section 28)
- **FIFO Strategy:** Orders waiting candidates strictly by arrival timestamp:
  $$\text{Key}_{\text{FIFO}} = t_{\text{arrival}}$$
- **Priority-Aware Strategy:** Orders critical life-threats first:
  $$\text{Key}_{\text{Priority}} = (\text{PriorityWeight}(P), t_{\text{arrival}})$$
  where $\text{PriorityWeight}(\text{P1})=1, \text{P2}=2, \text{P3}=3, \text{P4}=4$.

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
