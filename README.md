# Smart Hospital Emergency Response System Using Multi-Agent AI

An autonomous, cooperative **Multi-Agent Artificial Intelligence System (MAS)** simulating an intelligent hospital emergency department to coordinate ambulances, physicians, diagnostic equipment, and intensive care beds under resource scarcity.

Developed as a B.Tech Computer Science and Engineering Artificial Intelligence capstone project.

---

## 🌟 Key Features

- **Cooperative Multi-Agent Architecture:** Six distinct software agents with explicit PEAS profiles:
  - **Hospital Coordinator:** Global patient workflow orchestrator and queue manager.
  - **Triage Agent:** Deterministic rule-based priority categorization (P1 Critical, P2 High, P3 Moderate, P4 Low).
  - **Ambulance Agent:** Utility-ranked dispatch with distance penalties and advanced life support matching.
  - **Doctor Agent:** Specialty constraint filtering and workload balancing across clinical staff.
  - **Diagnostic Agent:** Equipment queue scheduler for CT, MRI, X-Ray, Ultrasound, and Blood Lab.
  - **ICU Agent:** Critical care bed allocation with ventilator capability prioritization.
- **Zero External AI Dependencies:** 100% locally runnable rule-based and utility-ranked AI system; zero API keys, paid subscriptions, or cloud inference required.
- **Discrete-Event Simulation (DES):** Min-heap event queue running simulated clinical milestones with fixed-seed reproducibility.
- **Empirical Baseline Comparison:** Side-by-side benchmarking comparing the **Priority-Aware MAS** against a conventional **First-In, First-Out (FIFO)** scheduling baseline across multiple workload cohorts.
- **Interactive Web Dashboard:** High-tech dark-mode dashboard built with React 18, Vite 5, Lucide icons, and Recharts.
- **Comprehensive Test Suite:** 29 automated tests covering unit logic, integration messaging, state machines, and REST API endpoints.

---

## 🏗️ Project Architecture

```
AEG Hospital/
├── backend/
│   ├── app/
│   │   ├── agents/            # Specialized intelligent agents
│   │   │   ├── base_agent.py
│   │   │   ├── triage_agent.py
│   │   │   ├── ambulance_agent.py
│   │   │   ├── doctor_agent.py
│   │   │   ├── diagnostic_agent.py
│   │   │   └── icu_agent.py
│   │   ├── coordinator/       # Master Coordinator
│   │   │   └── hospital_coordinator.py
│   │   ├── simulation/        # Discrete-event engine, scenarios & metrics
│   │   │   ├── engine.py
│   │   │   ├── events.py
│   │   │   ├── scenarios.py
│   │   │   ├── metrics.py
│   │   │   └── baseline_results.json
│   │   ├── workflows/         # Finite State Machine transition validator
│   │   │   └── patient_workflow.py
│   │   ├── models/            # SQLAlchemy ORM models and enums
│   │   │   ├── entities.py
│   │   │   └── enums.py
│   │   ├── schemas/           # Pydantic validation schemas
│   │   │   └── hospital_schemas.py
│   │   ├── database/          # Database engine and session
│   │   │   ├── session.py
│   │   │   └── init_db.py
│   │   ├── services/          # State management service
│   │   │   └── simulation_service.py
│   │   ├── api/               # FastAPI REST endpoints
│   │   │   └── routes.py
│   │   └── main.py            # FastAPI entry point with CORS & Lifespan
│   ├── tests/                 # 29 automated pytest test suites
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # Navbar and intake modal
│   │   ├── pages/             # 5 dashboard pages
│   │   │   ├── OverviewPage.jsx
│   │   │   ├── PatientQueuePage.jsx
│   │   │   ├── AgentMonitorPage.jsx
│   │   │   ├── EventTimelinePage.jsx
│   │   │   └── MetricsPage.jsx
│   │   ├── services/          # Axios API client
│   │   ├── App.jsx
│   │   └── index.css          # Design system & dark mode tokens
│   ├── package.json
│   └── index.html
├── scripts/
│   ├── seed_database.py       # Seed SQLite demonstration scenario
│   ├── run_simulation.py      # Standalone CLI simulation script
│   ├── evaluate_baseline.py   # FIFO vs Priority-Aware benchmark evaluator
│   └── capture_screenshots.ps1# Genuine screenshot capture automation
├── docs/
│   ├── project_report.md      # Full 6-section academic report
│   ├── architecture.md        # Technical design & Mermaid diagrams
│   ├── testing_results.md     # Test execution matrix (29/29 passed)
│   ├── implementation_status.md # Phase-by-phase implementation log
│   └── screenshots/           # 8 genuine application screenshots
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start Guide (Windows)

### Prerequisites
- Python 3.11 or later (`python --version`)
- Node.js v20.x or later and npm (`node --version`, `npm --version`)

---

### Step 1: Set Up Backend Virtual Environment
Open PowerShell in the project directory:

```powershell
# Create virtual environment in backend/venv
python -m venv backend\venv

