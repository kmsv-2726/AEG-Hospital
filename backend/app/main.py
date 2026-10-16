"""
Smart Hospital Emergency Response System - Backend Main API Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
from backend.app.api.routes import router
from backend.app.services.simulation_service import sim_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize simulation engine and database on startup
    sim_service.initialize()
    yield


app = FastAPI(
    title="Smart Hospital Emergency Response System API",
    description="Multi-Agent AI Simulation for Emergency Hospital Coordination",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend Vite dev server (default port 5173) and any local origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
