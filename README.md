# Priority-Aware Multi-Agent Hospital Emergency Coordination and Resource Scheduling Simulator

A local-first academic simulator for coordinating synthetic emergency workflows and limited ambulance, doctor, diagnostic, and ICU resources in one hospital. All agents are custom deterministic Python implementations. The application does not require external LLM services or cloud access and does not provide clinical diagnosis or treatment recommendations.

## System

The system includes five specialist agents (Triage, Ambulance, Doctor Allocation, Diagnostic Resource, and ICU Allocation), a Hospital Coordinator, and a discrete-event simulation engine. Patient progression is enforced by a finite-state machine. Resource agents validate eligibility and atomically reserve units; release events trigger retries of waiting requests.

The React/Vite dashboard reads state and evaluation results from the FastAPI backend. Persistence is local SQLite through SQLAlchemy. The system uses synthetic data only.

## Requirements

- Python 3.11 or later
- Node.js 20 or later and npm

## Run Locally (Windows PowerShell)

From the repository root:

```powershell
python -m venv backend\venv
.\backend\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
$env:PYTHONPATH = ".;./backend"
$env:DATABASE_URL = "sqlite:///./hospital_demo.db"
python scripts\seed_database.py
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
Set-Location frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`. The API docs are at `http://127.0.0.1:8000/docs`.

`seed_database.py` resets the database selected by `DATABASE_URL`; use a dedicated demo database as shown above. To use only the terminal interface, skip both servers and run from the repository root:

```powershell
$env:PYTHONPATH = ".;./backend"
$env:DATABASE_URL = "sqlite:///./hospital_demo.db"
python -m backend.app.cli
```

The CLI and web application use the same `SimulationService`, agents, coordinator, schema and resource algorithms when configured with the same `DATABASE_URL`.

## Tests and Evaluation

From the repository root:

```powershell
$env:PYTHONPATH = ".;./backend"
python -m pytest -q backend/tests
python scripts\evaluate_baseline.py
```

The latest full test run passed 44 tests before the current final UI pass; run the command above to verify the final count. Pytest uses a temporary SQLite database by default. If overriding `DATABASE_URL`, point it to a dedicated test database, never the application database.

The evaluator runs five fixed seeds at each cohort size (5 and 20). Each seed is generated once and replayed with identical patients, arrivals, resource capacities, and processing durations under both policies. The current means are:

| Workload | Policy | Mean wait | P1 doctor wait | P2 doctor wait | P3 doctor wait | P4 doctor wait | Assignments | Delayed | Conflicts | Completion |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 patients | FIFO | 0.87 min | 1.18 min | 0.00 min | 0.00 min | 0.00 min | 14 | 0 | 2.0 | 100% |
| 5 patients | Priority-aware | 0.87 min | 1.18 min | 0.00 min | 0.00 min | 0.00 min | 14 | 0 | 2.0 | 100% |
| 20 patients | FIFO | 3.08 min | 3.72 min | 7.51 min | 0.07 min | 0.15 min | 59.2 | 0 | 37.4 | 100% |
| 20 patients | Priority-aware | 3.07 min | 3.22 min | 8.51 min | 0.07 min | 0.15 min | 59.2 | 0 | 36.4 | 100% |

These are descriptive outcomes for the generated workloads, not clinical or real-world performance claims. Per-seed values, variability, and paired patient/resource fingerprints are recorded in [backend/app/simulation/baseline_results.json](backend/app/simulation/baseline_results.json).

## Project Files

- [Project report](docs/project_report.md): Introduction, PEAS Description, Agent and Environment Analysis, Design, Implementation, and Testing and Results.
- [Architecture](docs/architecture.md): agent responsibilities, communication, workflow, and deterministic selection rules.
- [Testing results](docs/testing_results.md): current run summary and historical test matrix.
- [Implementation status](docs/implementation_status.md): phase progress, environment, measured results, and acceptance state.
- [Screenshots](docs/screenshots/): existing dashboard screenshots.
