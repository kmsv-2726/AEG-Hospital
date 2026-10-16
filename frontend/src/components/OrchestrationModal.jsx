import React from 'react';
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
  ArrowRight
} from 'lucide-react';

export default function OrchestrationModal({ isOpen, onClose, patient, events = [] }) {
  if (!isOpen || !patient) return null;

  // Filter events related to this specific patient
  const patientEvents = events.filter(e => e.patient_id === patient.id);

  // Define the multi-agent pipeline steps
  const steps = [
    {
      agent: 'HospitalCoordinator',
      title: 'Intake & Workflow Initiation',
      icon: ShieldAlert,
      color: '#06b6d4',
      completed: true,
      detail: `Registered ${patient.name} (${patient.id}) into emergency department. Initiated multi-agent triage delegation.`,
    },
    {
      agent: 'TriageAgent',
      title: 'Urgency & Severity Stratification',
      icon: Bot,
      color: patient.priority === 'P1' ? '#ef4444' : patient.priority === 'P2' ? '#f59e0b' : '#38bdf8',
      completed: true,
      detail: `Rule-based evaluation matched "${patient.severity_category}". Assigned priority: ${patient.priority}.`,
      badge: patient.priority,
    },
    {
      agent: 'AmbulanceAgent',
      title: 'Fleet Utility Dispatch',
      icon: Ambulance,
      color: '#06b6d4',
      completed: !!patient.assigned_ambulance_id || !patient.requires_ambulance,
      detail: patient.assigned_ambulance_id 
        ? `Allocated closest equipped unit (${patient.assigned_ambulance_id}). Transit ETA dispatched.`
        : patient.requires_ambulance
        ? 'Fleet busy. Request queued in waiting pool.'
        : 'Walk-in / Ambulatory emergency. Ambulance transit skipped.',
      resource: patient.assigned_ambulance_id,
    },
    {
      agent: 'DoctorAgent',
      title: 'Specialty Staffing Allocation',
      icon: Stethoscope,
      color: '#818cf8',
      completed: !!patient.assigned_doctor_id,
      detail: patient.assigned_doctor_id
        ? `Matched clinical specialty "${patient.required_specialty}". Assigned physician (${patient.assigned_doctor_id}).`
        : `Requested specialty "${patient.required_specialty}". Awaiting next available physician in queue.`,
      resource: patient.assigned_doctor_id,
    },
    {
      agent: 'DiagnosticAgent',
      title: 'Diagnostic Imaging & Lab Queue',
      icon: Activity,
      color: '#34d399',
      completed: !!patient.assigned_diagnostic_id || !patient.required_diagnostic,
      detail: patient.assigned_diagnostic_id
        ? `Scheduled scanner (${patient.assigned_diagnostic_id}) for required ${patient.required_diagnostic}.`
        : patient.required_diagnostic
        ? `Required ${patient.required_diagnostic} is occupied. Patient entered diagnostic waiting queue.`
        : 'No imaging required for this clinical care pathway.',
      resource: patient.assigned_diagnostic_id,
    },
    {
      agent: 'ICUAgent',
      title: 'Critical Bed & Ventilator Allocation',
      icon: Bed,
      color: '#f87171',
      completed: !!patient.assigned_icu_bed_id || !patient.requires_icu,
      detail: patient.assigned_icu_bed_id
        ? `Reserved critical care bay (${patient.assigned_icu_bed_id}) with continuous hemodynamic monitoring.`
        : patient.requires_icu
        ? 'All ICU beds occupied. Priority queue triggered.'
        : 'Non-ICU standard care pathway.',
      resource: patient.assigned_icu_bed_id,
    },
  ];

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.82)',
      backdropFilter: 'blur(10px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 110,
      padding: '20px'
    }}>
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: '720px',
        maxHeight: '90vh',
        background: '#090d16',
        border: '1px solid rgba(6, 182, 212, 0.4)',
        borderRadius: '20px',
        padding: '24px 28px',
        boxShadow: '0 25px 60px rgba(0,0,0,0.8)',
        display: 'flex',
        flexDirection: 'column',
        gap: '18px',
        overflowY: 'auto'
      }}>
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
                  Live Multi-Agent Orchestration
                </h3>
                <span className={`badge-priority-${patient.priority.toLowerCase()}`} style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem' }}>
                  {patient.priority}
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Cooperative Agent Sequence for <strong>{patient.name}</strong> ({patient.id})
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

        {/* Patient Status Overview Card */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.7)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '12px',
          padding: '14px 18px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: '12px',
          fontSize: '0.8rem'
        }}>
          <div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem', textTransform: 'uppercase' }}>Reported Condition</div>
            <div style={{ color: '#fff', fontWeight: 600, marginTop: '2px' }}>{patient.condition_description}</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem', textTransform: 'uppercase' }}>Current Workflow State</div>
            <div style={{ marginTop: '2px' }}>
              <span className={`badge-state ${patient.workflow_state.startsWith('WAITING_') ? 'badge-state-waiting' : patient.workflow_state === 'COMPLETED' || patient.workflow_state === 'DISCHARGED' ? 'badge-state-completed' : 'badge-state-active'}`}>
                {patient.workflow_state}
              </span>
            </div>
          </div>
          <div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem', textTransform: 'uppercase' }}>Required Specialty</div>
            <div style={{ color: '#818cf8', fontWeight: 700, marginTop: '2px' }}>{patient.required_specialty}</div>
          </div>
          <div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem', textTransform: 'uppercase' }}>Assigned Assets</div>
            <div style={{ color: '#38bdf8', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', marginTop: '2px' }}>
              {[patient.assigned_ambulance_id, patient.assigned_doctor_id, patient.assigned_diagnostic_id, patient.assigned_icu_bed_id].filter(Boolean).join(' • ') || 'None'}
            </div>
          </div>
        </div>

        {/* Interactive Stepper Pipeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--cyan-primary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Autonomous Multi-Agent Pipeline Execution
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {steps.map((step, idx) => {
              const Icon = step.icon;
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
                    position: 'relative'
                  }}
                >
                  {/* Step Icon */}
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

                  {/* Step Description */}
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff' }}>{step.agent}</span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', background: 'rgba(0,0,0,0.3)', padding: '1px 6px', borderRadius: '4px' }}>{step.title}</span>
                      </div>
                      {step.completed && (
                        <span style={{ fontSize: '0.7rem', color: '#34d399', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <CheckCircle2 size={13} />
                          <span>ACTED</span>
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#cbd5e1' }}>
                      {step.detail}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

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
