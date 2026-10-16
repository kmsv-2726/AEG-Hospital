# MASTER PROJECT SPECIFICATION
# Smart Hospital Emergency Response System Using Multi-Agent AI

**Document purpose:** Complete implementation specification for an autonomous coding LLM.

**Project type:** Academic Artificial Intelligence project.

**Implementation approach:** Custom-built, rule-based multi-agent system with a simulated hospital environment.

**Mandatory constraint:** The complete core application must work locally without external LLM APIs, API keys, paid AI services, or cloud dependencies.

---

# PART A — INSTRUCTIONS TO THE CODING LLM

## 1. Your Role

Act as a senior Python developer, multi-agent systems engineer, software architect, testing engineer, and technical documentation writer.

You are responsible for taking this project from its current state to a working, tested, demonstrable academic application.

Do not merely explain how to build the project. Inspect the available development environment, create and implement the application, execute tests, resolve errors, and document the actual results.

The user is a final-year B.Tech CSE student. The implementation and documentation must be technically correct, understandable to a student, and suitable for an academic project review.

### Mandatory working principles

1. Inspect the development environment before installing packages or modifying files.
2. Inspect existing project files before creating or overwriting anything.
3. Build the project incrementally, using working checkpoints.
4. Implement all core agents yourself in Python.
5. Do not make an external LLM a dependency of any core functionality.
6. Do not fabricate successful test results, screenshots, metrics, or installation status.
7. Do not install unnecessary frameworks or services.
8. Run the application and verify its behavior rather than assuming that code is correct.
9. Preserve existing user files and avoid destructive changes.
10. Maintain a clear record of completed tasks, remaining tasks, errors, and next steps.

If you encounter an obstacle, investigate it, implement a safe workaround when possible, and document any remaining limitation.

---

# PART B — PROJECT DEFINITION

## 2. Project Title

**Smart Hospital Emergency Response System Using Multi-Agent AI**

## 3. Problem Statement

Hospital emergency departments must coordinate multiple resources, including ambulances, doctors, diagnostic equipment, and intensive care beds. When several simulated emergency patients arrive simultaneously, limited resources may become unavailable, creating queues, delays, and allocation conflicts.

A centralized system that handles every decision independently can become difficult to maintain and extend. This project proposes a cooperative Multi-Agent AI system in which specialized software agents independently manage different resource categories and communicate through structured messages.

A Hospital Coordinator coordinates these agents, manages the overall patient workflow, resolves coordination conflicts, and records system events.

The proposed system will simulate emergency workflows within one hospital and evaluate its performance using predefined metrics and a comparison against a First-In, First-Out (FIFO) scheduling baseline.

The project is strictly an academic simulation. It must not be presented as a clinically validated triage system, a real emergency dispatch service, or a substitute for medical professionals.

## 4. Project Objectives

The application must:

1. Demonstrate the design and implementation of a Multi-Agent System.
2. Implement five specialized software agents and one coordinating agent.
3. Demonstrate PEAS descriptions for the individual agents and the complete system.
4. Use rule-based reasoning and explainable resource-allocation algorithms.
5. Implement structured communication between agents.
6. Represent hospital knowledge using structured data and predefined rules.
7. Implement patient workflow planning and valid state transitions.
8. Handle competition for limited simulated resources.
9. Maintain a reproducible simulation using synthetic data.
10. Provide a functional user interface.
11. Record agent decisions, messages, state transitions, and resource utilization.
12. Calculate meaningful performance metrics.
13. Compare the proposed priority/resource-aware strategy against FIFO.
14. Generate test results and genuine screenshots for the final academic report.
15. Run entirely without external AI API keys.

## 5. Scope and Constraints

### In scope

- One simulated hospital.
- Synthetic patient and resource data.
- Custom Python agent implementations.
- Deterministic rules and utility-based selection.
- Event-driven simulation.
- Agent communication.
- Workflow planning.
- Resource reservations and queues.
- Local database persistence.
- REST API.
- Web-based dashboard.
- Automated tests.
- Performance evaluation.
- Academic documentation.

### Out of scope

- Real patient records or personally identifiable health information.
- Real-world medical diagnosis or treatment recommendations.
- Physical ambulance tracking or dispatch.
- Medical device integration.
- Real hospital information systems.
- Training deep learning models.
- Mandatory use of an LLM.
- External LLM APIs, API keys, subscriptions, or paid inference.
- Multi-hospital coordination.
- Cloud deployment as a prerequisite.
- RAG, vector databases, and embeddings in the initial implementation.

Do not expand the scope without first completing and verifying the mandatory requirements.

---

# PART C — DEVELOPMENT ENVIRONMENT AND DEPENDENCIES

## 6. Initial Environment Inspection

Before writing application code, inspect the environment and report:

- Operating system and version.
- Python version.
- Python package manager version.
- Node.js version.
- npm version.
- Git version.
- PostgreSQL availability, if relevant.
- Docker availability, if relevant.
- Existing project directory and source files.
- Available disk space, if accessible.
- Existing relevant Python and Node packages.
- Whether the required ports are already in use, if this can be checked safely.

Use the actual results of environment commands. Do not claim that a dependency is installed simply because it is listed in this document.

