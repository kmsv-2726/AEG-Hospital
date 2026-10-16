import React, { useState } from 'react';
import { Users, Search, Filter, Clock, Ambulance, Stethoscope, Activity, Bed, PlusCircle } from 'lucide-react';

export default function PatientQueuePage({ patients = [], onOpenEmergencyModal }) {
  const [filterPriority, setFilterPriority] = useState('ALL');
  const [filterWaiting, setFilterWaiting] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const filtered = patients.filter((p) => {
    if (filterPriority !== 'ALL' && p.priority !== filterPriority) return false;
    if (filterWaiting && !p.workflow_state.startsWith('WAITING_')) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        p.name.toLowerCase().includes(q) ||
        p.id.toLowerCase().includes(q) ||
        p.condition_description.toLowerCase().includes(q) ||
        p.required_specialty.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header & Controls */}
      <div className="glass-panel" style={{
        padding: '18px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: 'rgba(6, 182, 212, 0.15)', padding: '8px', borderRadius: '10px' }}>
            <Users size={22} color="var(--cyan-primary)" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff' }}>Patient Queue & Emergency Intake</h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Total: {patients.length} | Filtered: {filtered.length} patients
            </p>
          </div>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Search Box */}
          <div style={{ position: 'relative', minWidth: '220px' }}>
            <Search size={15} color="var(--text-dim)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
            <input
              type="text"
              placeholder="Search by ID, name, specialty..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '7px 10px 7px 32px',
                background: 'rgba(0,0,0,0.3)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '0.8rem',
                outline: 'none'
              }}
            />
          </div>

          {/* Priority filter pills */}
          <div style={{ display: 'flex', gap: '4px', background: 'rgba(0,0,0,0.25)', padding: '3px', borderRadius: '8px' }}>
            {['ALL', 'P1', 'P2', 'P3', 'P4'].map((prio) => (
              <button
                key={prio}
                onClick={() => setFilterPriority(prio)}
                style={{
                  padding: '5px 10px',
                  borderRadius: '6px',
                  border: 'none',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: filterPriority === prio ? 'var(--cyan-primary)' : 'transparent',
                  color: filterPriority === prio ? '#fff' : 'var(--text-muted)',
                }}
              >
                {prio}
              </button>
            ))}
          </div>

          {/* Waiting toggle */}
          <button
            onClick={() => setFilterWaiting(!filterWaiting)}
            style={{
              padding: '6px 12px',
              borderRadius: '8px',
              border: filterWaiting ? '1px solid var(--amber-warning)' : '1px solid var(--border-subtle)',
              background: filterWaiting ? 'rgba(245, 158, 11, 0.2)' : 'rgba(0,0,0,0.25)',
              color: filterWaiting ? '#fbbf24' : 'var(--text-muted)',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Clock size={13} />
            <span>Waiting Only</span>
          </button>

          {/* Intake button */}
          <button
            className="btn btn-primary"
            onClick={onOpenEmergencyModal}
            style={{ fontSize: '0.8rem', padding: '7px 14px' }}
          >
            <PlusCircle size={15} />
            <span>New Emergency</span>
          </button>
        </div>
      </div>

      {/* Patient Table */}
      <div className="glass-panel" style={{ padding: '20px', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-dim)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
              <th style={{ padding: '12px 14px' }}>ID & PATIENT</th>
              <th style={{ padding: '12px 14px' }}>PRIORITY</th>
              <th style={{ padding: '12px 14px' }}>SEVERITY & DIAGNOSIS</th>
              <th style={{ padding: '12px 14px' }}>WORKFLOW STATE</th>
              <th style={{ padding: '12px 14px' }}>AMBULANCE</th>
              <th style={{ padding: '12px 14px' }}>DOCTOR</th>
              <th style={{ padding: '12px 14px' }}>DIAGNOSTICS</th>
              <th style={{ padding: '12px 14px' }}>ICU BED</th>
              <th style={{ padding: '12px 14px' }}>ARRIVAL</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '36px', color: 'var(--text-dim)' }}>
                  No patients match the selected filter criteria.
                </td>
              </tr>
            ) : (
              filtered.map((p) => {
                const priorityClass = `badge-priority-${p.priority.toLowerCase()}`;
                const isWaiting = p.workflow_state.startsWith('WAITING_');
                return (
                  <tr key={p.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', transition: 'background 0.15s' }}>
                    <td style={{ padding: '14px' }}>
                      <div style={{ fontWeight: 700, color: '#fff' }}>{p.name}</div>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: '#38bdf8' }}>{p.id} • {p.age}y • {p.gender}</div>
                    </td>
                    <td style={{ padding: '14px' }}>
                      <span className={priorityClass} style={{ padding: '4px 10px', borderRadius: '6px', fontSize: '0.75rem' }}>
                        {p.priority}
                      </span>
                    </td>
                    <td style={{ padding: '14px', maxWidth: '240px' }}>
                      <div style={{ fontWeight: 600, color: '#e2e8f0', fontSize: '0.8rem' }}>{p.severity_category}</div>
                      <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {p.condition_description}
                      </div>
                    </td>
                    <td style={{ padding: '14px' }}>
                      <span className={`badge-state ${isWaiting ? 'badge-state-waiting' : p.workflow_state === 'COMPLETED' || p.workflow_state === 'DISCHARGED' ? 'badge-state-completed' : 'badge-state-active'}`}>
                        {p.workflow_state}
                      </span>
                    </td>
                    <td style={{ padding: '14px' }}>
                      {p.assigned_ambulance_id ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#38bdf8', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                          <Ambulance size={14} />
                          <span>{p.assigned_ambulance_id}</span>
                        </div>
                      ) : p.requires_ambulance ? (
                        <span style={{ color: 'var(--amber-warning)', fontSize: '0.75rem' }}>
                          {isWaiting && p.workflow_state.includes('AMBULANCE') ? 'Waiting Dispatch' : 'Pending'}
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Walk-in</span>
                      )}
                    </td>
                    <td style={{ padding: '14px' }}>
                      {p.assigned_doctor_id ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#818cf8', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                          <Stethoscope size={14} />
                          <span>{p.assigned_doctor_id}</span>
                        </div>
                      ) : (
                        <div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Req: {p.required_specialty}</div>
                          {isWaiting && p.workflow_state.includes('DOCTOR') && (
                            <span style={{ color: 'var(--amber-warning)', fontSize: '0.7rem', fontWeight: 600 }}>In Queue</span>
                          )}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '14px' }}>
                      {p.assigned_diagnostic_id ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#34d399', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                          <Activity size={14} />
                          <span>{p.assigned_diagnostic_id}</span>
                        </div>
                      ) : p.required_diagnostic ? (
                        <div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Req: {p.required_diagnostic}</div>
                          {isWaiting && p.workflow_state.includes('DIAGNOSTIC') && (
                            <span style={{ color: 'var(--amber-warning)', fontSize: '0.7rem', fontWeight: 600 }}>In Queue</span>
                          )}
                        </div>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>None</span>
                      )}
                    </td>
                    <td style={{ padding: '14px' }}>
                      {p.assigned_icu_bed_id ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f87171', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                          <Bed size={14} />
                          <span>{p.assigned_icu_bed_id}</span>
                        </div>
                      ) : p.requires_icu ? (
                        <div>
                          <span style={{ color: '#f87171', fontSize: '0.75rem', fontWeight: 600 }}>Required</span>
                          {isWaiting && p.workflow_state.includes('ICU') && (
                            <div style={{ color: 'var(--amber-warning)', fontSize: '0.7rem' }}>Waiting Bed</div>
                          )}
                        </div>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>None</span>
                      )}
                    </td>
                    <td style={{ padding: '14px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {p.arrival_time}m
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
