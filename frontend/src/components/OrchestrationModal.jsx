import React, { useState, useEffect } from 'react';
import { 
  X, 
  Bot, 
  CheckCircle2, 
  Clock, 
  Ambulance, 
  Stethoscope, 
  Activity, 
  Bed, 
  ShieldAlert, 
  Sparkles,
  ArrowRight,
  MessageSquare,
  Cpu,
  Lock,
  Layers
} from 'lucide-react';
import api from '../services/api';

export default function OrchestrationModal({ isOpen, onClose, patient, events = [] }) {
  const [activeView, setActiveView] = useState('pipeline'); // 'pipeline' | 'messages' | 'pcb'
  const [orchestrationData, setOrchestrationData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && patient?.id) {
      setLoading(true);
      api.getPatientOrchestration(patient.id)
        .then((data) => {
          setOrchestrationData(data);
        })
        .catch((err) => {
          console.warn('Failed to load orchestration details:', err);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [isOpen, patient?.id]);

  if (!isOpen || !patient) return null;

  const pcb = orchestrationData?.pcb;
  const messages = orchestrationData?.agent_messages || [];

  const trace = orchestrationData?.patient?.decision_trace || patient.decision_trace || [];
  const agentIcons = {
    HospitalCoordinator: ShieldAlert,
    TriageAgent: Bot,
    AmbulanceAgent: Ambulance,
    DoctorAgent: Stethoscope,
    DiagnosticAgent: Activity,
    ICUAgent: Bed,
  };
  const steps = trace.map((entry) => ({
    ...entry,
    icon: agentIcons[entry.agent] || Bot,
    title: entry.action,
    detail: entry.description,
    color: entry.status === 'SKIPPED' ? '#64748b'
      : entry.status === 'WAITING' || entry.status === 'REVIEW_REQUIRED' ? '#b45309'
        : '#0f766e',
  }));

  return (
    <div className="modal-backdrop">
      <div className="modal-panel orchestration-panel">
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              background: 'linear-gradient(135deg, #06b6d4, #6366f1)',
              padding: '10px',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 20px rgba(6, 182, 212, 0.4)'
            }}>
              <Sparkles size={22} color="#fff" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#fff' }}>
                  Recorded agent decisions & resource state
                </h3>
                <span className={`badge-priority-${patient.priority.toLowerCase()}`} style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem' }}>
                  {patient.priority}
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Autonomous Agent Communications for <strong>{patient.name}</strong> ({patient.id})
              </p>
            </div>
          </div>

          <button 
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', padding: '4px' }}
          >
            <X size={22} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
          <button
            onClick={() => setActiveView('pipeline')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '8px',
              border: 'none',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer',
              background: activeView === 'pipeline' ? 'var(--cyan-primary)' : 'rgba(255,255,255,0.05)',
              color: activeView === 'pipeline' ? '#fff' : 'var(--text-muted)'
            }}
          >
            <Layers size={15} />
            <span>Decision trace</span>
          </button>

          <button
            onClick={() => setActiveView('messages')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '8px',
              border: 'none',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer',
              background: activeView === 'messages' ? 'var(--cyan-primary)' : 'rgba(255,255,255,0.05)',
              color: activeView === 'messages' ? '#fff' : 'var(--text-muted)'
            }}
          >
            <MessageSquare size={15} />
            <span>Inter-Agent Messages ({messages.length})</span>
          </button>

          <button
            onClick={() => setActiveView('pcb')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '8px',
              border: 'none',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer',
              background: activeView === 'pcb' ? 'var(--cyan-primary)' : 'rgba(255,255,255,0.05)',
              color: activeView === 'pcb' ? '#fff' : 'var(--text-muted)'
            }}
          >
            <Cpu size={15} />
            <span>OS Process Control Block (PCB)</span>
          </button>
        </div>

        {/* Content based on active tab */}
        {activeView === 'pipeline' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {loading && <div className="empty-state">Loading recorded decisions…</div>}
            {!loading && steps.length === 0 && (
              <div className="empty-state">No decision trace has been recorded for this patient yet.</div>
            )}
            {steps.map((step, idx) => {
              const Icon = step.icon;
              const candidates = step.details?.candidates || [];
              return (
                <div 
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '14px',
                    padding: '12px 16px',
                    borderRadius: '12px',
                    background: step.completed ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.2)',
                    border: step.completed ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid rgba(255, 255, 255, 0.03)',
                  }}
                >
                  <div style={{
                    background: step.completed ? `${step.color}22` : 'rgba(255,255,255,0.05)',
                    padding: '8px',
                    borderRadius: '10px',
                    border: `1px solid ${step.completed ? step.color : 'transparent'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <Icon size={18} color={step.completed ? step.color : '#64748b'} />
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff' }}>{step.agent}</span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', background: 'rgba(0,0,0,0.3)', padding: '1px 6px', borderRadius: '4px' }}>{step.title}</span>
                      </div>
                      <span className={`trace-status trace-status-${String(step.status).toLowerCase().replaceAll('_', '-')}`}>
                        {step.status}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#cbd5e1' }}>
                      {step.detail}
                    </div>
                    {Object.keys(step.details || {}).length > 0 && (
                      <details style={{ marginTop: '8px' }}>
                        <summary style={{ cursor: 'pointer', fontSize: '0.75rem', color: 'var(--accent)' }}>
                          Decision inputs and resource evaluation
                        </summary>
                        {candidates.length > 0 ? (
                          <div className="trace-candidates">
                            {candidates.map((candidate) => (
                              <div className="trace-candidate" key={candidate.resource_id}>
                                <strong>{candidate.rank ? `${candidate.rank}. ` : ''}{candidate.resource_id}</strong>
                                <span>{candidate.eligible ? 'Eligible' : (candidate.rejection_reasons || []).join(', ')}</span>
                                {candidate.score !== null && candidate.score !== undefined && <b>Score {candidate.score}</b>}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <pre className="trace-json">{JSON.stringify(step.details, null, 2)}</pre>
                        )}
                      </details>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {activeView === 'messages' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '420px', overflowY: 'auto' }}>
            {messages.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
                No inter-agent messages recorded for this patient yet.
              </div>
            ) : (
              messages.map((msg, i) => (
                <div 
                  key={i}
                  style={{
                    padding: '10px 14px',
                    borderRadius: '10px',
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid rgba(255,255,255,0.06)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', fontWeight: 700 }}>
                      <span style={{ color: '#38bdf8' }}>{msg.sender}</span>
                      <ArrowRight size={12} color="var(--text-dim)" />
                      <span style={{ color: '#818cf8' }}>{msg.receiver}</span>
                    </div>
                    <span style={{ fontSize: '0.7rem', color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>
                      T+{msg.simulation_time.toFixed(1)}m
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#fff', fontWeight: 600 }}>
                    {msg.message_type}
                  </div>
                  {msg.payload && Object.keys(msg.payload).length > 0 && (
                    <pre style={{
                      margin: 0,
                      padding: '6px 8px',
                      background: 'rgba(0,0,0,0.3)',
                      borderRadius: '6px',
                      fontSize: '0.7rem',
                      color: 'var(--text-muted)',
                      fontFamily: 'var(--font-mono)',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {JSON.stringify(msg.payload, null, 2)}
                    </pre>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeView === 'pcb' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{
              background: 'rgba(15, 23, 42, 0.7)',
              border: '1px solid rgba(6, 182, 212, 0.25)',
              borderRadius: '12px',
              padding: '16px',
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
              gap: '12px'
            }}>
              <div>
                <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem', textTransform: 'uppercase' }}>Process ID (PID)</div>
                <div style={{ color: '#38bdf8', fontSize: '1.1rem', fontWeight: 800, fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                  {pcb?.pid || patient.id}
                </div>
              </div>

              <div>
                <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem', textTransform: 'uppercase' }}>OS Process State</div>
                <div style={{ marginTop: '2px' }}>
                  <span style={{
                    display: 'inline-block',
                    padding: '3px 10px',
                    borderRadius: '6px',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    background: pcb?.state === 'RUNNING' ? 'rgba(16, 185, 129, 0.2)' : pcb?.state === 'BLOCKED' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(6, 182, 212, 0.2)',
                    color: pcb?.state === 'RUNNING' ? '#34d399' : pcb?.state === 'BLOCKED' ? '#f87171' : '#38bdf8',
                    border: '1px solid currentColor'
                  }}>
                    {pcb?.state || 'READY'}
                  </span>
                </div>
              </div>

              <div>
                <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem', textTransform: 'uppercase' }}>Base / Dynamic Priority</div>
                <div style={{ color: '#fff', fontSize: '0.9rem', fontWeight: 700, marginTop: '2px' }}>
                  {pcb?.base_priority || patient.priority} (Aging: {pcb?.dynamic_priority?.toFixed(2) || '1.00'})
                </div>
              </div>

              <div>
                <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem', textTransform: 'uppercase' }}>CPU Burst (Doctor Exam)</div>
                <div style={{ color: '#fff', fontSize: '0.9rem', fontWeight: 700, marginTop: '2px' }}>
                  {pcb?.cpu_burst_time || 10.0} mins
                </div>
              </div>

              <div>
                <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem', textTransform: 'uppercase' }}>I/O Burst (Scanner / Lab)</div>
                <div style={{ color: '#fff', fontSize: '0.9rem', fontWeight: 700, marginTop: '2px' }}>
                  {pcb?.io_burst_time || 0.0} mins
                </div>
              </div>

              <div>
                <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem', textTransform: 'uppercase' }}>Allocated Locks</div>
                <div style={{ color: '#10b981', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', marginTop: '2px' }}>
                  {pcb?.allocated_resources?.join(', ') || [patient.assigned_doctor_id, patient.assigned_icu_bed_id].filter(Boolean).join(', ') || 'None'}
                </div>
              </div>
            </div>

            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
              <strong>OS Principle in Effect:</strong> Multi-Level Priority Scheduling with dynamic aging factor prevents starvation while real-time (P1/P2) emergency processes acquire exclusive Mutex locks and Counting Semaphore permits.
            </div>
          </div>
        )}

        {/* Footer */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
          <button 
            className="btn btn-primary"
            onClick={onClose}
            style={{ fontSize: '0.85rem', padding: '8px 20px' }}
          >
            <span>Close Orchestration View</span>
          </button>
        </div>
      </div>
    </div>
  );
}