After inspection, produce a concise compatibility report and dependency installation plan.

If a suitable project already exists, inspect and extend it instead of generating a conflicting project structure.

## 7. Recommended Technology Stack

Use the following stack unless an existing environment limitation makes a documented alternative necessary.

| Layer | Technology | Purpose |
|---|---|---|
| Core language | Python 3.11 or later | Agent intelligence and simulation |
| Agent architecture | Custom Python classes | Autonomous agent behavior |
| API backend | FastAPI | REST endpoints |
| Data validation | Pydantic | Validate inputs and messages |
| Database access | SQLAlchemy | Database models and queries |
| Database | SQLite initially | Local persistence |
| Frontend | React with Vite | Dashboard and controls |
| Frontend language | JavaScript or TypeScript | User interface |
| API communication | Axios or fetch | Connect frontend to backend |
| Charts | Recharts | Metrics and evaluation |
| Testing | pytest | Automated backend tests |
| API testing | FastAPI TestClient | Endpoint tests |
| Version control | Git | Source management |

Use a compatible set of package versions, verify installation, and pin working versions in the dependency files.

### Backend dependencies

Install only the packages required for the implementation, such as:

- `fastapi`
- `uvicorn`
- `pydantic`
- `sqlalchemy`
- `pytest`
- `httpx`

Additional packages may be introduced only when justified by a concrete requirement.

Use Python's built-in modules where appropriate for event scheduling, timestamps, enums, logging, and deterministic simulation.

### Frontend dependencies

Use:

- React
- Vite
- Axios or native fetch
- Recharts

An icon library or styling framework may be added if it materially improves the interface. It is not mandatory.

### Database decision

Start with SQLite because it is straightforward to install and suitable for a single-machine academic simulation.

Use SQLAlchemy so the application can be migrated to PostgreSQL later if required.

Do not install PostgreSQL, Docker, Redis, a message broker, or a vector database unless a demonstrated project requirement makes it necessary.

### Installation rules

- Create a project-local Python virtual environment.
- Do not modify system-wide packages unnecessarily.
- Do not uninstall existing software without permission.
- Do not use administrator privileges unless genuinely necessary and explicitly authorized.
- Do not overwrite unrelated files.
- Create `.gitignore` before committing source code.
- Do not commit credentials, virtual environments, databases containing private information, or generated build directories.
- Keep the application runnable locally.

---

# PART D — MULTI-AGENT SYSTEM DESIGN

## 8. Required Agents

Implement exactly five specialized resource/workflow agents and one Hospital Coordinator.

The Simulation Engine is a supporting subsystem, not an additional agent.

Every agent must have:

- A unique name and identifier.
- A defined goal.
- Defined inputs and percepts.
- Its own decision-making logic.
- Defined actions.
- Access to the relevant portion of shared state.
- A structured communication interface.
- Event logging.
- Input validation and error handling.
- Unit tests.

Use a common base interface for the specialized agents.

A recommended interface is:

- `perceive(...)`
- `decide(...)`
- `act(...)`
- `handle_message(...)`
- `get_status(...)`

These are interface suggestions, not a requirement to use exactly these method names.

Keep the agents independently testable. Do not place all business logic in a single coordinator class or in the API entry point.

## 9. Base Agent

Implement a reusable base agent that provides:

- Agent identity.
- Agent type.
- Current status.
- Message handling interface.
- Event emission.
- Access to permitted shared state.
- Basic error reporting.
- Common logging behavior.

The base agent must not contain all the specialized decision rules. Each subclass must implement its own responsibility.

## 10. Triage Agent

### Goal

Assign a synthetic emergency priority according to predefined simulation rules.

### Inputs

- Patient ID.
- Predefined severity category.
- Configured scenario attributes.
- Arrival time.
- Relevant simulation requirements.

### Priority categories

- P1: Critical.
- P2: High.
- P3: Moderate.
- P4: Low.

### Decision logic

Use explicit, deterministic rules. Do not call an external LLM or claim that the rules implement a medically validated triage protocol.

The rules should be configurable and covered by tests.

### Actions

- Validate the patient input.
- Assign the configured synthetic priority.
- Store the result.
- Generate a structured requirement object.
- Notify the Coordinator.
- Record the decision and its explanation.

### Example output

    {
      "agent": "TriageAgent",
      "patient_id": "P001",
      "priority": "P1",
      "action": "TRIAGE_COMPLETED",
      "reason": "The configured simulation rule matched the critical category."
    }

## 11. Ambulance Agent

### Goal

Allocate an eligible, available simulated ambulance.

### Ambulance attributes

- Ambulance ID.
- Availability status.
- Simulated location.
- Distance.
- Estimated travel time.
- Equipment capabilities.
- Current assignment.
- Availability timestamp.

### Inputs

- Patient priority.
- Required capabilities.
- Available ambulance list.
- Simulated travel times.
- Current reservations.

### Algorithm

1. Retrieve eligible ambulances.
2. Remove unavailable or incompatible ambulances.
3. Calculate a documented selection score for each eligible ambulance.
4. Select the best eligible candidate.
5. Reserve the ambulance atomically.
6. Record the assignment and dispatch event.
7. Notify the Coordinator.
8. If none is available, return a waiting or unavailable result.

