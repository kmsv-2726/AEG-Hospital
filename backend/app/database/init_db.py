"""
Database initialization and reset functions.
"""
from backend.app.database.session import engine, Base, SessionLocal
from backend.app.models.entities import (
    PatientModel,
    AmbulanceModel,
    DoctorModel,
    DiagnosticResourceModel,
    ICUBedModel,
    AgentMessageModel,
    SimulationEventModel,
    SimulationRunModel,
)


def init_db():
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)


def reset_db():
    """Drop and recreate all tables for a clean slate."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
