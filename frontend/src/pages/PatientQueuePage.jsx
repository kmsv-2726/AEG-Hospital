import React, { useMemo, useState } from 'react';
import { Search, UserPlus, Users } from 'lucide-react';
import { EmptyState, PageHeader, SectionTitle } from '../components/OperationsUI';

export default function PatientQueuePage({ patients = [], onOpenEmergencyModal, onViewOrchestration }) {
  const [priority, setPriority] = useState('ALL');
  const [waitingOnly, setWaitingOnly] = useState(false);
  const [query, setQuery] = useState('');
  const [sortBy, setSortBy] = useState('arrival');

  const filteredPatients = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return patients.filter((patient) => {
      if (priority !== 'ALL' && patient.priority !== priority) return false;
      if (waitingOnly && !patient.workflow_state?.startsWith('WAITING_')) return false;
      if (!normalizedQuery) return true;
      return [patient.id, patient.name, patient.emergency_type, patient.chief_complaint,
        patient.condition_description, patient.required_specialty]
        .some((value) => String(value || '').toLowerCase().includes(normalizedQuery));
    }).sort((left, right) => {
      if (sortBy === 'priority') return String(left.priority).localeCompare(String(right.priority)) || left.arrival_time - right.arrival_time;
      if (sortBy === 'name') return left.name.localeCompare(right.name);
      return left.arrival_time - right.arrival_time || left.id.localeCompare(right.id);
    });
  }, [patients, priority, waitingOnly, query, sortBy]);

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="PATIENT OPERATIONS"
        title="Patient queue"
        description={`${patients.length} registered synthetic cases · ${filteredPatients.length} shown`}
        actions={<button className="btn btn-primary" onClick={onOpenEmergencyModal}><UserPlus size={16} />Add emergency</button>}
      />

      <section className="page-section">
        <div className="queue-toolbar">
          <label className="search-field"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search patient, ID, complaint, specialty" aria-label="Search patients" /></label>
          <label className="inline-select">Priority
            <select value={priority} onChange={(event) => setPriority(event.target.value)}>
              {['ALL', 'P1', 'P2', 'P3', 'P4'].map((value) => <option key={value}>{value}</option>)}
            </select>
          </label>
          <label className="inline-select">Sort by
            <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
              <option value="arrival">Arrival time</option>
              <option value="priority">Priority</option>
              <option value="name">Patient name</option>
            </select>
          </label>
          <button className={`filter-chip ${waitingOnly ? 'is-active' : ''}`} aria-pressed={waitingOnly} onClick={() => setWaitingOnly((value) => !value)}>
            Waiting only
          </button>
        </div>

        <SectionTitle title="Registered cases" description="Assignments and states are read from the backend simulation service." />
        {filteredPatients.length === 0 ? (
          <EmptyState title={patients.length ? 'No matching patients' : 'No patients registered'} description={patients.length ? 'Change a filter or search term.' : 'Add a synthetic emergency to create the first workflow.'} />
        ) : (
          <div className="table-wrap">
            <table className="data-table patient-table">
              <thead><tr><th>Patient</th><th>Priority</th><th>Emergency / complaint</th><th>Status</th><th>Ambulance</th><th>Doctor</th><th>Diagnostic</th><th>ICU</th><th>Arrival</th><th /></tr></thead>
              <tbody>{filteredPatients.map((patient) => {
                const waiting = patient.workflow_state?.startsWith('WAITING_');
                const done = ['COMPLETED', 'DISCHARGED', 'TERMINATED'].includes(patient.workflow_state);
                const resources = [patient.assigned_ambulance_id, patient.assigned_doctor_id, patient.assigned_diagnostic_id, patient.assigned_icu_bed_id].filter(Boolean);
                return (
                  <tr key={patient.id}>
                    <td><span className="patient-primary">{patient.name}</span><span className="patient-secondary">{patient.id} · {patient.age}y · {patient.gender}</span></td>
                    <td><span className={`badge-priority-${String(patient.priority).toLowerCase()}`}>{patient.priority}</span>{patient.triage_requires_review && <small className="review-flag">Review</small>}</td>
                    <td><span className="patient-primary">{patient.emergency_type || patient.severity_category}</span><span className="patient-secondary">{patient.chief_complaint || patient.condition_description || 'No complaint provided'}</span></td>
                    <td><span className={`status-pill ${waiting ? 'is-waiting' : done ? 'is-complete' : 'is-active'}`}>{patient.workflow_state}</span></td>
                    <td>{patient.assigned_ambulance_id || (patient.requires_ambulance ? 'Pending' : 'Walk-in')}</td>
                    <td>{patient.assigned_doctor_id || patient.required_specialty}</td>
                    <td>{patient.assigned_diagnostic_id || patient.required_diagnostic || 'Not required'}</td>
                    <td>{patient.assigned_icu_bed_id || (patient.requires_icu ? 'Waiting / pending' : 'Not required')}</td>
                    <td>{Number(patient.arrival_time || 0).toFixed(1)}m</td>
                    <td><button className="text-button" onClick={() => onViewOrchestration(patient)}>Decision trace</button></td>
                  </tr>
                );
              })}</tbody>
            </table>
          </div>
        )}
        <div className="queue-footnote"><Users size={14} />{filteredPatients.reduce((count, patient) => count + (patient.assigned_doctor_id ? 1 : 0), 0)} doctor assignments · {filteredPatients.reduce((count, patient) => count + (patient.assigned_ambulance_id ? 1 : 0), 0)} ambulance assignments</div>
      </section>
    </div>
  );
}