Travel times and locations are simulated. No GPS integration is required.

## 12. Doctor Agent

### Goal

Assign a suitable simulated doctor to an eligible patient.

### Doctor attributes

- Doctor ID.
- Display name or synthetic label.
- Specialty.
- Availability.
- Workload.
- Current patient assignment.
- Availability timestamp.

### Supported specialties

- Emergency Medicine.
- Trauma.
- Cardiology.
- Neurology.
- General Medicine.

### Algorithm

1. Identify the requested specialty.
2. Find available compatible doctors.
3. Apply documented eligibility constraints.
4. Rank eligible candidates by a deterministic score.
5. Reserve the selected doctor.
6. Notify the Coordinator.
7. Queue the request if no compatible doctor is available.

Do not implement actual medical diagnosis or make clinical decisions.

## 13. Diagnostic Agent

### Goal

Allocate simulated diagnostic equipment and manage queues.

### Supported resource categories

- CT.
- MRI.
- X-Ray.
- Blood Test.
- Ultrasound.

### Resource attributes

- Resource ID.
- Resource category.
- Availability.
- Queue length.
- Simulated processing duration.
- Current patient.
- Availability timestamp.

### Algorithm

1. Validate the requested resource category.
2. Find compatible equipment.
3. Evaluate current availability and queue state.
4. Select a suitable resource.
5. Reserve the resource.
6. Schedule a completion event.
7. Release the resource when processing finishes.
8. Notify the Coordinator of completion or unavailability.

Diagnostic processing is simulated. The system must not interpret results or recommend medical treatment.

## 14. ICU Agent

### Goal

Manage simulated ICU bed allocation and release.

### ICU bed attributes

- Bed ID.
- Availability status.
- Simulated equipment availability.
- Current patient.
- Reservation timestamp.
- Release timestamp.

### Algorithm

1. Receive an ICU request.
2. Check configured requirements.
3. Identify eligible available beds.
4. Reserve a suitable bed atomically.
5. Notify the Coordinator.
6. Return a waiting status if no bed is available.
7. Release the bed when the associated simulated workflow ends.

The agent must not make real clinical admission decisions.

## 15. Hospital Coordinator

### Goal

Coordinate the overall patient workflow and communication between specialized agents.

### Responsibilities

- Receive and validate emergency requests.
- Initiate the patient workflow.
- Send messages to appropriate agents.
- Process agent responses.
- Update workflow state through permitted transitions.
- Coordinate resource requests.
- Handle waiting states and retries.
- Detect resource allocation conflicts.
- Record events and decisions.
- Collect simulation metrics.
- Notify the dashboard of updated state through the API layer.

### Architectural constraint

The Coordinator must not bypass agent logic by directly assigning every resource.

The specialized agent responsible for a resource must validate and perform its own reservation through a safe, shared reservation service or database transaction.

The Coordinator may request an action and process its result, but must not silently override availability constraints.

---

# PART E — ENVIRONMENT, KNOWLEDGE AND COMMUNICATION

## 16. Shared Hospital State

Define a structured representation of the simulation state.

It must contain:

- Patients.
- Ambulances.
- Doctors.
- ICU beds.
- Diagnostic resources.
- Active patient workflows.
- Pending resource requests.
- Agent messages.
- Event logs.
- Simulation clock.
- Scheduled events.
- Performance metrics.
- Current simulation run ID.

Use Pydantic schemas at API boundaries and appropriate typed Python models internally.

Avoid uncontrolled global variables. State ownership and update permissions must be documented.

## 17. Agent Communication Protocol

Implement structured messages.

Each message must contain:

- Message ID.
- Sender.
- Receiver.
- Message type.
- Patient ID when applicable.
- Resource ID when applicable.
- Simulation timestamp.
- Payload.
- Correlation or request ID.
- Processing status.

Use a validated message schema.

### Required message types

- `PATIENT_REGISTERED`
- `TRIAGE_COMPLETED`
- `AMBULANCE_REQUEST`
- `AMBULANCE_ASSIGNED`
- `PATIENT_ARRIVING`
- `DOCTOR_REQUEST`
- `DOCTOR_ASSIGNED`
- `DIAGNOSTIC_REQUEST`
- `DIAGNOSTIC_ASSIGNED`
- `ICU_REQUEST`
- `ICU_RESERVED`
- `RESOURCE_UNAVAILABLE`
- `RESOURCE_RELEASED`
- `TREATMENT_STARTED`
- `PATIENT_COMPLETED`
- `PATIENT_DISCHARGED`

Additional message types may be added when necessary.

### Example

    {
      "message_id": "MSG-001",
      "sender": "TriageAgent",
      "receiver": "HospitalCoordinator",
      "message_type": "TRIAGE_COMPLETED",
      "patient_id": "P001",
      "resource_id": null,
      "simulation_time": 0,
      "correlation_id": "REQ-001",
      "payload": {
        "priority": "P1"
      }
    }

All important messages must be recorded in the event log.

Do not use unstructured print statements as the primary communication mechanism.

For the initial version, communication may occur through direct method calls and a typed message dispatcher. A distributed messaging platform is not required.

## 18. Knowledge Representation

Represent hospital knowledge using structured data and explicit rules.

Knowledge includes:

