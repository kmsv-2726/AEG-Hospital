import React, { useState } from 'react';
import { 
  Bot, 
  Shield, 
  CheckCircle2, 
  MessageSquare, 
  AlertCircle, 
  Cpu, 
  Zap, 
  Activity, 
  Lock, 
  Unlock, 
  ArrowRight,
  Layers,
  Sparkles,
  Users
} from 'lucide-react';

export default function AgentMonitorPage({ agents = [], resources, osStatus, messages = [], onViewOrchestration, patients = [] }) {
  const [activeTab, setActiveTab] = useState('agents'); // 'agents' | 'messages' | 'os'

  const agentMetadata = {
    HospitalCoordinator: {
      tag: 'MASTER COORDINATOR',
      peas: {
        percepts: 'Emergency notifications, agent replies, waiting queues, clock ticks',
        actions: 'Workflow progression, message routing, conflict resolution, retry triggers',
        goal: 'Optimize emergency throughput and resolve resource competition cooperative MAS',
        environment: 'Simulated ED with ambulances, physicians, scanners, ICU beds',
      },
      accent: 'linear-gradient(135deg, #06b6d4, #6366f1)',
    },
    TriageAgent: {
      tag: 'RULE-BASED INTAKE',
      peas: {
        percepts: 'Patient symptoms, reported trauma severity, arrival timestamp',
        actions: 'Assign synthetic priority P1-P4, emit TRIAGE_COMPLETED event',
        goal: 'Deterministic stratification of urgency to protect life-threatening cases',
        environment: 'Intake and emergency admission queue',
      },
      accent: 'linear-gradient(135deg, #ef4444, #f59e0b)',
    },
    AmbulanceAgent: {
      tag: 'DISPATCH OPTIMIZER',
      peas: {
        percepts: 'Fleet status (available/busy), patient coordinates, priority',
        actions: 'Utility ranking, atomic dispatch, release upon hospital arrival',
        goal: 'Minimize response time and prioritize critical patients for advanced ALS',
        environment: 'Simulated geographic sectors and fleet stations',
      },
      accent: 'linear-gradient(135deg, #06b6d4, #10b981)',
    },
    DoctorAgent: {
      tag: 'STAFFING BALANCER',
      peas: {
        percepts: 'Physician specialties, current patient assignment, workload count',
        actions: 'Specialty constraint filtering, workload tie-breaking, doctor reservation',
        goal: 'Match medical specialty and distribute clinical load evenly',
        environment: 'Emergency trauma, cardiology, and general medicine bays',
      },
      accent: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    },
    DiagnosticAgent: {
      tag: 'EQUIPMENT SCHEDULER',
      peas: {
        percepts: 'Scanners (CT, MRI, X-Ray, Lab), queue length, processing duration',
        actions: 'Equipment booking, completion scheduling, queue reassignment',
        goal: 'Maximize scanner utilization and eliminate idle diagnostic time',
        environment: 'Hospital diagnostic imaging suite',
      },
      accent: 'linear-gradient(135deg, #f59e0b, #eab308)',
    },
    ICUAgent: {
      tag: 'CRITICAL CARE ALLOCATOR',
      peas: {
        percepts: 'ICU bed availability, ventilator equipment presence, patient priority',
        actions: 'Ventilator-matching reservation, conflict queueing, bed sanitization release',
        goal: 'Safeguard critical ICU capacity for unstable P1 resuscitation',
        environment: 'Intensive Care Unit bays',
      },
      accent: 'linear-gradient(135deg, #ec4899, #f43f5e)',
    },
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'EXAMINING':
      case 'SCANNING':
      case 'MONITORING_ICU':
      case 'DISPATCHING':
      case 'BUSY':
        return '#38bdf8';
      case 'WAITING_RESOURCE':
      case 'BLOCKED':
        return '#f87171';
      case 'IDLE':
      case 'ACTIVE':
      default:
        return '#34d399';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div className="glass-panel" style={{
        padding: '20px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ background: 'rgba(99, 102, 241, 0.2)', padding: '10px', borderRadius: '12px' }}>
            <Bot size={24} color="var(--indigo-primary)" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#fff' }}>Autonomous Multi-Agent AI & OS Resource Center</h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Real-time monitoring of 5 Specialized Agents, Inter-Agent Message Bus, and OS Resource Allocation
            </p>
          </div>
        </div>

        {/* Tab Controls */}
        <div style={{ display: 'flex', gap: '6px', background: 'rgba(0,0,0,0.3)', padding: '4px', borderRadius: '10px' }}>
          <button
            onClick={() => setActiveTab('agents')}
            style={{
              padding: '6px 14px',
              borderRadius: '7px',
              border: 'none',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer',
              background: activeTab === 'agents' ? 'var(--cyan-primary)' : 'transparent',
              color: activeTab === 'agents' ? '#fff' : 'var(--text-muted)'
            }}
          >
            Agent Monitor ({agents.length})
          </button>

          <button
            onClick={() => setActiveTab('messages')}
            style={{
              padding: '6px 14px',
              borderRadius: '7px',
              border: 'none',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer',
              background: activeTab === 'messages' ? 'var(--cyan-primary)' : 'transparent',
              color: activeTab === 'messages' ? '#fff' : 'var(--text-muted)'
            }}
          >
            Inter-Agent Message Bus ({messages.length})
          </button>

          <button
            onClick={() => setActiveTab('os')}
            style={{
              padding: '6px 14px',
              borderRadius: '7px',
              border: 'none',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer',
              background: activeTab === 'os' ? 'var(--cyan-primary)' : 'transparent',
              color: activeTab === 'os' ? '#fff' : 'var(--text-muted)'
            }}
          >
            OS Resource Management
          </button>
        </div>
      </div>

      {/* VIEW 1: AGENT MONITOR */}
      {activeTab === 'agents' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '20px' }}>
          {agents.map((ag) => {
            const meta = agentMetadata[ag.name] || {
              tag: 'AGENT',
              peas: { percepts: 'State', actions: 'Execute', goal: 'Coordinate', environment: 'ED' },
              accent: 'linear-gradient(135deg, #06b6d4, #6366f1)',
            };
            const statusColor = getStatusColor(ag.status);

            return (
              <div key={ag.name} className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', position: 'relative', overflow: 'hidden' }}>
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '3px', background: meta.accent }}></div>

                {/* Identity & Status */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff' }}>{ag.name}</h3>
                      <span style={{ fontSize: '0.65rem', fontWeight: 700, padding: '2px 8px', borderRadius: '4px', background: 'rgba(255,255,255,0.08)', color: 'var(--cyan-primary)', fontFamily: 'var(--font-mono)' }}>
                        {meta.tag}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '2px' }}>{ag.role}</div>
                  </div>

                  <div style={{
                    padding: '4px 10px',
                    borderRadius: '9999px',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    fontFamily: 'var(--font-mono)',
                    background: `${statusColor}22`,
                    color: statusColor,
                    border: `1px solid ${statusColor}55`,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}>
                    <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: statusColor }}></span>
                    {ag.status}
                  </div>
                </div>

                {/* Active Patient Engagement */}
                {ag.active_patients && ag.active_patients.length > 0 && (
                  <div style={{ background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.25)', borderRadius: '8px', padding: '8px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: '#38bdf8' }}>
                      <Users size={14} />
                      <span>Actively Handling: <strong>{ag.active_patients.join(', ')}</strong></span>
                    </div>
                    {onViewOrchestration && (
                      <button
                        onClick={() => {
                          const p = patients.find(pt => pt.id === ag.active_patients[0]);
                          if (p) onViewOrchestration(p);
                        }}
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#fff',
                          fontSize: '0.7rem',
                          textDecoration: 'underline',
                          cursor: 'pointer'
                        }}
                      >
                        Inspect
                      </button>
                    )}
                  </div>
                )}

                {/* Live Action & Last Message */}
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px 14px', borderRadius: '10px', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Zap size={11} color="var(--amber-warning)" />
                      Most Recent Autonomous Action
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#e2e8f0', marginTop: '2px', wordBreak: 'break-word' }}>
                      {ag.last_action || 'Initialized and awaiting emergency arrival.'}
                    </div>
                  </div>

                  <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '6px' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <MessageSquare size={11} color="var(--cyan-primary)" />
                      Last Inter-Agent Message
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                      {ag.last_message || 'No direct messages recorded in current tick.'}
                    </div>
                  </div>
                </div>

                {/* PEAS Specification Profile */}
                <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '12px' }}>
                  <div style={{ fontSize: '0.72rem', color: 'var(--cyan-primary)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.04em' }}>
                    PEAS Specification Profile
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '6px', fontSize: '0.75rem' }}>
                    <div>
                      <strong style={{ color: '#fff' }}>P (Goal):</strong>{' '}
                      <span style={{ color: 'var(--text-muted)' }}>{meta.peas.goal}</span>
                    </div>
                    <div>
                      <strong style={{ color: '#fff' }}>E (Environment):</strong>{' '}
                      <span style={{ color: 'var(--text-muted)' }}>{meta.peas.environment}</span>
                    </div>
                    <div>
                      <strong style={{ color: '#fff' }}>A (Actuators):</strong>{' '}
                      <span style={{ color: 'var(--text-muted)' }}>{meta.peas.actions}</span>
                    </div>
                    <div>
                      <strong style={{ color: '#fff' }}>S (Sensors):</strong>{' '}
                      <span style={{ color: 'var(--text-muted)' }}>{meta.peas.percepts}</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* VIEW 2: INTER-AGENT MESSAGE BUS FEED */}
      {activeTab === 'messages' && (
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>Inter-Agent Message Bus Log</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Chronological record of autonomous messages dispatched between specialized agents</p>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--cyan-primary)', background: 'rgba(6, 182, 212, 0.15)', padding: '4px 10px', borderRadius: '6px', fontWeight: 600 }}>
              {messages.length} Dispatched Messages
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '600px', overflowY: 'auto' }}>
            {messages.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
                No inter-agent messages recorded yet. Submit a new emergency patient or advance the simulation.
              </div>
            ) : (
              messages.slice().reverse().map((msg, i) => (
                <div
                  key={i}
                  style={{
                    padding: '12px 16px',
                    borderRadius: '10px',
                    background: 'rgba(15, 23, 42, 0.5)',
                    border: '1px solid rgba(255,255,255,0.05)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '6px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 700, color: '#38bdf8', fontSize: '0.85rem' }}>{msg.sender}</span>
                      <ArrowRight size={13} color="var(--text-dim)" />
                      <span style={{ fontWeight: 700, color: '#818cf8', fontSize: '0.85rem' }}>{msg.receiver}</span>
                      {msg.patient_id && (
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: '4px', color: '#fff' }}>
                          Patient: {msg.patient_id}
                        </span>
                      )}
                    </div>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: '#f59e0b' }}>
                      Sim T+{msg.simulation_time.toFixed(1)}m
                    </span>
                  </div>

                  <div style={{ fontSize: '0.8rem', color: '#fff', fontWeight: 600 }}>
                    {msg.message_type}
                  </div>

                  {msg.payload && Object.keys(msg.payload).length > 0 && (
                    <pre style={{
                      margin: 0,
                      padding: '6px 10px',
                      background: 'rgba(0,0,0,0.3)',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
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
        </div>
      )}

      {/* VIEW 3: OS RESOURCE MANAGEMENT */}
      {activeTab === 'os' && osStatus && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* OS Key Utilization Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
            <div className="glass-panel" style={{ padding: '16px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>Physician CPU Utilization</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#38bdf8', marginTop: '4px' }}>
                {osStatus.doctor_cpu_utilization_pct}%
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>Exclusive Doctor Mutexes active</div>
            </div>

            <div className="glass-panel" style={{ padding: '16px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>Scanner I/O Utilization</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#34d399', marginTop: '4px' }}>
                {osStatus.diagnostic_io_utilization_pct}%
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>Diagnostic imaging equipment in duty</div>
            </div>

            <div className="glass-panel" style={{ padding: '16px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>ICU Counting Semaphore</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f87171', marginTop: '4px' }}>
                {osStatus.icu_semaphore?.allocated_permits} / {osStatus.icu_semaphore?.capacity}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                {osStatus.icu_semaphore?.blocked_count} processes blocked on permits
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '16px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>OS Ready Queue Length</div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fbbf24', marginTop: '4px' }}>
                {osStatus.ready_queue_length}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                Patients awaiting doctor dispatch
              </div>
            </div>
          </div>

          {/* Counting Semaphores & Mutexes Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
            {/* Semaphores Card */}
            <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Lock size={18} color="var(--rose-danger)" />
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>OS Counting Semaphores</h3>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, color: '#fff', fontSize: '0.85rem' }}>{osStatus.icu_semaphore?.name}</span>
                    <span style={{ fontSize: '0.75rem', color: '#f87171', fontWeight: 700 }}>
                      Permits: {osStatus.icu_semaphore?.available_permits} / {osStatus.icu_semaphore?.capacity}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Active Holders: {Object.keys(osStatus.icu_semaphore?.holders || {}).join(', ') || 'None'}
                  </div>
                  {osStatus.icu_semaphore?.blocked_count > 0 && (
                    <div style={{ fontSize: '0.75rem', color: '#fbbf24', marginTop: '4px' }}>
                      Blocked Queue: {osStatus.icu_semaphore?.blocked_pids?.join(', ')}
                    </div>
                  )}
                </div>

                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 700, color: '#fff', fontSize: '0.85rem' }}>{osStatus.ambulance_semaphore?.name}</span>
                    <span style={{ fontSize: '0.75rem', color: '#38bdf8', fontWeight: 700 }}>
                      Permits: {osStatus.ambulance_semaphore?.available_permits} / {osStatus.ambulance_semaphore?.capacity}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Active Holders: {Object.keys(osStatus.ambulance_semaphore?.holders || {}).join(', ') || 'None'}
                  </div>
                </div>
              </div>
            </div>

            {/* Mutexes Card */}
            <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Cpu size={18} color="var(--cyan-primary)" />
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>Exclusive Resource Mutexes</h3>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '8px' }}>
                {osStatus.doctor_mutexes?.map((m, i) => (
                  <div key={i} style={{ background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#fff' }}>{m.name}</span>
                      {m.is_locked ? <Lock size={12} color="#f87171" /> : <Unlock size={12} color="#34d399" />}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: m.is_locked ? '#f87171' : '#34d399', marginTop: '2px' }}>
                      {m.is_locked ? `Locked by ${m.current_owner}` : 'Unlocked / Idle'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Process Control Blocks (PCB) Table */}
          <div className="glass-panel" style={{ padding: '20px', overflowX: 'auto' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff', marginBottom: '12px' }}>
              Registered Patient Process Control Blocks (PCBs)
            </h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                  <th style={{ padding: '10px 12px' }}>PID</th>
                  <th style={{ padding: '10px 12px' }}>PATIENT NAME</th>
                  <th style={{ padding: '10px 12px' }}>OS STATE</th>
                  <th style={{ padding: '10px 12px' }}>PRIORITY (AGING)</th>
                  <th style={{ padding: '10px 12px' }}>CPU BURST</th>
                  <th style={{ padding: '10px 12px' }}>I/O BURST</th>
                  <th style={{ padding: '10px 12px' }}>HELD LOCKS</th>
                </tr>
              </thead>
              <tbody>
                {osStatus.pcbs?.map((pcb) => (
                  <tr key={pcb.pid} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#38bdf8', fontWeight: 700 }}>
                      {pcb.pid}
                    </td>
                    <td style={{ padding: '10px 12px', color: '#fff' }}>
                      {pcb.patient_name}
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{
                        display: 'inline-block',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        background: pcb.state === 'RUNNING' ? 'rgba(16,185,129,0.2)' : pcb.state === 'BLOCKED' ? 'rgba(239,68,68,0.2)' : 'rgba(6,182,212,0.2)',
                        color: pcb.state === 'RUNNING' ? '#34d399' : pcb.state === 'BLOCKED' ? '#f87171' : '#38bdf8'
                      }}>
                        {pcb.state}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', color: '#fff' }}>
                      {pcb.base_priority} (dyn: {pcb.dynamic_priority?.toFixed(2)})
                    </td>
                    <td style={{ padding: '10px 12px', color: 'var(--text-muted)' }}>
                      {pcb.cpu_burst_time}m
                    </td>
                    <td style={{ padding: '10px 12px', color: 'var(--text-muted)' }}>
                      {pcb.io_burst_time}m
                    </td>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#10b981', fontSize: '0.75rem' }}>
                      {pcb.allocated_resources?.join(', ') || 'None'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
