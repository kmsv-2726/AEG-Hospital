"""
Patient Workflow Finite State Machine and Transition Validator.
"""
from typing import Set, Dict
from backend.app.models.enums import WorkflowState


class WorkflowTransitionError(Exception):
    """Raised when an illegal workflow state transition is attempted."""
    pass


class PatientWorkflowFSM:
    """
    Validates patient progression through the hospital emergency pathway.
    Ensures state machine integrity and logs valid transitions.
    """

    ALLOWED_TRANSITIONS: Dict[WorkflowState, Set[WorkflowState]] = {
        WorkflowState.REGISTERED: {WorkflowState.TRIAGED},
        WorkflowState.TRIAGED: {
            WorkflowState.WAITING_FOR_AMBULANCE,
            WorkflowState.AMBULANCE_ASSIGNED,
            WorkflowState.ARRIVED,
        },
        WorkflowState.WAITING_FOR_AMBULANCE: {
            WorkflowState.AMBULANCE_ASSIGNED,
            WorkflowState.TERMINATED,
        },
        WorkflowState.AMBULANCE_ASSIGNED: {WorkflowState.IN_TRANSIT},
        WorkflowState.IN_TRANSIT: {WorkflowState.ARRIVED},
        WorkflowState.ARRIVED: {WorkflowState.ADMITTED},
        WorkflowState.ADMITTED: {
            WorkflowState.WAITING_FOR_DOCTOR,
            WorkflowState.DOCTOR_ASSIGNED,
        },
        WorkflowState.WAITING_FOR_DOCTOR: {
            WorkflowState.DOCTOR_ASSIGNED,
            WorkflowState.TERMINATED,
        },
        WorkflowState.DOCTOR_ASSIGNED: {
            WorkflowState.WAITING_FOR_DIAGNOSTIC,
            WorkflowState.DIAGNOSTICS_IN_PROGRESS,
            WorkflowState.WAITING_FOR_ICU,
            WorkflowState.ICU_ALLOCATED,
            WorkflowState.TREATMENT_SIMULATED,
        },
        WorkflowState.WAITING_FOR_DIAGNOSTIC: {
            WorkflowState.DIAGNOSTICS_IN_PROGRESS,
            WorkflowState.TERMINATED,
        },
        WorkflowState.DIAGNOSTICS_IN_PROGRESS: {WorkflowState.DIAGNOSTICS_COMPLETED},
        WorkflowState.DIAGNOSTICS_COMPLETED: {
            WorkflowState.WAITING_FOR_ICU,
            WorkflowState.ICU_ALLOCATED,
            WorkflowState.TREATMENT_SIMULATED,
        },
        WorkflowState.WAITING_FOR_ICU: {
            WorkflowState.ICU_ALLOCATED,
            WorkflowState.TERMINATED,
        },
        WorkflowState.ICU_ALLOCATED: {WorkflowState.TREATMENT_SIMULATED},
        WorkflowState.TREATMENT_SIMULATED: {WorkflowState.COMPLETED},
        WorkflowState.COMPLETED: {WorkflowState.DISCHARGED},
        WorkflowState.DISCHARGED: set(),
        WorkflowState.TERMINATED: set(),
    }

    @classmethod
    def can_transition(cls, current_state: WorkflowState, next_state: WorkflowState) -> bool:
        """Check if transition from current_state to next_state is valid."""
        return next_state in cls.ALLOWED_TRANSITIONS.get(current_state, set())

    @classmethod
    def validate_transition(cls, current_state: WorkflowState, next_state: WorkflowState, patient_id: str):
        """Validate transition, raising WorkflowTransitionError if invalid."""
        if not cls.can_transition(current_state, next_state):
            raise WorkflowTransitionError(
                f"Invalid workflow transition for Patient {patient_id}: "
                f"Cannot advance from {current_state.value} to {next_state.value}."
            )
