"""
Database initialization and reset functions.
"""
from sqlalchemy import inspect, text
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
    """Create tables and apply additive SQLite columns for existing local databases."""
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "sqlite":
        additions = {
            "patients": {
                "emergency_type": "VARCHAR(100)",
                "chief_complaint": "VARCHAR(255)",
                "symptoms": "TEXT",
                "heart_rate": "INTEGER",
                "oxygen_saturation": "FLOAT",
                "blood_pressure": "VARCHAR(32)",
                "triage_mode": "VARCHAR(20) NOT NULL DEFAULT 'AUTO'",
                "triage_reason": "VARCHAR(500)",
                "triage_requires_review": "BOOLEAN NOT NULL DEFAULT 0",
                "required_equipment": "VARCHAR(255) NOT NULL DEFAULT ''",
                "required_icu_equipment": "VARCHAR(255) NOT NULL DEFAULT ''",
                "requires_ventilator": "BOOLEAN NOT NULL DEFAULT 0",
                "decision_trace_json": "TEXT NOT NULL DEFAULT '[]'",
            },
            "icu_beds": {"has_monitoring": "BOOLEAN NOT NULL DEFAULT 1"},
        }
        inspector = inspect(engine)
        with engine.begin() as connection:
            for table_name, columns in additions.items():
                if table_name not in inspector.get_table_names():
                    continue
                current_columns = {
                    column["name"] for column in inspector.get_columns(table_name)
                }
                for column_name, declaration in columns.items():
                    if column_name not in current_columns:
                        connection.execute(
                            text(
                                f"ALTER TABLE {table_name} ADD COLUMN "
                                f"{column_name} {declaration}"
                            )
                        )


def reset_db():
    """Drop and recreate all tables for a clean slate."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