- Patient requirements.
- Synthetic severity categories.
- Doctor specialties.
- Resource availability.
- Ambulance capabilities.
- ICU capacity.
- Diagnostic equipment types.
- Resource eligibility rules.
- Priority weights.
- Selection score weights.
- Workflow transition rules.

Keep configuration separate from decision-making code wherever practical.

Use a small, documented configuration file or typed configuration object for simulation parameters.

No trained machine learning model, vector database, or external knowledge API is required.

## 19. Planning and Workflow Management

Implement a finite-state machine or equivalent explicit workflow planner.

### Example workflow

    ARRIVED
      -> TRIAGED
      -> AMBULANCE_ASSIGNED
      -> IN_TRANSIT
      -> ADMITTED
      -> DOCTOR_ASSIGNED
      -> DIAGNOSTICS (if required)
      -> ICU_ALLOCATED (if required)
      -> TREATMENT_SIMULATED
      -> COMPLETED

The exact workflow should be adapted to the simulation. Optional steps must be explicitly skipped when they are not required.

### Required waiting states

- `WAITING_FOR_AMBULANCE`
- `WAITING_FOR_DOCTOR`
- `WAITING_FOR_DIAGNOSTIC`
- `WAITING_FOR_ICU`

### Requirements

- Validate all state transitions.
- Reject invalid transitions with a useful error.
- Record state changes in the event log.
- Retry eligible requests when resources become available.
- Avoid infinite retry loops.
- Record terminal outcomes for requests that cannot be fulfilled.
- Ensure reset returns the simulation to a consistent initial state.

The Simulation Engine must manage simulated time and process scheduled events. Do not depend on real-time sleeps to simulate hours or minutes.

---

# PART F — RESOURCE ALLOCATION AND SIMULATION

## 20. Resource Allocation

Use a two-stage approach:

**Stage 1: Eligibility constraints**

Remove resources that are unavailable, incompatible, or already reserved.

**Stage 2: Deterministic ranking**

Rank the remaining eligible candidates using a documented utility score.

Example:

    score = (
        priority_weight
        + suitability_weight * suitability_score
        - time_weight * estimated_wait
        - workload_weight * workload_penalty
    )

Normalize the inputs where appropriate and document the configured weights.

Do not allow a high score to override a hard availability or compatibility constraint.

Provide an explanation for every assignment, such as:

- Resource was available.
- Required capability matched.
- Estimated wait was lower than the other eligible candidates.
- Workload was lower than the alternative.

Tie-breaking must be deterministic, for example by resource ID or arrival order.

## 21. Resource Conflict Handling

The simulation must deliberately demonstrate resource contention.

Example:

- One trauma doctor.
- One CT scanner.
- Three ICU beds.
- Three ambulances.
- Multiple simultaneous synthetic patient requests.

Required behavior:

1. Multiple patients may request the same resource.
2. The resource-owning agent checks current availability.
3. Only one request can successfully reserve an exclusive resource at a time.
4. Other requests enter an appropriate waiting state.
5. The conflict is logged.
6. The request is reconsidered when a resource becomes available.
7. The waiting patient is not assigned an unavailable resource.
8. All reservations are released at the correct workflow stage.

Use transaction-safe reservation logic, locking where appropriate, or another concurrency-safe design.

Even if the first version processes events sequentially, resource reservation must be designed so that invalid double-booking is prevented.

## 22. Simulation Engine

Build a discrete-event simulation engine.

It should support:

- Synthetic patient arrivals.
- Simulated travel durations.
- Resource request events.
- Service start events.
- Service completion events.
- Resource release events.
- Patient workflow transitions.
- Waiting queues.
- Simulation start and reset.
- Fixed-seed reproducibility.
- Event history.
- Metrics calculation.

Use a simulated clock and an ordered event queue.

Do not make simulation results depend on arbitrary real-time delays, browser timing, or network speed.

## 23. Demonstration Scenario

Create a deterministic initial scenario.

### Resources

| Resource | Quantity |
|---|---:|
| Ambulances | 3 |
| Trauma doctors | 1 |
| Cardiology doctors | 1 |
| General Medicine doctors | 2 |
| ICU beds | 3 |
| CT scanners | 1 |
| MRI scanners | 1 |
| X-Ray machines | 1 |

Blood Test and Ultrasound resources may be added.

### Patients

| Patient | Synthetic category | Example requirement |
|---|---|---|
| P001 | Critical trauma | Trauma specialty, X-Ray, ICU |
| P002 | Critical cardiac | Cardiology specialty |
| P003 | High trauma | Trauma specialty |
| P004 | Moderate injury | General Medicine, optional X-Ray |
| P005 | Low severity | General Medicine |

The scenario must create at least one real resource conflict in the simulation, not merely display a warning.

Use configurable synthetic durations and arrivals to produce reproducible behavior.

Demonstrate:

1. Patient registration.
2. Priority assignment.
3. Ambulance allocation.
4. Doctor allocation.
5. Diagnostic allocation.
6. ICU reservation.
7. Waiting due to limited resources.
8. Agent communication.
9. Resource release and retry.
10. Workflow completion.
11. Metric calculation.

Do not assume every patient must use every resource. Optional resource requirements must be represented explicitly.

