import React from 'react';
import { Bot, Shield, CheckCircle2, MessageSquare, AlertCircle, Cpu, Zap, Activity } from 'lucide-react';

export default function AgentMonitorPage({ agents = [], resources }) {
  // Enhanced agent descriptions for academic presentation
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
            <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#fff' }}>Multi-Agent System (MAS) Live Monitor</h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Monitoring 5 Autonomous Specialized Agents + 1 Central Hospital Coordinator
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(16, 185, 129, 0.15)', padding: '4px 10px', borderRadius: '6px', color: '#34d399', fontWeight: 600 }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }}></span>
            Active Architecture
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(6, 182, 212, 0.15)', padding: '4px 10px', borderRadius: '6px', color: '#38bdf8', fontWeight: 600 }}>
            PEAS Compliant
          </span>
        </div>
      </div>

      {/* Agents Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '20px' }}>
        {agents.map((ag) => {
          const meta = agentMetadata[ag.name] || {
            tag: 'AGENT',
            peas: { percepts: 'State', actions: 'Execute', goal: 'Coordinate', environment: 'ED' },
            accent: 'linear-gradient(135deg, #06b6d4, #6366f1)',
          };

          return (
            <div key={ag.name} className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', position: 'relative', overflow: 'hidden' }}>
              {/* Top Accent Ribbon */}
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '3px', background: meta.accent }}></div>

              {/* Agent Identity */}
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
                  background: ag.status === 'ACTIVE' || ag.status === 'IDLE' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                  color: ag.status === 'ACTIVE' || ag.status === 'IDLE' ? '#34d399' : '#fbbf24',
                  border: '1px solid rgba(255,255,255,0.08)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: ag.status === 'ACTIVE' || ag.status === 'IDLE' ? '#10b981' : '#f59e0b' }}></span>
                  {ag.status}
                </div>
              </div>

              {/* Live Action & Last Message */}
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px 14px', borderRadius: '10px', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Zap size={11} color="var(--amber-warning)" />
                    Most Recent Action
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#e2e8f0', marginTop: '2px', wordBreak: 'break-word' }}>
                    {ag.last_action || 'Initialized and awaiting simulation events.'}
                  </div>
                </div>

                <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '6px' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <MessageSquare size={11} color="var(--cyan-primary)" />
                    Last Message Exchanged
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                    {ag.last_message || 'No direct messages recorded in current tick.'}
                  </div>
                </div>
              </div>

              {/* PEAS Decomposition Box */}
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
    </div>
  );
}
