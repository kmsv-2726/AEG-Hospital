import React, { useEffect, useState } from 'react';
import { Activity, Bot, Cpu, Network, ShieldCheck, Stethoscope } from 'lucide-react';
import { EmptyState, PageHeader, SectionTitle } from '../components/OperationsUI';

const agentIcons = {
  HospitalCoordinator: Network,
  TriageAgent: ShieldCheck,
  AmbulanceAgent: Activity,
  DoctorAgent: Stethoscope,
  DiagnosticAgent: Cpu,
  ICUAgent: Activity,
};

export default function AgentMonitorPage({ agents = [], resources, osStatus, messages = [], onViewOrchestration, patients = [] }) {
  const [activeTab, setActiveTab] = useState('trace');
  const patientsWithTrace = patients.filter((patient) => patient.decision_trace?.length);
  const [selectedPatientId, setSelectedPatientId] = useState(patientsWithTrace[0]?.id || '');

  useEffect(() => {
    if (!patientsWithTrace.some((patient) => patient.id === selectedPatientId)) {
      setSelectedPatientId(patientsWithTrace[0]?.id || '');
    }
  }, [patients, selectedPatientId]);

  const selectedPatient = patients.find((patient) => patient.id === selectedPatientId);
  const trace = selectedPatient?.decision_trace || [];
  const tabs = [
    ['trace', 'Patient execution'],
    ['agents', 'Agent status'],
    ['messages', `Messages (${messages.length})`],
    ['os', 'Resource locks'],
  ];

  return (
    <div className="page-stack">
      <PageHeader eyebrow="COORDINATION AND DECISION AUDIT" title="Agent monitor" description="Inspect recorded agent results and live resource ownership." />
      <div className="monitor-tabs" role="tablist" aria-label="Agent monitor views">
        {tabs.map(([id, label]) => <button key={id} role="tab" aria-selected={activeTab === id} className={`filter-chip ${activeTab === id ? 'is-active' : ''}`} onClick={() => setActiveTab(id)}>{label}</button>)}
      </div>

      {activeTab === 'trace' && (
        <section className="page-section">
          <div className="trace-toolbar">
            <label className="inline-select">Patient execution
              <select value={selectedPatientId} onChange={(event) => setSelectedPatientId(event.target.value)}>
                {patientsWithTrace.map((patient) => <option key={patient.id} value={patient.id}>{patient.id} · {patient.name}</option>)}
              </select>
            </label>
            {selectedPatient && <span className={`status-pill ${selectedPatient.workflow_state?.startsWith('WAITING_') ? 'is-waiting' : ''}`}>{selectedPatient.workflow_state}</span>}
            {selectedPatient && <button className="text-button" onClick={() => onViewOrchestration(selectedPatient)}>Open full trace</button>}
          </div>
          {trace.length === 0 ? <EmptyState title="No patient trace available" description="Register an emergency to record triage, agent activation, candidate ranking, and reservation outcomes." /> : (
            <div className="decision-list">
              {trace.map((entry) => {
                const Icon = agentIcons[entry.agent] || Bot;
                const candidates = entry.details?.candidates || [];
                return (
                  <article className="trace-entry" key={`${entry.sequence}-${entry.agent}-${entry.action}`}>
                    <div className="trace-entry-index">{String(entry.sequence).padStart(2, '0')}</div>
                    <div className="trace-entry-content">
                      <div className="trace-entry-heading"><Icon size={16} /><strong>{entry.agent}</strong><span>{entry.action}</span><span className={`trace-status trace-status-${String(entry.status).toLowerCase().replaceAll('_', '-')}`}>{entry.status}</span><time>{Number(entry.simulation_time || 0).toFixed(1)}m</time></div>
                      <p>{entry.description}</p>
                      {candidates.length > 0 && <div className="candidate-table-wrap"><table className="data-table candidate-table">
                        <thead><tr><th>Rank</th><th>Candidate</th><th>Eligibility</th><th>Score / estimate</th><th>Reason</th></tr></thead>
                        <tbody>{candidates.map((candidate) => <tr key={candidate.resource_id}>
                          <td>{candidate.rank ?? '—'}</td><td>{candidate.resource_id}</td><td>{candidate.eligible ? 'Eligible' : 'Rejected'}</td>
                          <td>{candidate.score ?? candidate.estimated_completion_minutes ?? '—'}</td>
                          <td>{candidate.rejection_reasons?.join(', ') || (candidate.eligible ? 'Passed capability and availability checks' : 'Not eligible')}</td>
                        </tr>)}</tbody>
                      </table></div>}
                      {entry.details && !candidates.length && Object.keys(entry.details).length > 0 && <details className="trace-inputs"><summary>Decision inputs</summary><pre className="trace-json">{JSON.stringify(entry.details, null, 2)}</pre></details>}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      )}

      {activeTab === 'agents' && (
        <section className="page-section">
          <SectionTitle title="Current agent state" description="Live status fields returned by the backend." />
          {agents.length === 0 ? <EmptyState title="Agent state unavailable" description="The backend has not returned agent status." /> : <div className="agent-status-list">
            {agents.map((agent) => {
              const Icon = agentIcons[agent.name] || Bot;
              return <article className="agent-status-row" key={agent.name}>
                <span className="agent-icon"><Icon size={18} /></span>
                <div className="agent-status-main"><strong>{agent.name}</strong><span>{agent.role}</span><small>{agent.last_action || 'No action recorded in this process.'}</small></div>
                <div className="agent-status-meta"><span className="status-pill is-active">{agent.status}</span><small>{agent.active_patients?.length || 0} active · {agent.pending_count || 0} pending</small></div>
              </article>;
            })}
          </div>}
        </section>
      )}

      {activeTab === 'messages' && (
        <section className="page-section">
          <SectionTitle title="Structured message log" description="Recorded synchronous coordinator-agent handoffs with correlation IDs." />
          {messages.length === 0 ? <EmptyState title="No messages recorded" description="Agent messages appear when an emergency is processed." /> : <div className="message-table-wrap"><table className="data-table"><thead><tr><th>Sim time</th><th>Patient</th><th>From</th><th>To</th><th>Message</th><th>Status</th></tr></thead><tbody>
            {messages.slice().reverse().map((message) => <tr key={message.message_id}><td>{Number(message.simulation_time || 0).toFixed(1)}m</td><td>{message.patient_id || '—'}</td><td>{message.sender}</td><td>{message.receiver}</td><td>{message.message_type}</td><td><span className="status-pill">{message.status}</span></td></tr>)}
          </tbody></table></div>}
        </section>
      )}

      {activeTab === 'os' && (
        <section className="page-section">
          <SectionTitle title="Resource and process state" description="Current semaphore, mutex and patient-process state from the OS manager." />
          {!osStatus ? <EmptyState title="OS state unavailable" description="The backend has not returned process and resource lock state." /> : <div className="os-grid">
            {[
              ['ICU beds', osStatus.icu_semaphore],
              ['Ambulances', osStatus.ambulance_semaphore],
            ].map(([label, semaphore]) => <div className="os-resource" key={label}><strong>{label}</strong><span>{semaphore?.available_permits ?? 0} free / {semaphore?.capacity ?? 0} total</span><small>{semaphore?.blocked_count ?? 0} waiting</small></div>)}
            <div className="os-resource"><strong>Doctors</strong><span>{osStatus.doctor_mutexes?.filter((item) => !item.is_locked).length || 0} free / {osStatus.doctor_mutexes?.length || 0} total</span><small>{osStatus.doctor_mutexes?.filter((item) => item.is_locked).length || 0} locked</small></div>
            <div className="os-resource"><strong>Diagnostics</strong><span>{osStatus.diagnostic_mutexes?.filter((item) => !item.is_locked).length || 0} free / {osStatus.diagnostic_mutexes?.length || 0} total</span><small>{osStatus.diagnostic_mutexes?.filter((item) => item.is_locked).length || 0} locked</small></div>
          </div>}
          {resources && <div className="live-resource-note">Live capacities: {resources.counts?.ambulances?.total || 0} ambulances · {resources.counts?.doctors?.total || 0} doctors · {resources.counts?.diagnostic_resources?.total || 0} diagnostic units · {resources.counts?.icu_beds?.total || 0} ICU beds.</div>}
        </section>
      )}
    </div>
  );
}