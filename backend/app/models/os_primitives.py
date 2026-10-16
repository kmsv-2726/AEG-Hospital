"""
Operating System (OS) Primitives for Hospital Multi-Agent Emergency System.
Implements:
- Process Control Block (Patient PCB)
- Process States (NEW, READY, RUNNING, BLOCKED, TERMINATED)
- Resource Mutexes & Counting Semaphores (ICU Beds, Doctors, Scanners, Ambulances)
- Multi-Level Priority Scheduler with Dynamic Aging to Prevent Starvation
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ProcessState(str, Enum):
    NEW = "NEW"                  # Patient registered, awaiting triage
    READY = "READY"              # Triaged, waiting in ready queue for physician/resource
    RUNNING = "RUNNING"          # Currently executing (in doctor consultation / scan / treatment)
    BLOCKED = "BLOCKED"          # Waiting for scarce resource (Doctor, Scanner, ICU bed)
    TERMINATED = "TERMINATED"    # Treatment completed, discharged


class PatientPCB(BaseModel):
    """
    Process Control Block (PCB) representing a patient as an OS process.
    Tracks execution times, burst times, state transitions, and held resources.
    """
    pid: str = Field(..., description="Process ID / Patient ID, e.g. P101")
    patient_name: str
    base_priority: str = "P3"            # P1 (Real-Time), P2 (High), P3 (Normal), P4 (Low)
    numeric_priority: int = 3           # 1 (highest) to 4 (lowest)
    dynamic_priority: float = 3.0       # Dynamically adjusted priority with aging
    state: ProcessState = ProcessState.NEW
    
    # OS Execution Timestamps (in simulated minutes)
    arrival_time: float = 0.0
    cpu_burst_time: float = 10.0        # Doctor examination & medical procedure duration
    io_burst_time: float = 0.0          # Diagnostic scan / lab duration
    mem_burst_time: float = 0.0         # ICU critical bed stay duration
    
    start_execution_time: Optional[float] = None
    completion_time: Optional[float] = None
    total_waiting_time: float = 0.0
    last_state_change_time: float = 0.0
    
    # Resource Locks held / requested
    allocated_resources: List[str] = Field(default_factory=list)
    waiting_for_resource: Optional[str] = None
    
    # OS Metric getters
    @property
    def turnaround_time(self) -> Optional[float]:
        if self.completion_time is not None:
            return max(0.0, self.completion_time - self.arrival_time)
        return None

    @property
    def response_time(self) -> Optional[float]:
        if self.start_execution_time is not None:
            return max(0.0, self.start_execution_time - self.arrival_time)
        return None

    def update_state(self, new_state: ProcessState, current_time: float, resource: Optional[str] = None):
        """Advance PCB state and accumulate waiting/blocked time."""
        time_in_prev_state = max(0.0, current_time - self.last_state_change_time)
        if self.state in (ProcessState.READY, ProcessState.BLOCKED):
            self.total_waiting_time += time_in_prev_state

        self.state = new_state
        self.last_state_change_time = current_time

        if new_state == ProcessState.RUNNING and self.start_execution_time is None:
            self.start_execution_time = current_time

        if new_state == ProcessState.TERMINATED:
            self.completion_time = current_time

        if resource:
            if new_state == ProcessState.RUNNING and resource not in self.allocated_resources:
                self.allocated_resources.append(resource)
                self.waiting_for_resource = None
            elif new_state == ProcessState.BLOCKED:
                self.waiting_for_resource = resource

    def apply_aging(self, current_time: float, aging_rate: float = 0.05):
        """
        OS Aging Mechanism:
        Reduces dynamic_priority (closer to 1.0) the longer a process sits in READY/BLOCKED,
        preventing starvation of low-priority (P3/P4) patients.
        """
        if self.state in (ProcessState.READY, ProcessState.BLOCKED):
            wait = max(0.0, current_time - self.last_state_change_time)
            # Dynamic priority improves (decreases toward 1) with time
            self.dynamic_priority = max(1.0, float(self.numeric_priority) - (wait * aging_rate))


class CountingSemaphore:
    """
    OS Counting Semaphore for pool resources (e.g. ICU Beds, Ambulances).
    Atomic acquire and release with priority-aware waiting queue.
    """
    def __init__(self, name: str, capacity: int):
        self.name = name
        self.capacity = capacity
        self.value = capacity
        self.holders: Dict[str, str] = {}  # pid -> resource_unit_id
        self.wait_queue: List[str] = []     # List of pids blocked on this semaphore

    def acquire(self, pid: str, unit_id: str) -> bool:
        """Attempt to acquire a permit. Returns True if granted, False if blocked."""
        if self.value > 0 and pid not in self.holders:
            self.value -= 1
            self.holders[pid] = unit_id
            if pid in self.wait_queue:
                self.wait_queue.remove(pid)
            return True
        else:
            if pid not in self.wait_queue and pid not in self.holders:
                self.wait_queue.append(pid)
            return False

    def release(self, pid: str) -> Optional[str]:
        """Release a permit held by pid. Returns the released unit_id if any."""
        if pid in self.holders:
            unit_id = self.holders.pop(pid)
            self.value = min(self.capacity, self.value + 1)
            return unit_id
        return None

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "capacity": self.capacity,
            "available_permits": self.value,
            "allocated_permits": self.capacity - self.value,
            "utilization_pct": round(((self.capacity - self.value) / max(1, self.capacity)) * 100, 1),
            "holders": dict(self.holders),
            "blocked_count": len(self.wait_queue),
            "blocked_pids": list(self.wait_queue),
        }


class ResourceMutex:
    """
    OS Mutual Exclusion (Mutex) Lock for exclusive resources (individual doctors, scanners).
    """
    def __init__(self, resource_id: str, resource_type: str, name: str):
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.name = name
        self.is_locked = False
        self.current_owner: Optional[str] = None
        self.wait_queue: List[str] = []
        self.total_acquisitions = 0
        self.total_lock_time = 0.0
        self.locked_at: Optional[float] = None

    def acquire(self, pid: str, current_time: float) -> bool:
        """Lock mutex for pid."""
        if not self.is_locked:
            self.is_locked = True
            self.current_owner = pid
            self.locked_at = current_time
            self.total_acquisitions += 1
            if pid in self.wait_queue:
                self.wait_queue.remove(pid)
            return True
        else:
            if pid not in self.wait_queue and self.current_owner != pid:
                self.wait_queue.append(pid)
            return False

    def release(self, pid: str, current_time: float) -> bool:
        """Unlock mutex held by pid."""
        if self.is_locked and self.current_owner == pid:
            if self.locked_at is not None:
                self.total_lock_time += max(0.0, current_time - self.locked_at)
            self.is_locked = False
            self.current_owner = None
            self.locked_at = None
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "name": self.name,
            "is_locked": self.is_locked,
            "current_owner": self.current_owner,
            "blocked_count": len(self.wait_queue),
            "blocked_pids": list(self.wait_queue),
            "total_acquisitions": self.total_acquisitions,
            "total_lock_time": round(self.total_lock_time, 1),
        }


class HospitalOSManager:
    """
    Master OS Resource & Process Manager.
    Manages:
    - Patient PCBs (Processes)
    - Ready Queue (processes awaiting CPU/Doctor)
    - Blocked Queues (processes blocked on semaphores/mutexes)
    - Semaphores (ICU beds, Ambulances)
    - Mutexes (Specialty Doctors, Diagnostic Scanners)
    - CPU/Doctor Duty Cycle & Utilization Monitoring
    """
    def __init__(self):
        self.pcbs: Dict[str, PatientPCB] = {}
        self.ready_queue: List[str] = []
        
        # OS Semaphores
        self.icu_semaphore = CountingSemaphore("ICU_Beds_Semaphore", capacity=3)
        self.ambulance_semaphore = CountingSemaphore("Ambulance_Fleet_Semaphore", capacity=3)
        
        # OS Mutexes
        self.doctor_mutexes: Dict[str, ResourceMutex] = {}
        self.diagnostic_mutexes: Dict[str, ResourceMutex] = {}

    def register_patient_process(self, patient_dict: Dict[str, Any], current_time: float) -> PatientPCB:
        """Initialize and register a new Process Control Block for a patient."""
        pid = patient_dict["id"]
        priority_str = patient_dict.get("priority", "P3")
        num_prio = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}.get(priority_str, 3)
        
        # Diagnostic & ICU burst times
        io_burst = 15.0 if patient_dict.get("required_diagnostic") else 0.0
        mem_burst = 20.0 if patient_dict.get("requires_icu") else 0.0
        cpu_burst = 15.0 if priority_str in ("P1", "P2") else 10.0

        pcb = PatientPCB(
            pid=pid,
            patient_name=patient_dict.get("name", "Unknown"),
            base_priority=priority_str,
            numeric_priority=num_prio,
            dynamic_priority=float(num_prio),
            state=ProcessState.NEW,
            arrival_time=current_time,
            cpu_burst_time=cpu_burst,
            io_burst_time=io_burst,
            mem_burst_time=mem_burst,
            last_state_change_time=current_time,
        )
        self.pcbs[pid] = pcb
        return pcb

    def sync_resources(self, doctors: List[Dict[str, Any]], diagnostics: List[Dict[str, Any]], icu_beds: List[Dict[str, Any]], ambulances: List[Dict[str, Any]]):
        """Synchronize OS mutexes and semaphores with environment resources."""
        # Update semaphore capacities
        self.icu_semaphore.capacity = len(icu_beds)
        self.ambulance_semaphore.capacity = len(ambulances)

        # Register doctor mutexes
        for d in doctors:
            if d["id"] not in self.doctor_mutexes:
                self.doctor_mutexes[d["id"]] = ResourceMutex(
                    resource_id=d["id"],
                    resource_type=f"Doctor ({d.get('specialty', 'General')})",
                    name=d.get("name", d["id"]),
                )

        # Register diagnostic mutexes
        for diag in diagnostics:
            if diag["id"] not in self.diagnostic_mutexes:
                self.diagnostic_mutexes[diag["id"]] = ResourceMutex(
                    resource_id=diag["id"],
                    resource_type=f"Scanner ({diag.get('category', 'Imaging')})",
                    name=diag.get("name", diag["id"]),
                )

    def transition_process(self, pid: str, new_state: ProcessState, current_time: float, resource: Optional[str] = None):
        """Safely transition a patient PCB and maintain Ready Queue."""
        pcb = self.pcbs.get(pid)
        if not pcb:
            return

        pcb.update_state(new_state, current_time, resource)

        if new_state == ProcessState.READY:
            if pid not in self.ready_queue:
                self.ready_queue.append(pid)
        else:
            if pid in self.ready_queue:
                self.ready_queue.remove(pid)

    def apply_aging(self, current_time: float):
        """Run OS aging sweep over all registered PCBs."""
        for pcb in self.pcbs.values():
            pcb.apply_aging(current_time)

        # Sort ready queue by dynamic priority (lowest number = highest priority)
        self.ready_queue.sort(key=lambda pid: (self.pcbs[pid].dynamic_priority, self.pcbs[pid].arrival_time))

    def get_os_metrics(self, current_time: float) -> Dict[str, Any]:
        """Aggregate OS utilization, scheduling queues, and PCB summaries."""
        self.apply_aging(current_time)
        
        state_counts = {state.value: 0 for state in ProcessState}
        completed_pcbs = []
        for pcb in self.pcbs.values():
            state_counts[pcb.state.value] += 1
            if pcb.state == ProcessState.TERMINATED:
                completed_pcbs.append(pcb)

        avg_turnaround = (
            sum(p.turnaround_time for p in completed_pcbs if p.turnaround_time is not None) / len(completed_pcbs)
            if completed_pcbs else 0.0
        )
        avg_wait = (
            sum(p.total_waiting_time for p in self.pcbs.values()) / max(1, len(self.pcbs))
        )

        # Active Doctor utilization
        busy_doctors = sum(1 for m in self.doctor_mutexes.values() if m.is_locked)
        doc_util = round((busy_doctors / max(1, len(self.doctor_mutexes))) * 100, 1) if self.doctor_mutexes else 0.0

        # Active Scanner utilization
        busy_scanners = sum(1 for m in self.diagnostic_mutexes.values() if m.is_locked)
        scan_util = round((busy_scanners / max(1, len(self.diagnostic_mutexes))) * 100, 1) if self.diagnostic_mutexes else 0.0

        return {
            "process_counts": state_counts,
            "total_processes": len(self.pcbs),
            "ready_queue_length": len(self.ready_queue),
            "ready_queue_pids": list(self.ready_queue),
            "average_turnaround_time": round(avg_turnaround, 2),
            "average_waiting_time": round(avg_wait, 2),
            "doctor_cpu_utilization_pct": doc_util,
            "diagnostic_io_utilization_pct": scan_util,
            "icu_semaphore": self.icu_semaphore.get_status(),
            "ambulance_semaphore": self.ambulance_semaphore.get_status(),
            "doctor_mutexes": [m.get_status() for m in self.doctor_mutexes.values()],
            "diagnostic_mutexes": [m.get_status() for m in self.diagnostic_mutexes.values()],
            "pcbs": [p.model_dump() for p in self.pcbs.values()],
        }
