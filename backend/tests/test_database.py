"""
Tests for database initialization, persistence, and reset.
"""
from backend.app.database.init_db import reset_db
from backend.app.database.session import SessionLocal
from backend.app.models.entities import (
    AmbulanceModel,
    DoctorModel,
    PatientModel,
    DiagnosticResourceModel,
    ICUBedModel,
)
from scripts.seed_database import seed_hospital


def test_database_seeding_and_counts():
    reset_db()
    db = SessionLocal()
    try:
        seed_hospital(db)
        ambulances = db.query(AmbulanceModel).all()
        doctors = db.query(DoctorModel).all()
        patients = db.query(PatientModel).all()
        diagnostics = db.query(DiagnosticResourceModel).all()
        icu_beds = db.query(ICUBedModel).all()

        assert len(ambulances) == 3
        assert len(doctors) == 4
        assert len(patients) == 5
        assert len(diagnostics) == 5
        assert len(icu_beds) == 3

        # Verify trauma doctor
        trauma_docs = [d for d in doctors if d.specialty == "Trauma"]
        assert len(trauma_docs) == 1
        assert trauma_docs[0].name == "Dr. Marcus Vance"
    finally:
        db.close()


def test_database_reset():
    db = SessionLocal()
    try:
        reset_db()
        assert db.query(PatientModel).count() == 0
        assert db.query(DoctorModel).count() == 0
    finally:
        db.close()
