import React, { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { EmptyState, PageHeader, SectionTitle } from '../components/OperationsUI';

export default function EventTimelinePage({ events = [] }) {
  const [query, setQuery] = useState('');
  const [conflictsOnly, setConflictsOnly] = useState(false);
  const filtered = useMemo(() => events.filter((event) => {
    if (conflictsOnly && !event.is_conflict) return false;
    const search = query.trim().toLowerCase();
    if (!search) return true;
    return [event.event_type, event.agent, event.patient_id, event.resource_id, event.description]
      .some((value) => String(value || '').toLowerCase().includes(search));
  }).slice().reverse(), [events, query, conflictsOnly]);

  return (
    <div className="page-stack">
      <PageHeader eyebrow="SIMULATED EVENT LOG" title="Event timeline" description={`${events.length} recorded events · ${events.filter((event) => event.is_conflict).length} allocation conflicts`} />
      <section className="page-section">
        <div className="queue-toolbar">
          <label className="search-field"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search event, patient, agent or resource" aria-label="Search events" /></label>
          <button className={`filter-chip ${conflictsOnly ? 'is-active' : ''}`} aria-pressed={conflictsOnly} onClick={() => setConflictsOnly((value) => !value)}>Conflicts only</button>
        </div>
        <SectionTitle title="Recorded activity" description="Simulation time, agent, patient, resource and actual outcome." />
        {filtered.length === 0 ? <EmptyState title="No matching events" description={events.length ? 'Change the search or conflict filter.' : 'Process an emergency to create backend events.'} /> : (
          <div className="timeline-list">
            {filtered.map((event, index) => <article className={`timeline-event ${event.is_conflict ? 'timeline-event-conflict' : ''}`} key={event.id || `${event.simulation_time}-${event.event_type}-${index}`}>
              <time className="timeline-time">T+{Number(event.simulation_time || 0).toFixed(1)}m</time>
              <div className="timeline-body">
                <div className="timeline-heading"><strong>{event.event_type}</strong><span className="timeline-agent">{event.agent}</span><span className={`status-pill ${event.outcome === 'SUCCESS' ? 'is-complete' : event.is_conflict ? 'is-waiting' : ''}`}>{event.outcome}</span></div>
                <p>{event.description}</p>
                <small>{event.patient_id ? `Patient ${event.patient_id}` : 'Hospital event'}{event.resource_id ? ` · Resource ${event.resource_id}` : ''}</small>
              </div>
            </article>)}
          </div>
        )}
      </section>
    </div>
  );
}