---

# PART G — DATABASE AND BACKEND

## 24. Database Design

Implement SQLAlchemy models for:

- `patients`
- `doctors`
- `ambulances`
- `icu_beds`
- `diagnostic_resources`
- `agent_messages`
- `events`
- `simulation_runs`

Include appropriate:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Status fields.
- Simulation timestamps.
- Resource assignment fields.
- Correlation IDs.
- Indexes where useful.

Store simulated timestamps consistently. Keep simulation time separate from wall-clock time.

Use transactions for resource reservation and workflow updates when multiple records must remain consistent.

Create a seeding script to initialize the demonstration data.

Provide a reset mechanism that clears or restores simulation data safely without deleting unrelated user files.

## 25. REST API

Implement and test these endpoints:

| Method | Endpoint | Function |
|---|---|---|
| GET | `/api/health` | Backend health check |
| GET | `/api/patients` | List synthetic patients |
| POST | `/api/patients` | Register a patient |
| GET | `/api/resources` | Retrieve resource availability |
| GET | `/api/agents` | Retrieve agent status |
| GET | `/api/events` | Retrieve event history |
| POST | `/api/simulation/start` | Start a simulation |
| POST | `/api/simulation/reset` | Reset simulation state |
| GET | `/api/metrics` | Retrieve current metrics |
| POST | `/api/emergency` | Submit a synthetic emergency |

You may add endpoints for simulation status, event pagination, baseline selection, or simulation configuration.

Validate all request and response schemas.

Use suitable HTTP status codes and useful error messages.

Document the endpoints through FastAPI's generated OpenAPI documentation.

Do not use frontend-only hardcoded values as a substitute for backend functionality.

---

# PART H — FRONTEND AND USER INTERFACE

## 26. Dashboard Requirements

Create a clear, responsive dashboard suitable for an academic demonstration.

### Page 1: Overview

Display:

- Active simulated emergencies.
- Waiting patients.
- Available ambulances.
- Available doctors.
- Available ICU beds.
- Diagnostic equipment availability.
- Simulation status.
- Start and reset controls.

### Page 2: Patient Queue

Display:

- Patient ID.
- Synthetic priority.
- Arrival time.
- Current workflow state.
- Assigned ambulance.
- Assigned doctor.
- Diagnostic status.
- ICU status.
- Waiting duration.

Provide useful status filters and priority indicators.

### Page 3: Agent Monitor

Display all five specialized agents and the Coordinator.

For each agent, show:

- Name.
- Current state.
- Most recent action.
- Last message.
- Pending requests, if any.
- Relevant resource information.

### Page 4: Event Timeline

Display:

- Timestamp.
- Sender.
- Receiver.
- Message type.
- Patient ID.
- Event details.
- Outcome.

Make resource conflicts and successful reservations easy to identify.

### Page 5: Metrics and Results

Display:

- Average waiting time.
- Average simulated ambulance response time.
- Time to doctor.
- Time to diagnostics.
- Time to ICU.
- Resource utilization.
- Unresolved requests.
- Resource conflicts.
- Workflow completion rate.

Include a comparison between FIFO and priority/resource-aware scheduling.

All dashboard values must come from actual backend data.

Charts must update after simulation runs and resets.

---

# PART I — PERFORMANCE EVALUATION

## 27. Required Performance Metrics

Implement the following metrics.

### Average waiting time

For completed resource requests:

    waiting_time = resource_start_time - resource_request_time

Calculate the mean over the eligible requests.

### Average response time

For simulated ambulance dispatches:

    response_time = ambulance_arrival_time - emergency_request_time

Document the precise event definitions used.

### Time to doctor

    time_to_doctor = doctor_assignment_time - hospital_arrival_time

### Time to diagnostics

    time_to_diagnostics = diagnostic_start_time - diagnostic_request_time

### Time to ICU

    time_to_ICU = ICU_reservation_time - ICU_request_time

Calculate only for patients who requested and received an ICU reservation.

### Resource utilization

    utilization_percent =
        busy_resource_time / available_resource_time * 100

Calculate utilization separately for ambulances, doctors, diagnostic resources, and ICU beds.

### Unresolved requests

Count requests still waiting or otherwise unfulfilled when the simulation ends.

### Resource conflicts

Count rejected allocation attempts caused by resource unavailability, incompatible allocation attempts, or duplicate reservations. Define categories clearly and avoid double-counting the same event.

### Workflow completion rate

    completion_rate =
        completed_workflows / registered_patients * 100

If no eligible observations exist for a metric, return `N/A` or a structured null value. Do not substitute zero.

Record the denominator, excluded cases, and simulation duration when presenting results.

## 28. Baseline Comparison

Implement two selectable allocation strategies:

**Baseline A — FIFO**

- Process eligible resource requests in arrival order.
- Respect resource availability and compatibility.
- Use arrival time as the tie-breaker.

**Proposed Strategy B — Priority and Resource-Aware**

- Apply eligibility constraints.
- Prioritize requests using the configured priority policy.
- Rank compatible resources using documented utility scores.
- Handle waiting requests and resource releases.

Run both strategies on equivalent initial scenarios with identical arrivals, resources, and service durations.

