"""
Database seeding script for the Smart Hospital Multi-Agent Emergency System.
Initializes tables and seeds the standard demonstration scenario.
"""
import sys
import os

# Ensure backend is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database.init_db import reset_db
from backend.app.database.session import SessionLocal
from backend.app.models.entities import (
    AmbulanceModel,
    DoctorModel,
    DiagnosticResourceModel,
    ICUBedModel,
    PatientModel,
)
from backend.app.simulation.scenarios import DEMO_RESOURCES, DEMO_PATIENTS


def seed_hospital(db_session=None):
    """Seed the database with standard demonstration resources and patients."""
    owns_session = False
    if db_session is None:
        reset_db()
        db_session = SessionLocal()
        owns_session = True

    try:
        # Seed Ambulances
        for amb in DEMO_RESOURCES["ambulances"]:
            db_session.add(AmbulanceModel(**amb))

        # Seed Doctors
        for doc in DEMO_RESOURCES["doctors"]:
            db_session.add(DoctorModel(**doc))

        # Seed Diagnostic Resources
        for diag in DEMO_RESOURCES["diagnostic_resources"]:
            db_session.add(DiagnosticResourceModel(**diag))

        # Seed ICU Beds
        for bed in DEMO_RESOURCES["icu_beds"]:
            db_session.add(ICUBedModel(**bed))

        # Seed Patients
        for p in DEMO_PATIENTS:
            db_session.add(PatientModel(**p))

        db_session.commit()
        print(f"Successfully seeded {len(DEMO_RESOURCES['ambulances'])} ambulances, "
              f"{len(DEMO_RESOURCES['doctors'])} doctors, "
              f"{len(DEMO_RESOURCES['diagnostic_resources'])} diagnostic resources, "
              f"{len(DEMO_RESOURCES['icu_beds'])} ICU beds, and "
              f"{len(DEMO_PATIENTS)} synthetic emergency patients.")
    finally:
        if owns_session:
            db_session.close()


if __name__ == "__main__":
    seed_hospital()