# Activate virtual environment
.\backend\venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend\requirements.txt
```

---

### Step 2: Initialize Database and Seed Scenario
```powershell
$env:PYTHONPATH = ".;./backend"
python scripts\seed_database.py
```
*Output: Successfully seeded 3 ambulances, 4 doctors, 5 diagnostic resources, 3 ICU beds, and 5 synthetic emergency patients.*

---

### Step 3: Start the FastAPI Backend Server
```powershell
$env:PYTHONPATH = ".;./backend"
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/api/health`

---

### Step 4: Start the Frontend Dashboard
Open a second PowerShell terminal in the project directory:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```
- Open your browser to: **`http://127.0.0.1:5173`**

---

### Step 5: Run Automated Tests
```powershell
$env:PYTHONPATH = ".;./backend"
.\backend\venv\Scripts\pytest -v backend\tests
```
*Result: 29 passed out of 29 in ~1.7 seconds.*

---

### Step 6: Run Standalone CLI Demonstration
To run the simulation and view the event timeline directly in the terminal:
```powershell
$env:PYTHONPATH = ".;./backend"
python scripts\run_simulation.py
```

To run the comparative empirical evaluation comparing FIFO vs Priority-Aware:
```powershell
$env:PYTHONPATH = ".;./backend"
python scripts\evaluate_baseline.py
```

---

## 📊 Empirical Evaluation Summary

| Workload Cohort | Strategy | Critical (P1) Wait to Doctor | Low Severity (P4) Wait to Doctor | Total Conflicts | Workflows Completed |
|---|---|---|---|---|---|
| **Workload 5** | FIFO | 0.00 mins | 0.00 mins | 4 | 5 / 5 (100%) |
| **Workload 5** | Priority MAS | 0.00 mins | 0.00 mins | 4 | 5 / 5 (100%) |
| **Workload 20** | FIFO | **38.09 mins** | 33.08 mins | 44 | 20 / 20 (100%) |
| **Workload 20** | Priority MAS | **27.37 mins (-28.1%)** | 42.44 mins (+28.3%) | 60 | 20 / 20 (100%) |

**Core Finding:** In congested scenarios, the **Priority-Aware Multi-Agent System reduces critical patient waiting times by 28.1%** while maintaining a 100% completion rate.

---

## 📸 Screenshots

Genuine screenshots of the running dashboard are located in [`docs/screenshots/`](file:///c:/Users/kmani/Desktop/AEG%20Hospital/docs/screenshots/):
1. [`01_dashboard_before_simulation.png`](file:///c:/Users/kmani/Desktop/AEG%20Hospital/docs/screenshots/01_dashboard_before_simulation.png): Command Center Overview
2. [`02_patient_queue_priorities.png`](file:///c:/Users/kmani/Desktop/AEG%20Hospital/docs/screenshots/02_patient_queue_priorities.png): Patient Urgency Queue
3. [`03_agent_monitor.png`](file:///c:/Users/kmani/Desktop/AEG%20Hospital/docs/screenshots/03_agent_monitor.png): Multi-Agent Live Monitor with PEAS specifications
4. [`04_event_timeline.png`](file:///c:/Users/kmani/Desktop/AEG%20Hospital/docs/screenshots/04_event_timeline.png): Event & Message Timeline
5. [`05_resource_conflict.png`](file:///c:/Users/kmani/Desktop/AEG%20Hospital/docs/screenshots/05_resource_conflict.png): Resource Contention & Waiting Queues
6. [`06_resource_release.png`](file:///c:/Users/kmani/Desktop/AEG%20Hospital/docs/screenshots/06_resource_release.png): Resource Release & Workflow Progression
7. [`07_metrics_completed.png`](file:///c:/Users/kmani/Desktop/AEG%20Hospital/docs/screenshots/07_metrics_completed.png): Quantitative KPIs & Utilization Radars
8. [`08_fifo_comparison_charts.png`](file:///c:/Users/kmani/Desktop/AEG%20Hospital/docs/screenshots/08_fifo_comparison_charts.png): Empirical FIFO vs Priority MAS Comparison

---

## 📄 Academic Documentation

- **Full Project Report:** [`docs/project_report.md`](file:///c:/Users/kmani/Desktop/AEG%20Hospital/docs/project_report.md)
- **Technical Architecture:** [`docs/architecture.md`](file:///c:/Users/kmani/Desktop/AEG%20Hospital/docs/architecture.md)
- **Automated Test Report:** [`docs/testing_results.md`](file:///c:/Users/kmani/Desktop/AEG%20Hospital/docs/testing_results.md)
- **Implementation Status:** [`docs/implementation_status.md`](file:///c:/Users/kmani/Desktop/AEG%20Hospital/docs/implementation_status.md)
