"""
SQLAlchemy ORM models for Smart Hospital Emergency Response System.
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Text
from backend.app.database.session import Base


class PatientModel(Base):
    __tablename__ = "patients"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False, default=40)
    gender = Column(String(20), nullable=False, default="Unknown")
    condition_description = Column(String(255), nullable=False)
    severity_category = Column(String(100), nullable=False)
    priority = Column(String(10), nullable=False, default="P3")  # P1, P2, P3, P4
    workflow_state = Column(String(50), nullable=False, default="REGISTERED")
    arrival_time = Column(Float, nullable=False, default=0.0)

    # Resource requirements and assignments
    requires_ambulance = Column(Boolean, nullable=False, default=True)
    assigned_ambulance_id = Column(String(50), nullable=True)

    required_specialty = Column(String(50), nullable=False, default="General Medicine")
    assigned_doctor_id = Column(String(50), nullable=True)

    required_diagnostic = Column(String(50), nullable=True)
    assigned_diagnostic_id = Column(String(50), nullable=True)

    requires_icu = Column(Boolean, nullable=False, default=False)
    assigned_icu_bed_id = Column(String(50), nullable=True)

    # Tracking simulation timestamps for metrics
    hospital_arrival_time = Column(Float, nullable=True)
    ambulance_dispatch_time = Column(Float, nullable=True)
    doctor_request_time = Column(Float, nullable=True)
    doctor_assignment_time = Column(Float, nullable=True)
    diagnostic_request_time = Column(Float, nullable=True)
    diagnostic_start_time = Column(Float, nullable=True)
    diagnostic_end_time = Column(Float, nullable=True)
    icu_request_time = Column(Float, nullable=True)
    icu_reservation_time = Column(Float, nullable=True)
    treatment_start_time = Column(Float, nullable=True)
    completion_time = Column(Float, nullable=True)
    waiting_duration = Column(Float, nullable=False, default=0.0)


class AmbulanceModel(Base):
    __tablename__ = "ambulances"

    id = Column(String(50), primary_key=True, index=True)
    call_sign = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False, default="AVAILABLE")
    simulated_location = Column(String(100), nullable=False, default="Station Central")
    base_distance_km = Column(Float, nullable=False, default=5.0)
    equipment_capabilities = Column(String(255), nullable=False, default="BLS,ALS")
    current_patient_id = Column(String(50), nullable=True)
    availability_timestamp = Column(Float, nullable=False, default=0.0)
    total_busy_time = Column(Float, nullable=False, default=0.0)
    total_dispatches = Column(Integer, nullable=False, default=0)


class DoctorModel(Base):
    __tablename__ = "doctors"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    specialty = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False, default="AVAILABLE")
    workload_count = Column(Integer, nullable=False, default=0)
    current_patient_id = Column(String(50), nullable=True)
    availability_timestamp = Column(Float, nullable=False, default=0.0)
    total_busy_time = Column(Float, nullable=False, default=0.0)


class DiagnosticResourceModel(Base):
    __tablename__ = "diagnostic_resources"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # CT, MRI, X-Ray, Blood Test, Ultrasound
    status = Column(String(30), nullable=False, default="AVAILABLE")
    queue_length = Column(Integer, nullable=False, default=0)
    simulated_duration = Column(Float, nullable=False, default=15.0)  # minutes
    current_patient_id = Column(String(50), nullable=True)
    availability_timestamp = Column(Float, nullable=False, default=0.0)
    total_busy_time = Column(Float, nullable=False, default=0.0)


class ICUBedModel(Base):
    __tablename__ = "icu_beds"

    id = Column(String(50), primary_key=True, index=True)
    unit_name = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False, default="AVAILABLE")
    has_ventilator = Column(Boolean, nullable=False, default=True)
    current_patient_id = Column(String(50), nullable=True)
    reservation_timestamp = Column(Float, nullable=True)
    release_timestamp = Column(Float, nullable=True)
    total_busy_time = Column(Float, nullable=False, default=0.0)


class AgentMessageModel(Base):
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(50), nullable=False, index=True)
    sender = Column(String(50), nullable=False)
    receiver = Column(String(50), nullable=False)
    message_type = Column(String(50), nullable=False)
    patient_id = Column(String(50), nullable=True, index=True)
    resource_id = Column(String(50), nullable=True)
    simulation_time = Column(Float, nullable=False, default=0.0)
    correlation_id = Column(String(50), nullable=True)
    payload_json = Column(Text, nullable=False, default="{}")
    status = Column(String(30), nullable=False, default="PROCESSED")


class SimulationEventModel(Base):
    __tablename__ = "simulation_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    simulation_time = Column(Float, nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    agent = Column(String(50), nullable=False)
    patient_id = Column(String(50), nullable=True, index=True)
    resource_id = Column(String(50), nullable=True)
    description = Column(String(255), nullable=False)
    outcome = Column(String(50), nullable=False, default="SUCCESS")
    is_conflict = Column(Boolean, nullable=False, default=False)


class SimulationRunModel(Base):
    __tablename__ = "simulation_runs"

    id = Column(String(50), primary_key=True, index=True)
    strategy = Column(String(50), nullable=False, default="PRIORITY_AWARE")
    status = Column(String(30), nullable=False, default="IDLE")
    start_time = Column(Float, nullable=False, default=0.0)
    end_time = Column(Float, nullable=False, default=0.0)
    total_patients = Column(Integer, nullable=False, default=0)
    completed_workflows = Column(Integer, nullable=False, default=0)
    unresolved_requests = Column(Integer, nullable=False, default=0)
    conflict_count = Column(Integer, nullable=False, default=0)
    metrics_json = Column(Text, nullable=False, default="{}")
