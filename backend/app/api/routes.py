"""
FastAPI REST API routes for Smart Hospital Multi-Agent Emergency Response System.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.hospital_schemas import (
    PatientCreate,
    PatientRead,
    ResourceSummary,
    AgentStatusRead,
    SimulationEventSchema,
    MetricsSummary,
    SimulationStartRequest,
    SimulationResetRequest,
)
from backend.app.services.simulation_service import sim_service
from backend.app.models.enums import AllocationStrategy

router = APIRouter(prefix="/api", tags=["Hospital Simulation API"])


@router.get("/health", tags=["Health"])
async def health_check():
    """Verify backend API and simulation engine operational readiness."""
    return {
        "status": "healthy",
        "service": "Smart Hospital Multi-Agent System API",
        "version": "1.0.0",
        "simulation_mode": "local_rule_based",
        "external_api_keys_required": False,
    }


@router.get("/patients", response_model=List[PatientRead], tags=["Patients"])
async def list_patients():
    """Retrieve all simulated emergency patients and their current workflow states."""
    return sim_service.get_patients()


@router.post("/patients", response_model=PatientRead, status_code=status.HTTP_201_CREATED, tags=["Patients"])
async def register_patient(patient: PatientCreate):
    """Register a new synthetic emergency patient into the hospital."""
    try:
        created = sim_service.add_emergency_patient(patient)
        return created
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to register patient: {str(e)}")


@router.post("/emergency", response_model=PatientRead, status_code=status.HTTP_201_CREATED, tags=["Emergency"])
async def submit_emergency(patient: PatientCreate):
    """Submit a high-priority synthetic emergency incident triggering immediate agent dispatch."""
    return sim_service.add_emergency_patient(patient)


@router.get("/resources", response_model=ResourceSummary, tags=["Resources"])
async def get_resources():
    """Retrieve current availability of ambulances, doctors, diagnostic equipment, and ICU beds."""
    return sim_service.get_resources()


@router.get("/agents", response_model=List[AgentStatusRead], tags=["Agents"])
async def get_agents():
    """Retrieve active status, last actions, and messages for all specialized agents and Coordinator."""
    return sim_service.get_agents()


@router.get("/events", response_model=List[SimulationEventSchema], tags=["Events"])
async def get_events():
    """Retrieve chronological event and conflict log generated during simulation."""
    return sim_service.get_events()


@router.post("/simulation/start", response_model=MetricsSummary, tags=["Simulation"])
async def start_simulation(request: SimulationStartRequest = SimulationStartRequest()):
    """Run discrete-event multi-agent simulation with selected strategy (FIFO or PRIORITY_AWARE)."""
    return sim_service.start_simulation(strategy=request.strategy)


@router.post("/simulation/reset", tags=["Simulation"])
async def reset_simulation(request: SimulationResetRequest = SimulationResetRequest()):
    """Reset simulation state and re-seed the standard demonstration emergency scenario."""
    sim_service.reset_simulation()
    return {
        "status": "RESET_SUCCESSFUL",
        "message": "Hospital state and database restored to baseline demonstration scenario.",
    }


@router.get("/metrics", response_model=MetricsSummary, tags=["Evaluation"])
async def get_metrics():
    """Retrieve current performance metrics including wait times, utilization, and completion rate."""
    return sim_service.get_metrics()


@router.get("/baseline", tags=["Evaluation"])
async def get_baseline_comparison():
    """Retrieve empirical baseline comparison data between FIFO and Priority-Aware strategies."""
    data = sim_service.get_baseline_comparison()
    if not data:
        raise HTTPException(status_code=404, detail="Baseline evaluation data not yet generated.")
    return data