Use multiple synthetic workload sizes for evaluation, for example 5, 20, 50, and 100 patients, subject to acceptable runtime.

If random workload generation is used, use controlled seeds and equivalent workloads for both strategies.

Generate charts comparing relevant metrics.

Do not claim that the proposed approach is superior unless the measured results support that conclusion.

Discuss trade-offs, including the possibility that priority scheduling reduces waiting for high-priority requests while increasing waiting for lower-priority requests.

The evaluation measures simulated software performance, not real hospital outcomes.

---

# PART J — TESTING

## 29. Testing Requirements

Use pytest for backend tests.

Implement the following test levels.

### Unit tests

Test:

- Triage rules.
- Invalid input handling.
- Resource eligibility.
- Ambulance selection.
- Doctor specialty matching.
- Diagnostic resource selection.
- ICU bed reservation.
- Utility score calculations.
- Workflow transition validation.
- Metric calculations.

### Integration tests

Test:

- Agent message exchange.
- Coordinator processing.
- Database persistence.
- Resource reservation and release.
- Waiting queue updates.
- Event recording.
- Retry behavior after resource release.

### End-to-end tests

Run complete synthetic emergency scenarios and verify that:

- Patients are registered.
- Agents process requests.
- Resource allocations are valid.
- Conflicts are handled.
- Workflows advance.
- Events are recorded.
- Metrics are calculated.
- Reset restores the expected initial state.

### API tests

Test valid requests, invalid requests, missing resources, duplicate requests, and server errors.

### Frontend checks

Verify that the dashboard renders backend data correctly, controls trigger the appropriate API requests, and charts reflect the latest simulation run.

### Reproducibility checks

Repeat a deterministic simulation from the same initial state and verify that its event ordering, assignments, and metrics match.

### Required test report

Generate a report containing:

- Test name.
- Purpose.
- Input.
- Expected result.
- Actual result.
- Pass/fail status.
- Relevant error details.

Run the tests before marking a feature complete.

Never invent passing test results.

---

# PART K — ACADEMIC REPORT REQUIREMENTS

## 30. Final Report Structure

Create `docs/project_report.md` with the following six main sections, aligned with the user's academic rubric.

### Section 1 — Introduction

Include:

- Background.
- Problem statement.
- Motivation.
- Objectives.
- Proposed solution.
- Scope and limitations.

### Section 2 — PEAS Description

Include:

- PEAS for the complete system.
- PEAS for each agent.
- Performance measure definitions.
- Logical sensors and their input mappings.
- Actuators and their output mappings.
- A clear explanation of how the mappings are implemented.

### Section 3 — Agent and Environment Analysis

Include:

- Agent categories.
- Goal-based and rule-based behavior.
- Utility-based selection where implemented.
- Cooperative multi-agent behavior.
- Observability.
- Determinism.
- Dynamic environment properties.
- Discrete state representation.
- Sequential workflow properties.
- Justification for each classification based on the actual implementation.

Do not label a property as implemented if the architecture does not support it.

### Section 4 — Design

Include:

- Overall architecture.
- Component diagram.
- Agent responsibilities.
- Agent communication diagram.
- Shared state.
- Database design.
- Workflow state machine.
- Algorithms.
- Resource conflict resolution.
- Hardware requirements.
- Software requirements.
- Dependencies and packages.
- Security and safety constraints.

### Section 5 — Implementation

Include:

- Development environment.
- Input representation.
- Synthetic dataset.
- Module structure.
- Class responsibilities.
- Algorithms.
- Database entities.
- API endpoints.
- Frontend pages.
- Simulation scenario.
- Example message exchange.
- Implementation limitations.

### Section 6 — Testing and Results

Include:

- Testing levels.
- Test cases.
- Actual test results.
- Simulation screenshots.
- Performance metric definitions.
- FIFO comparison.
- Charts generated from actual runs.
- Discussion of findings.
- Limitations and future improvements.

Add a conclusion and references after the six required sections if useful.

Use formal but understandable academic English.

Include diagram source files where practical so diagrams can be edited.

Never fabricate references, screenshots, measurements, or findings.

---

# PART L — SCREENSHOTS AND DEMONSTRATION

## 31. Required Screenshots

Create a directory named `docs/screenshots/`.

Capture genuine screenshots of the running application showing:

1. Main dashboard before the simulation.
2. Patient queue with different priorities.
3. Agent monitor.
4. Event timeline showing agent communication.
5. A resource conflict and waiting request.
6. A successful resource release and reassignment.
7. Metrics after a completed simulation.
8. FIFO-versus-priority comparison charts.

Use actual screenshots from the implemented frontend or, if the frontend is not yet functional, clearly identified terminal/API outputs for interim development evidence.

Do not use generated illustrations or mockup images as evidence of a functioning application.

Add captions explaining what each screenshot demonstrates.

## 32. Demonstration Script

Create `scripts/run_simulation.py` to run the deterministic demonstration without requiring the frontend.

The demonstration should:

1. Initialize the synthetic hospital.
2. Register the predefined patients.
3. Trigger the agents.
4. Process resource requests.
5. Demonstrate a resource conflict.
6. Release a resource.
7. Reconsider waiting requests.
8. Complete eligible workflows.
9. Print a concise event summary.
10. Display the final metrics.

