import React, { useState } from 'react';
import { Clock, Search, AlertOctagon, CheckCircle2, RefreshCw, Filter, ArrowUpRight } from 'lucide-react';

export default function EventTimelinePage({ events = [] }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [conflictsOnly, setConflictsOnly] = useState(false);

  const filtered = events.filter((evt) => {
    if (conflictsOnly && !evt.is_conflict) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        evt.description.toLowerCase().includes(q) ||
        evt.agent.toLowerCase().includes(q) ||
        evt.event_type.toLowerCase().includes(q) ||
        (evt.patient_id && evt.patient_id.toLowerCase().includes(q))
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
            <Clock size={22} color="var(--cyan-primary)" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#fff' }}>Chronological Event & Message Timeline</h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Logged {events.length} multi-agent events | {events.filter(e => e.is_conflict).length} resource conflicts detected
            </p>
          </div>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ position: 'relative', minWidth: '240px' }}>
            <Search size={15} color="var(--text-dim)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
            <input
              type="text"
              placeholder="Search events, patients, agents..."
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

          <button
            onClick={() => setConflictsOnly(!conflictsOnly)}
            style={{
              padding: '7px 14px',
              borderRadius: '8px',
              border: conflictsOnly ? '1px solid var(--amber-warning)' : '1px solid var(--border-subtle)',
              background: conflictsOnly ? 'rgba(245, 158, 11, 0.25)' : 'rgba(0,0,0,0.25)',
              color: conflictsOnly ? '#fbbf24' : 'var(--text-muted)',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <AlertOctagon size={15} color={conflictsOnly ? '#fbbf24' : 'var(--text-dim)'} />
            <span>Resource Conflicts Only</span>
          </button>
        </div>
      </div>

      {/* Events List */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        {filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
            No events match your current filter. Run the simulation to generate real agent messages and events.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {filtered.map((evt, idx) => {
              const isConflict = evt.is_conflict;
              const isRelease = evt.event_type.includes('RELEASED');
              const isAssignment = evt.event_type.includes('ASSIGNED') || evt.event_type.includes('RESERVED');

              return (
                <div
                  key={evt.id || idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '16px',
                    padding: '14px 18px',
                    borderRadius: '12px',
                    background: isConflict 
                      ? 'rgba(245, 158, 11, 0.08)' 
                      : isRelease
                      ? 'rgba(99, 102, 241, 0.06)'
                      : isAssignment
                      ? 'rgba(6, 182, 212, 0.06)'
                      : 'rgba(255, 255, 255, 0.02)',
                    border: isConflict 
                      ? '1px solid rgba(245, 158, 11, 0.3)' 
                      : '1px solid var(--border-subtle)',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {/* Timestamp & Type Icon */}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '70px' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem', fontWeight: 700, color: '#38bdf8' }}>
                      {evt.simulation_time.toFixed(1)}m
                    </span>
                    <div style={{ marginTop: '6px' }}>
                      {isConflict ? (
                        <div style={{ background: 'rgba(245, 158, 11, 0.2)', padding: '5px', borderRadius: '50%' }}>
                          <AlertOctagon size={16} color="var(--amber-warning)" />
                        </div>
                      ) : isRelease ? (
                        <div style={{ background: 'rgba(99, 102, 241, 0.2)', padding: '5px', borderRadius: '50%' }}>
                          <RefreshCw size={16} color="var(--indigo-primary)" />
                        </div>
                      ) : (
                        <div style={{ background: 'rgba(16, 185, 129, 0.2)', padding: '5px', borderRadius: '50%' }}>
                          <CheckCircle2 size={16} color="var(--emerald-success)" />
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Event Details */}
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', marginBottom: '4px' }}>
                      <span style={{ fontWeight: 700, color: '#fff', fontSize: '0.9rem' }}>
                        {evt.agent}
                      </span>
                      <span style={{
                        fontSize: '0.7rem',
                        fontFamily: 'var(--font-mono)',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        background: 'rgba(255, 255, 255, 0.06)',
                        color: 'var(--text-muted)'
                      }}>
                        {evt.event_type}
                      </span>
                      {evt.patient_id && (
                        <span style={{
                          fontSize: '0.7rem',
                          fontFamily: 'var(--font-mono)',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          background: 'rgba(6, 182, 212, 0.15)',
                          color: '#38bdf8',
                          fontWeight: 600
                        }}>
                          Patient: {evt.patient_id}
                        </span>
                      )}
                      {evt.resource_id && (
                        <span style={{
                          fontSize: '0.7rem',
                          fontFamily: 'var(--font-mono)',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          background: 'rgba(99, 102, 241, 0.15)',
                          color: '#818cf8',
                          fontWeight: 600
                        }}>
                          Resource: {evt.resource_id}
                        </span>
                      )}
                      {isConflict && (
                        <span style={{
                          fontSize: '0.7rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background: 'rgba(245, 158, 11, 0.2)',
                          color: '#fbbf24',
                          border: '1px solid rgba(245, 158, 11, 0.4)'
                        }}>
                          [!] RESOURCE CONFLICT
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: '0.85rem', color: isConflict ? '#fde68a' : '#e2e8f0' }}>
                      {evt.description}
                    </div>
                  </div>

                  {/* Outcome Tag */}
                  <div style={{
                    fontSize: '0.7rem',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    padding: '3px 8px',
                    borderRadius: '6px',
                    background: evt.outcome === 'SUCCESS' ? 'rgba(16, 185, 129, 0.15)' : evt.outcome === 'CONFLICT_WAITING' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(99, 102, 241, 0.15)',
                    color: evt.outcome === 'SUCCESS' ? '#34d399' : evt.outcome === 'CONFLICT_WAITING' ? '#fbbf24' : '#818cf8',
                  }}>
                    {evt.outcome}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
