Smart Hospital Emergency Response System
Multi-Agent AI Simulation Project
Build a complete academic prototype called:
"Smart Hospital Emergency Response System Using Multi-Agent AI"
The project must simulate ONE hospital only. Do not implement multiple hospitals in the MVP.
The purpose of the system is to demonstrate concepts from Artificial Intelligence including:
•	PEAS
•	Intelligent Agents
•	Multi-Agent Systems
•	Knowledge Representation
•	Planning
•	Search
•	Reasoning
•	Agent Communication
•	Resource Allocation
•	Utility-based decision making
•	Agentic AI
•	Optional RAG/LLM integration
The system must use ONLY synthetic/simulated patient and hospital data. It must NOT provide real medical diagnosis, clinical recommendations, or real-world treatment decisions.
________________________________________
1. Core Agents
Implement the following autonomous agents:
1.	Triage Agent
2.	Ambulance Agent
3.	Doctor Agent
4.	Diagnostic Lab Agent
5.	ICU Agent
6.	Hospital Coordinator/Orchestrator Agent
Each agent must have:
•	Identity
•	Goal
•	Knowledge
•	Internal state
•	Perception/input
•	Decision logic
•	Actions
•	Communication capability
•	Event logging
Do not create unnecessary agents.
________________________________________
2. Triage Agent
Responsibilities:
•	Receive synthetic emergency patient information.
•	Assign emergency priority.
•	Generate a structured patient requirement.
•	Notify other agents through structured messages.
Priority levels:
P1 = Critical
P2 = High
P3 = Moderate
P4 = Low
Use deterministic rule-based logic for the initial implementation.
The LLM may assist with natural-language extraction, but must not independently make unrestricted medical decisions.
________________________________________
3. Ambulance Agent
Maintain simulated ambulance resources.
Each ambulance must contain:
•	ambulance_id
•	status
•	location
•	distance
•	ETA
•	equipment
•	capacity
•	current_patient
The agent must select a suitable available ambulance based on:
•	availability
•	ETA
•	distance
•	required equipment
All values are simulated.
________________________________________
4. Doctor Agent
Maintain simulated doctors.
Each doctor contains:
•	doctor_id
•	name
•	specialization
•	availability
•	workload
•	current_patient
Supported specializations may include:
•	Emergency Medicine
•	Trauma
•	Cardiology
•	Neurology
•	General Medicine
The agent must match patients to available simulated doctors according to predefined resource-matching rules.
Do not implement medical diagnosis.
________________________________________
5. Diagnostic Lab Agent
Maintain simulated diagnostic resources:
•	CT
•	MRI
•	X-Ray
•	Blood Test
•	Ultrasound
Each resource must contain:
•	resource_id
•	resource_type
•	status
•	queue_length
•	processing_time
•	current_patient
The agent must allocate diagnostic resources and manage simulated queues.
________________________________________
6. ICU Agent
Maintain simulated ICU beds.
Each ICU bed contains:
•	bed_id
•	status
•	ventilator_available
•	monitoring_available
•	patient_id
The ICU Agent must:
•	check bed availability
•	reserve beds
•	release beds
•	maintain ICU occupancy
•	notify the Coordinator when resources are unavailable
No clinical decision-making should be implemented.
________________________________________
7. Hospital Coordinator
Implement a central Coordinator/Orchestrator responsible for coordinating the agents.
It must:
•	receive emergency requests
•	initiate patient workflows
•	communicate with agents
•	maintain shared state
•	coordinate resource conflicts
•	execute planning workflows
•	monitor patient progress
•	log all agent actions
The Coordinator should NOT directly manipulate every resource. It should communicate with specialized agents.
________________________________________
8. Shared Hospital State
Implement a shared state containing:
•	patients
•	ambulances
•	doctors
•	ICU beds
•	diagnostic resources
•	active workflows
•	agent messages
•	event logs
•	performance metrics
Use Pydantic models for validation.
If LangGraph is used, represent the workflow state using a typed state object.
________________________________________
9. Agent Communication
Implement structured agent messages.
Supported message types should include:
PATIENT_REGISTERED
TRIAGE_COMPLETED
AMBULANCE_REQUEST
AMBULANCE_ASSIGNED
PATIENT_ARRIVING
DOCTOR_REQUEST
DOCTOR_ASSIGNED
DIAGNOSTIC_REQUEST
DIAGNOSTIC_ASSIGNED
ICU_REQUEST
ICU_RESERVED
RESOURCE_UNAVAILABLE
TREATMENT_STARTED
PATIENT_COMPLETED
PATIENT_DISCHARGED
Example:
{
"sender": "TriageAgent",
"receiver": "AmbulanceAgent",
"message_type": "AMBULANCE_REQUEST",
"patient_id": "P001",
"priority": "P1",
"timestamp": "..."
}
All important communication must be logged.
________________________________________
10. Planning
Implement an emergency workflow planner.
Example patient workflow:
ARRIVED
→ TRIAGED
→ AMBULANCE_ASSIGNED
→ IN_TRANSIT
→ ADMITTED
→ DOCTOR_ASSIGNED
→ DIAGNOSTICS
→ ICU_ALLOCATED
→ TREATMENT
→ COMPLETED
The planner must support resource conflicts and waiting states.
Example:
If no trauma doctor is available:
PATIENT → WAITING_FOR_DOCTOR
When the doctor becomes available:
PATIENT → DOCTOR_ASSIGNED
The system must support parallelizable tasks where appropriate.
________________________________________
11. Resource Conflict Simulation
The system must support resource contention.
Example:
Resources:
•	1 trauma doctor
•	1 CT scanner
•	3 ICU beds
•	3 ambulances
Patients:
•	P001 Critical Trauma
•	P002 Critical Cardiac
•	P003 High Trauma
•	P004 Moderate Injury
•	P005 Low Severity
The simulation must demonstrate how agents coordinate when multiple patients request the same limited resource.
________________________________________
12. Utility / Selection Logic
Implement transparent deterministic scoring.
Example:
resource_score =
priority_weight
•	suitability_score
•	waiting_time_penalty
•	distance_penalty
•	workload_penalty
Keep the scoring explainable.
Do not use opaque LLM output for core resource allocation.
________________________________________
13. Knowledge Representation
Represent hospital knowledge using structured data and rules.
Knowledge should include:
•	patient requirements
•	doctor specialization
•	doctor availability
•	ambulance equipment
•	ICU capacity
•	diagnostic resource availability
•	emergency priority rules
•	hospital resource policies
Store structured data in PostgreSQL.
Optionally implement a small policy knowledge base for RAG.
________________________________________
14. LLM Integration
Use an LLM only where it provides clear value.
Appropriate uses:
•	converting natural-language emergency requests into structured input
•	summarizing simulation state
•	explaining agent decisions
•	generating natural-language status reports
•	answering questions about simulated hospital policies
Do NOT use the LLM as the unrestricted authority for:
•	medical diagnosis
•	treatment decisions
•	real clinical recommendations
•	arbitrary resource manipulation
The deterministic agent system must remain the source of truth.
________________________________________
15. Optional RAG
Create a small synthetic hospital policy knowledge base.
Possible files:
hospital_policies/
emergency_priority.txt
ambulance_policy.txt
doctor_assignment.txt
diagnostic_policy.txt
icu_allocation.txt
Implement RAG only after the core multi-agent system works.
RAG should be optional and modular.
________________________________________
16. Database
Use PostgreSQL with SQLAlchemy.
Required tables:
patients
doctors
ambulances
icu_beds
diagnostic_resources
agent_messages
events
Add appropriate primary keys, foreign keys, timestamps, status fields, and indexes.
Use Alembic migrations.
________________________________________
17. Backend
Use:
•	Python 3.11+
•	FastAPI
•	Pydantic
•	SQLAlchemy
•	PostgreSQL
•	LangGraph
•	python-dotenv
•	pytest
Create REST APIs for:
•	patients
•	resources
•	agents
•	simulation
•	events
•	metrics
Suggested endpoints:
GET /api/patients
POST /api/patients
GET /api/resources
GET /api/agents
GET /api/events
POST /api/simulation/start
POST /api/simulation/reset
GET /api/metrics
POST /api/emergency
________________________________________
18. Frontend
Use:
•	React
•	Vite
•	React Router
•	Axios
•	Recharts
•	Lucide React
•	Tailwind CSS if useful
Create:
Dashboard
Display:
•	active emergencies
•	available ambulances
•	available doctors
•	available ICU beds
•	diagnostic resource status
Patient Queue
Display:
•	patient ID
•	priority
•	status
•	assigned doctor
•	diagnostic resource
•	ICU bed
Agent Monitor
Display status of:
•	Triage Agent
•	Ambulance Agent
•	Doctor Agent
•	Diagnostic Agent
•	ICU Agent
•	Coordinator
Event Timeline
Display real-time/simulated:
•	agent messages
•	resource allocation
•	patient state changes
•	conflicts
•	completed actions
Metrics
Display:
•	average waiting time
•	average response time
•	ICU utilization
•	doctor utilization
•	ambulance utilization
•	diagnostic utilization
•	patients completed
________________________________________
19. Project Structure
Create:
backend/
app/
agents/
workflows/
models/
schemas/
tools/
database/
llm/
knowledge/
api/
main.py
tests/
requirements.txt
.env.example
frontend/
src/
components/
pages/
services/
App.jsx
main.jsx
package.json
docs/
architecture/
project_report/
api/
scripts/
seed_database.py
run_simulation.py
README.md
docker-compose.yml
________________________________________
20. Development Order
Do NOT attempt to build the entire system at once.
Build in this exact order:
PHASE 1:
Environment and dependency verification.
PHASE 2:
FastAPI + PostgreSQL connection.
PHASE 3:
Database models and migrations.
PHASE 4:
Synthetic hospital data generator.
PHASE 5:
Base Agent class.
PHASE 6:
Triage Agent.
PHASE 7:
Ambulance Agent.
PHASE 8:
Doctor Agent.
PHASE 9:
Diagnostic Agent.
PHASE 10:
ICU Agent.
PHASE 11:
Coordinator/Orchestrator.
PHASE 12:
Shared state and agent communication.
PHASE 13:
Emergency workflow planner.
PHASE 14:
Resource conflict handling.
PHASE 15:
Simulation engine.
PHASE 16:
REST APIs.
PHASE 17:
React dashboard.
PHASE 18:
LLM integration.
PHASE 19:
Optional RAG.
PHASE 20:
Testing and evaluation.
PHASE 21:
Dockerization.
Do not proceed to the next major phase until the previous phase has a working test.
________________________________________
21. Testing Requirements
Use pytest.
Write tests for:
•	triage priority assignment
•	ambulance selection
•	doctor matching
•	diagnostic allocation
•	ICU reservation
•	resource conflicts
•	message validation
•	patient workflow transitions
•	coordinator behavior
•	database CRUD
•	complete emergency simulation
Create at least one end-to-end scenario involving multiple simultaneous emergency patients.
________________________________________
22. Evaluation
Implement a baseline FIFO resource allocation strategy.
Compare it against the multi-agent priority/resource-aware strategy.
Measure:
•	average patient waiting time
•	average response time
•	average time to doctor
•	average time to diagnostics
•	average time to ICU
•	resource utilization
•	number of unresolved requests
•	number of resource conflicts
Generate charts for the final report.
Do not claim the system improves real hospital outcomes. Results apply only to the synthetic simulation.
________________________________________
23. Demonstration Scenario
Create a deterministic demo with:
Ambulances:
3
Doctors:
1 Trauma
1 Cardiology
2 General Medicine
ICU:
3 beds
Diagnostics:
1 CT
1 MRI
1 X-Ray
Patients:
P001 = Critical Trauma
P002 = Critical Cardiac
P003 = High Trauma
P004 = Moderate Injury
P005 = Low Severity
The demonstration must visibly show:
1.	Patient arrival
2.	Triage
3.	Priority assignment
4.	Ambulance assignment
5.	Doctor assignment
6.	Diagnostic allocation
7.	ICU allocation
8.	Resource conflict
9.	Agent communication
10.	Patient workflow completion
11.	Metrics
________________________________________
24. Logging
Every important agent action must create an event.
Example:
{
"timestamp": "...",
"agent": "AmbulanceAgent",
"patient_id": "P001",
"event_type": "AMBULANCE_ASSIGNED",
"details": "AMB01 assigned",
"status": "SUCCESS"
}
The dashboard must read these events.
________________________________________
25. Dependency Management
Before coding:
1.	Inspect installed Python version.
2.	Inspect installed Node.js and npm versions.
3.	Inspect whether PostgreSQL is installed/running.
4.	Check whether Docker is available.
5.	Check Git installation.
6.	Create a virtual environment.
7.	Install only required backend dependencies.
8.	Create frontend dependencies.
9.	Verify all imports.
10.	Start backend.
11.	Start frontend.
12.	Verify database connection.
13.	Run a basic health check.
14.	Only then begin implementing agents.
Do not blindly upgrade system-wide packages.
Prefer project-local virtual environments.
Pin versions in requirements.txt after successful installation.
________________________________________
26. Configuration
Use environment variables.
Create:
.env.example
with:
DATABASE_URL=
LLM_API_KEY=
LLM_MODEL=
Never commit .env.
Do not hardcode API keys.
________________________________________
27. Code Quality Requirements
Use:
•	type hints
•	Pydantic validation
•	modular classes
•	clear interfaces
•	docstrings for major classes
•	structured logging
•	error handling
•	async FastAPI endpoints where appropriate
•	separation of business logic from API routes
•	separation of agents from database code
Avoid giant files.
Avoid putting all agent logic inside main.py.
________________________________________
28. Architecture Rules
The following rules are mandatory:
1.	Agents must have clearly defined responsibilities.
2.	Deterministic resource allocation must not depend entirely on an LLM.
3.	Agents must communicate using structured messages.
4.	Shared state must be explicit.
5.	All resource changes must be logged.
6.	All patient data must be synthetic.
7.	The system must remain a simulation.
8.	No real medical decision-making.
9.	No unnecessary external services.
10.	The MVP must work locally without Docker.
11.	RAG is optional and must not block the core system.
12.	LLM integration must be modular so the application can run in simulation mode even if the LLM API is unavailable.
________________________________________
29. Final Acceptance Criteria
The project is considered complete only when:
•	The backend starts successfully.
•	The frontend starts successfully.
•	PostgreSQL connects successfully.
•	Synthetic hospital data can be generated.
•	All six agents can run.
•	Agents communicate using structured messages.
•	Patients can move through the emergency workflow.
•	Resource conflicts are handled.
•	ICU/doctor/ambulance/diagnostic resources are updated correctly.
•	Events are logged.
•	Dashboard displays current state.
•	Simulation can be started/reset.
•	Metrics are calculated.
•	Tests pass.
•	LLM integration works when configured.
•	System still works in simulation mode without an LLM API.
•	README contains setup and execution instructions.
•	Architecture documentation explains PEAS, agents, planning, knowledge representation and communication.
________________________________________
30. First Task
Before writing application code, inspect the development environment and report:
1.	Python version
2.	Node.js version
3.	npm version
4.	PostgreSQL availability/version
5.	Docker availability/version
6.	Git availability/version
7.	Operating system
8.	Existing project files
9.	Existing Python packages relevant to the project
10.	Existing Node packages relevant to the project
Then produce a dependency compatibility plan.
Do NOT modify or uninstall existing global software without explicit approval.
After the environment report, create the project structure and install the required dependencies.
Do not begin implementing agents until the environment and dependencies are verified.