Ensure that the script is repeatable and its output is understandable to a student presenting the project.

---

# PART M — PROJECT STRUCTURE

## 33. Required Directory Layout

Use this layout as the target. Adapt it only when a simpler or more maintainable structure is justified.

    smart-hospital-mas/
    ├── backend/
    │   ├── app/
    │   │   ├── agents/
    │   │   │   ├── __init__.py
    │   │   │   ├── base_agent.py
    │   │   │   ├── triage_agent.py
    │   │   │   ├── ambulance_agent.py
    │   │   │   ├── doctor_agent.py
    │   │   │   ├── diagnostic_agent.py
    │   │   │   └── icu_agent.py
    │   │   ├── coordinator/
    │   │   │   ├── __init__.py
    │   │   │   └── hospital_coordinator.py
    │   │   ├── simulation/
    │   │   │   ├── engine.py
    │   │   │   ├── events.py
    │   │   │   └── scenarios.py
    │   │   ├── workflows/
    │   │   │   └── patient_workflow.py
    │   │   ├── models/
    │   │   ├── schemas/
    │   │   ├── services/
    │   │   ├── database/
    │   │   ├── api/
    │   │   └── main.py
    │   ├── tests/
    │   └── requirements.txt
    ├── frontend/
    │   ├── src/
    │   │   ├── components/
    │   │   ├── pages/
    │   │   ├── services/
    │   │   ├── App.jsx
    │   │   └── main.jsx
    │   └── package.json
    ├── scripts/
    │   ├── seed_database.py
    │   └── run_simulation.py
    ├── docs/
    │   ├── project_report.md
    │   ├── architecture.md
    │   ├── testing_results.md
    │   └── screenshots/
    ├── .env.example
    ├── .gitignore
    └── README.md

Do not create empty modules merely to match the directory tree. Each created module must have a clear purpose.

---

# PART N — IMPLEMENTATION PLAN

## 34. Required Development Phases

Work in the following order. Verify each phase before proceeding.

### Phase 1: Environment inspection

- Inspect installed tools.
- Inspect the existing project.
- Report compatibility.
- Prepare the dependency plan.

### Phase 2: Project foundation

- Create the directory structure.
- Create a Python virtual environment.
- Install minimal backend dependencies.
- Configure Git and `.gitignore`.
- Verify imports and the backend health endpoint.

### Phase 3: Domain models

- Define patient and resource models.
- Define enums and workflow states.
- Define structured message schemas.
- Define shared state.
- Add model tests.

### Phase 4: Synthetic data and persistence

- Create the demonstration data generator.
- Implement SQLite and SQLAlchemy.
- Implement database initialization and seeding.
- Test persistence and reset.

### Phase 5: Base agent

- Implement the base interface.
- Implement logging and message handling.
- Test agent identity, status and event emission.

### Phase 6: Specialized agents

Implement and test each agent separately:

1. Triage.
2. Ambulance.
3. Doctor.
4. Diagnostic.
5. ICU.

### Phase 7: Communication and coordination

- Implement message dispatch.
- Implement the Coordinator.
- Implement resource reservation.
- Implement conflict detection.
- Test message delivery and resource exclusivity.

### Phase 8: Workflow and simulation

- Implement the state machine.
- Implement simulated time.
- Implement event scheduling.
- Implement waiting states.
- Implement resource releases and retries.
- Run the deterministic demonstration.

### Phase 9: Metrics and baseline

- Implement metric calculation.
- Implement FIFO scheduling.
- Implement priority/resource-aware scheduling.
- Compare equivalent workloads.
- Generate evaluation charts.

### Phase 10: API

- Implement the required endpoints.
- Add validation and error handling.
- Test endpoints with FastAPI TestClient.

### Phase 11: Frontend

- Create the React application.
- Implement dashboard pages.
- Connect the frontend to the backend.
- Verify actual state updates and simulation controls.

### Phase 12: Testing and refinement

- Run all unit tests.
- Run integration and end-to-end tests.
- Test reproducibility.
- Resolve errors.
- Verify reset and conflict behavior.

### Phase 13: Documentation and demonstration

- Generate the architecture documentation.
- Complete the six-section academic report.
- Capture genuine screenshots.
- Generate actual result charts.
- Write setup and demonstration instructions.

### Phase 14: Final acceptance

- Start the application from a clean documented setup.
- Verify backend and frontend startup.
- Verify database initialization.
- Run the deterministic demo.
- Run the test suite.
- Confirm that the core application works without API keys.
- Produce the final implementation summary.

Do not start the next major phase while the current phase has unresolved critical errors.

---

# PART O — RUNNING THE APPLICATION

## 35. Required Execution Experience

The README must contain exact, verified commands for the user's operating system.

Provide separate instructions for:

- Creating the Python virtual environment.
- Installing backend dependencies.
- Starting the backend.
- Installing frontend dependencies.
- Starting the frontend.
- Seeding synthetic data.
- Running the standalone simulation.
- Running tests.
- Resetting the simulation.

The expected development experience should be approximately:

**Terminal 1 — Backend**

Start the FastAPI server using the documented local command.

**Terminal 2 — Frontend**

Start the Vite development server using the documented npm command.

**Browser**

