import React from 'react';
import { Activity, Ambulance, Bed, Clock3, HeartPulse, Stethoscope, Users } from 'lucide-react';
import { EmptyState, PageHeader, SectionTitle, StatTile } from '../components/OperationsUI';

const terminalStates = new Set(['COMPLETED', 'DISCHARGED', 'TERMINATED']);

const resourceGroups = [
  { key: 'ambulances', label: 'Ambulances', manager: 'Ambulance Agent', icon: Ambulance, utilization: 'ambulance_utilization', tone: 'teal' },
  { key: 'doctors', label: 'Doctors', manager: 'Doctor Allocation Agent', icon: Stethoscope, utilization: 'doctor_utilization', tone: 'blue' },
  { key: 'diagnostic_resources', label: 'Diagnostic equipment', manager: 'Diagnostic Resource Agent', icon: Activity, utilization: 'diagnostic_utilization', tone: 'amber' },
  { key: 'icu_beds', label: 'ICU beds', manager: 'ICU Allocation Agent', icon: Bed, utilization: 'icu_utilization', tone: 'red' },
];

export default function OverviewPage({ patients = [], resources, metrics, strategy, setActiveTab, onViewOrchestration, events = [] }) {
  const highPriority = patients.filter((patient) => ['P1', 'P2'].includes(patient.priority)).length;
  const waiting = patients.filter((patient) => patient.workflow_state?.startsWith('WAITING_')).length;
  const active = patients.filter((patient) => !terminalStates.has(patient.workflow_state)).length;
  const completed = patients.filter((patient) => terminalStates.has(patient.workflow_state)).length;

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="HOSPITAL OPERATIONS · SYNTHETIC WORKLOAD"
        title="Emergency coordination overview"
        description={`Current policy: ${strategy === 'FIFO' ? 'First-in, first-out baseline' : 'Priority-aware resource scheduling'}.`}
        actions={<button className="btn btn-secondary" onClick={() => setActiveTab('patients')}><Users size={15} />Patient queue</button>}
      />

      <div className="stat-grid">
        <StatTile label="Registered patients" value={patients.length} detail={`${active} currently active`} icon={Users} tone="teal" />
        <StatTile label="High-priority cases" value={highPriority} detail="P1 critical and P2 high" icon={HeartPulse} tone="red" />
        <StatTile label="Waiting requests" value={waiting} detail="Waiting on a constrained resource" icon={Clock3} tone="amber" />
        <StatTile label="Completed workflows" value={`${completed}/${patients.length}`} detail={`${metrics?.workflow_completion_rate ?? 0}% completed`} icon={Activity} tone="green" />
      </div>

      <section className="page-section">
        <SectionTitle title="Resource capacity" description="Current availability from the simulation engine; utilization is measured simulated busy time." />
        {resources ? (
          <div className="resource-grid">
            {resourceGroups.map(({ key, label, manager, icon: Icon, utilization, tone }) => {
              const count = resources.counts?.[key] || { available: 0, busy: 0, total: 0 };
              return (
                <article className="resource-tile" key={key}>
                  <div className="resource-tile-heading"><span className={`stat-icon tone-${tone}`}><Icon size={17} /></span><div><h3>{label}</h3><p>{manager}</p></div></div>
                  <div className="resource-count"><strong>{count.available} available</strong><span>{count.busy} busy / {count.total} total</span></div>
                  <div className="resource-progress" aria-label={`${label} availability`}><span style={{ width: count.total ? `${(count.available / count.total) * 100}%` : '0%' }} /></div>
                  <p className="resource-utilization">Measured utilization: {metrics?.[utilization] ?? 0}%</p>
                </article>
              );
            })}
          </div>
        ) : <EmptyState title="Resource state unavailable" description="The backend has not returned current hospital resources." />}
      </section>

      <div className="overview-lower-grid">
        <section className="page-section">
          <SectionTitle title="Patient workflows" description="Current assignments and waiting states from backend patient records." actions={<button className="text-button" onClick={() => setActiveTab('patients')}>View queue</button>} />
          {patients.length === 0 ? <EmptyState title="No patients registered" description="Add a synthetic emergency to start a workflow." /> : (
            <div className="table-wrap">
              <table className="data-table">
                <thead><tr><th>Patient</th><th>Priority</th><th>Status</th><th>Resources</th><th /></tr></thead>
                <tbody>{patients.slice(0, 7).map((patient) => (
                  <tr key={patient.id}>
                    <td><span className="patient-primary">{patient.name}</span><span className="patient-secondary">{patient.id} · {patient.age}y</span></td>
                    <td><span className={`badge-priority-${String(patient.priority).toLowerCase()}`}>{patient.priority}</span></td>
                    <td><span className={`status-pill ${patient.workflow_state?.startsWith('WAITING_') ? 'is-waiting' : terminalStates.has(patient.workflow_state) ? 'is-complete' : 'is-active'}`}>{patient.workflow_state}</span></td>
                    <td className="assigned-resources">{[patient.assigned_ambulance_id, patient.assigned_doctor_id, patient.assigned_diagnostic_id, patient.assigned_icu_bed_id].filter(Boolean).join(' · ') || 'Not assigned'}</td>
                    <td><button className="text-button" onClick={() => onViewOrchestration(patient)}>Trace</button></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
        </section>

        <section className="page-section recent-events">
          <SectionTitle title="Recent activity" description="Latest recorded simulation events." actions={<button className="text-button" onClick={() => setActiveTab('timeline')}>Timeline</button>} />
          {events.length === 0 ? <EmptyState title="No events recorded" description="Events appear here when agents process a patient." /> : (
            <div className="recent-event-list">
              {events.slice(-6).reverse().map((event, index) => (
                <div className="recent-event" key={event.id || `${event.simulation_time}-${index}`}>
                  <span className={`event-marker ${event.is_conflict ? 'event-marker-warning' : ''}`} />
                  <div><strong>{event.event_type}</strong><span>{event.patient_id || 'Hospital'} · {event.agent}</span><small>{event.description}</small></div>
                  <time>{Number(event.simulation_time || 0).toFixed(1)}m</time>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}