import React from 'react';
import { 
  Users, 
  CheckCircle2, 
  AlertOctagon, 
  Clock, 
  Ambulance, 
  Stethoscope, 
  Activity, 
  Bed, 
  ArrowRight,
  TrendingUp,
  Cpu
} from 'lucide-react';

export default function OverviewPage({ 
  patients = [], 
  resources, 
  metrics, 
  strategy, 
  setActiveTab 
}) {
  const counts = resources?.counts || {
    ambulances: { available: 3, busy: 0, total: 3 },
    doctors: { available: 4, busy: 0, total: 4 },
    diagnostic_resources: { available: 5, busy: 0, total: 5 },
    icu_beds: { available: 3, busy: 0, total: 3 },
  };

  const completedCount = patients.filter(p => ['COMPLETED', 'DISCHARGED'].includes(p.workflow_state)).length;
  const waitingCount = patients.filter(p => p.workflow_state.startsWith('WAITING_')).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner / System Strategy Status */}
      <div className="glass-panel" style={{
        padding: '20px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px',
        background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.12), rgba(99, 102, 241, 0.08))',
        border: '1px solid rgba(6, 182, 212, 0.25)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ background: 'rgba(6, 182, 212, 0.2)', padding: '10px', borderRadius: '12px' }}>
            <Cpu size={24} color="var(--cyan-primary)" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.01em' }}>
              Hospital Emergency Command Center
            </h2>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
              Active Multi-Agent AI Strategy: <strong style={{ color: '#38bdf8' }}>{strategy === 'PRIORITY_AWARE' ? 'Priority & Resource-Aware Multi-Agent Coordination' : 'First-In, First-Out (FIFO) Baseline'}</strong>
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: 600 }}>Simulation Engine</div>
            <div style={{ fontSize: '0.85rem', color: '#10b981', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }}></span>
              Deterministic Discrete-Event Mode
            </div>
          </div>
        </div>
      </div>

      {/* Top Level Metric KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="glass-panel" style={{ padding: '18px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-muted)', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>Active Cohort</span>
            <Users size={18} color="var(--cyan-primary)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#fff' }}>{patients.length}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>Synthetic patients registered</div>
        </div>

        <div className="glass-panel" style={{ padding: '18px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-muted)', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>Completed Workflows</span>
            <CheckCircle2 size={18} color="var(--emerald-success)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#fff' }}>
            {completedCount} <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>/ {patients.length}</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--emerald-success)', marginTop: '4px', fontWeight: 600 }}>
            {metrics?.workflow_completion_rate || 0}% Success Rate
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '18px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-muted)', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>Resource Conflicts</span>
            <AlertOctagon size={18} color={metrics?.resource_conflicts > 0 ? "var(--amber-warning)" : "var(--text-dim)"} />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: metrics?.resource_conflicts > 0 ? '#fbbf24' : '#fff' }}>
            {metrics?.resource_conflicts || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Resolved via queuing & retries
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '18px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-muted)', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>Avg Waiting Time</span>
            <Clock size={18} color="var(--indigo-primary)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#fff' }}>
            {metrics?.average_waiting_time !== null && metrics?.average_waiting_time !== undefined 
              ? `${metrics.average_waiting_time}m` 
              : 'N/A'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>Mean queue duration</div>
        </div>
      </div>

      {/* Resource Allocation Gauges */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {/* Ambulances */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ background: 'rgba(6,182,212,0.15)', padding: '8px', borderRadius: '8px' }}>
                <Ambulance size={20} color="var(--cyan-primary)" />
              </div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>Ambulance Fleet</h4>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Managed by AmbulanceAgent</div>
              </div>
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: counts.ambulances.available > 0 ? '#34d399' : '#f87171' }}>
              {counts.ambulances.available} / {counts.ambulances.total} Ready
            </span>
          </div>
          <div style={{ height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ 
              width: `${(counts.ambulances.available / counts.ambulances.total) * 100}%`, 
              height: '100%', 
              background: 'linear-gradient(90deg, #06b6d4, #10b981)' 
            }}></div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '10px' }}>
            <span>Busy: {counts.ambulances.busy}</span>
            <span>Utilization: {metrics?.ambulance_utilization || 0}%</span>
          </div>
        </div>

        {/* Doctors */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ background: 'rgba(99,102,241,0.15)', padding: '8px', borderRadius: '8px' }}>
                <Stethoscope size={20} color="var(--indigo-primary)" />
              </div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>Medical Doctors</h4>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Managed by DoctorAgent</div>
              </div>
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: counts.doctors.available > 0 ? '#34d399' : '#f87171' }}>
              {counts.doctors.available} / {counts.doctors.total} Ready
            </span>
          </div>
          <div style={{ height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ 
              width: `${(counts.doctors.available / counts.doctors.total) * 100}%`, 
              height: '100%', 
              background: 'linear-gradient(90deg, #6366f1, #06b6d4)' 
            }}></div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '10px' }}>
            <span>Busy: {counts.doctors.busy}</span>
            <span>Workload Util: {metrics?.doctor_utilization || 0}%</span>
          </div>
        </div>

        {/* Diagnostic Resources */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ background: 'rgba(245,158,11,0.15)', padding: '8px', borderRadius: '8px' }}>
                <Activity size={20} color="var(--amber-warning)" />
              </div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>Diagnostic Scanners</h4>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Managed by DiagnosticAgent</div>
              </div>
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: counts.diagnostic_resources.available > 0 ? '#34d399' : '#f87171' }}>
              {counts.diagnostic_resources.available} / {counts.diagnostic_resources.total} Ready
            </span>
          </div>
          <div style={{ height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ 
              width: `${(counts.diagnostic_resources.available / counts.diagnostic_resources.total) * 100}%`, 
              height: '100%', 
              background: 'linear-gradient(90deg, #f59e0b, #10b981)' 
            }}></div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '10px' }}>
            <span>Busy: {counts.diagnostic_resources.busy}</span>
            <span>Queue Util: {metrics?.diagnostic_utilization || 0}%</span>
          </div>
        </div>

        {/* ICU Beds */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ background: 'rgba(239,68,68,0.15)', padding: '8px', borderRadius: '8px' }}>
                <Bed size={20} color="var(--rose-danger)" />
              </div>
              <div>
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#fff' }}>ICU Critical Beds</h4>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Managed by ICUAgent</div>
              </div>
            </div>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: counts.icu_beds.available > 0 ? '#34d399' : '#f87171' }}>
              {counts.icu_beds.available} / {counts.icu_beds.total} Ready
            </span>
          </div>
          <div style={{ height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ 
              width: `${(counts.icu_beds.available / counts.icu_beds.total) * 100}%`, 
              height: '100%', 
              background: 'linear-gradient(90deg, #ef4444, #f59e0b)' 
            }}></div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '10px' }}>
            <span>Occupied: {counts.icu_beds.busy}</span>
            <span>Bed Util: {metrics?.icu_utilization || 0}%</span>
          </div>
        </div>
      </div>

      {/* Active Patient Emergency Overview */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>Live Patient Progression</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Emergency department cohort workflow state tracking</p>
          </div>
          <button 
            onClick={() => setActiveTab('patients')} 
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <span>Full Patient Queue</span>
            <ArrowRight size={14} />
          </button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-dim)' }}>
                <th style={{ padding: '10px 14px' }}>PATIENT</th>
                <th style={{ padding: '10px 14px' }}>PRIORITY</th>
                <th style={{ padding: '10px 14px' }}>CONDITION</th>
                <th style={{ padding: '10px 14px' }}>WORKFLOW STATE</th>
                <th style={{ padding: '10px 14px' }}>RESOURCES ASSIGNED</th>
              </tr>
            </thead>
            <tbody>
              {patients.slice(0, 5).map((p) => {
                const priorityClass = `badge-priority-${p.priority.toLowerCase()}`;
                const isWaiting = p.workflow_state.startsWith('WAITING_');
                return (
                  <tr key={p.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '12px 14px', fontWeight: 600, color: '#fff' }}>
                      {p.name} <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-dim)' }}>({p.id})</span>
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className={priorityClass} style={{ padding: '3px 8px', borderRadius: '4px', fontSize: '0.75rem' }}>
                        {p.priority}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--text-muted)', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {p.condition_description}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className={`badge-state ${isWaiting ? 'badge-state-waiting' : p.workflow_state === 'COMPLETED' || p.workflow_state === 'DISCHARGED' ? 'badge-state-completed' : 'badge-state-active'}`}>
                        {p.workflow_state}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: '#38bdf8' }}>
                      {[p.assigned_ambulance_id, p.assigned_doctor_id, p.assigned_diagnostic_id, p.assigned_icu_bed_id].filter(Boolean).join(' • ') || '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