Open the locally reported frontend URL and verify the dashboard.

Do not assume a port is available. If a port conflict occurs, choose a suitable alternative and document it.

Do not report the application as running unless the process and health check have been verified.

---

# PART P — QUALITY AND SAFETY REQUIREMENTS

## 36. Code Quality

Use:

- Type hints.
- Small, focused classes and functions.
- Pydantic validation.
- Clear separation of concerns.
- Structured logging.
- Explicit error handling.
- Meaningful names.
- Docstrings for important classes and algorithms.
- Consistent formatting.
- Automated tests.
- Reproducible configuration.

Avoid:

- A giant `main.py`.
- Copy-pasted decision logic.
- Unexplained magic numbers.
- Hidden global state.
- Hardcoded dashboard metrics.
- Arbitrary sleeps as a simulation engine.
- Direct database manipulation that bypasses resource constraints.
- Unnecessary external services.
- Claims that the system uses machine learning when it uses only rules.

## 37. Safety and Privacy

- Use synthetic patient records exclusively.
- Do not import real hospital data.
- Do not implement clinical diagnosis.
- Do not recommend actual medical treatment.
- Do not connect to real ambulance or medical equipment systems.
- Clearly label the application as a simulation.
- Avoid collecting personal information through the dashboard.
- Do not include credentials in source control.
- Validate API inputs.
- Prevent duplicate resource reservations.
- Handle errors without exposing secrets or unnecessary system details.

---

# PART Q — FINAL ACCEPTANCE CRITERIA

## 38. Definition of Done

The project is complete only when the following requirements have been verified.

### Multi-agent functionality

- [ ] Base agent interface implemented.
- [ ] Five specialized agents implemented.
- [ ] Hospital Coordinator implemented.
- [ ] Each agent has a distinct responsibility and decision logic.
- [ ] Structured messages work.
- [ ] Messages and actions are logged.

### AI concepts

- [ ] PEAS mappings documented.
- [ ] Agent and environment classification justified.
- [ ] Knowledge representation implemented.
- [ ] Workflow planning implemented.
- [ ] Rule-based reasoning implemented.
- [ ] Utility/resource allocation implemented.
- [ ] Resource conflicts handled.
- [ ] Agent cooperation demonstrated.

### Simulation

- [ ] Synthetic data generated.
- [ ] Deterministic demo works.
- [ ] Simulated time and events work.
- [ ] Waiting requests are handled.
- [ ] Resources are reserved and released correctly.
- [ ] Reset restores the correct initial state.
- [ ] Repeated deterministic runs produce reproducible results.

### Backend and frontend

- [ ] API starts successfully.
- [ ] Database initializes successfully.
- [ ] API endpoints are tested.
- [ ] Dashboard connects to the backend.
- [ ] Patient queue shows actual state.
- [ ] Agent monitor shows actual activity.
- [ ] Event timeline displays logged events.
- [ ] Metrics and charts use actual results.

### Evaluation and report

- [ ] FIFO baseline implemented.
- [ ] Priority/resource-aware strategy implemented.
- [ ] Equivalent workloads compared.
- [ ] Metrics computed correctly.
- [ ] Unit tests executed.
- [ ] Integration tests executed.
- [ ] End-to-end tests executed.
- [ ] Actual test results documented.
- [ ] Genuine screenshots captured.
- [ ] Six-section academic report completed.
- [ ] README setup instructions verified.

### Independence from external services

- [ ] No LLM API key required.
- [ ] No paid AI service required.
- [ ] Core functionality runs locally.
- [ ] No external AI dependency controls resource allocation.

---

# PART R — REQUIRED FIRST RESPONSE AND WORKING BEHAVIOR

## 39. First Task

Do not immediately generate the entire codebase.

Your first response must contain:

1. A concise summary of the requirements you understood.
2. The actual environment inspection results.
3. The existing project files discovered.
4. The dependency compatibility assessment.
5. The proposed implementation sequence.
6. Any blocking issue that genuinely requires user input.

After providing the environment report, begin implementation if the environment and permissions permit.

Do not ask the user to restate requirements already defined in this document.

## 40. Progress Tracking

Maintain a `docs/implementation_status.md` file with:

- Phase name.
- Task.
- Status: Not Started, In Progress, Blocked or Verified.
- Files created or changed.
- Commands executed.
- Tests executed.
- Actual outcomes.
- Known limitations.
- Next task.

Update this file after completing each phase.

Keep the final README and implementation status consistent with the actual repository.

## 41. Final Deliverables

At completion, provide:

1. A working project source tree.
2. A verified dependency list.
3. A database initialization and synthetic data seeding process.
4. Five specialized agents and the Coordinator.
5. A working simulation engine.
6. A working backend API.
7. A functional React dashboard.
8. Automated tests and actual test results.
9. FIFO comparison and evaluation charts.
10. A complete six-section academic report.
11. Genuine application screenshots.
12. Architecture documentation.
13. README with verified setup and execution commands.
14. An implementation status report.
15. A concise final summary of completed features and known limitations.

If a feature cannot be completed, clearly mark it as incomplete rather than falsely claiming acceptance.

**Begin now with Phase 1: inspect the available environment and existing project files, then report your findings before implementing the application.**
