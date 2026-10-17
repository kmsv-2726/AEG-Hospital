import React, { useState } from 'react';
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { AlertTriangle, CheckCircle2, Clock3, Users } from 'lucide-react';
import { EmptyState, PageHeader, SectionTitle, StatTile } from '../components/OperationsUI';

function formatValue(value, suffix = '') {
  return value === null || value === undefined ? '—' : `${value}${suffix}`;
}

export default function MetricsPage({ metrics, baselineData }) {
  const [selectedCohort, setSelectedCohort] = useState('workload_20');
  const cohort = baselineData?.[selectedCohort];
  const fifo = cohort?.FIFO;
  const priority = cohort?.PRIORITY_AWARE;
  const priorityChart = fifo && priority ? ['P1', 'P2', 'P3', 'P4'].map((level) => ({
    priority: level,
    FIFO: fifo[`${level.toLowerCase()}_average_wait_to_doctor`],
    Priority: priority[`${level.toLowerCase()}_average_wait_to_doctor`],
  })) : [];

  const comparisons = fifo && priority ? [
    ['Mean queue wait (min)', fifo.average_waiting_time, priority.average_waiting_time],
    ['Ambulance response (min)', fifo.average_ambulance_response_time, priority.average_ambulance_response_time],
    ['Doctor wait (min)', fifo.average_time_to_doctor, priority.average_time_to_doctor],
    ['Diagnostic wait (min)', fifo.average_time_to_diagnostics, priority.average_time_to_diagnostics],
    ['ICU wait (min)', fifo.average_time_to_icu, priority.average_time_to_icu],
    ['Successful resource assignments', fifo.successful_resource_assignments, priority.successful_resource_assignments],
    ['Delayed patients at run end', fifo.delayed_patients, priority.delayed_patients],
    ['Allocation conflicts', fifo.resource_conflicts, priority.resource_conflicts],
    ['Unresolved requests', fifo.unresolved_requests, priority.unresolved_requests],
    ['Completion rate', fifo.completion_rate, priority.completion_rate, '%'],
    ['Ambulance utilization', fifo.ambulance_utilization, priority.ambulance_utilization, '%'],
    ['Doctor utilization', fifo.doctor_utilization, priority.doctor_utilization, '%'],
    ['Diagnostic utilization', fifo.diagnostic_utilization, priority.diagnostic_utilization, '%'],
    ['ICU utilization', fifo.icu_utilization, priority.icu_utilization, '%'],
  ] : [];

  return (
    <div className="page-stack">
      <PageHeader eyebrow="MEASURED SIMULATION RESULTS" title="Metrics and evaluation" description="Paired synthetic workloads; both policies receive the same patients, arrivals, capacities and processing durations." />

      <section className="page-section">
        <SectionTitle title="Current simulation run" description={`Policy: ${metrics?.strategy || 'Not run'} · simulated duration ${formatValue(metrics?.simulation_duration, ' min')}`} />
        {!metrics ? <EmptyState title="No current run metrics" description="Run the simulation to populate live measurements." /> : <div className="stat-grid">
          <StatTile label="Average queue wait" value={formatValue(metrics.average_waiting_time, ' min')} detail="Ambulance dispatch, doctor, diagnostics and ICU queues" icon={Clock3} tone="teal" />
          <StatTile label="Completed workflows" value={`${metrics.completed_workflows}/${metrics.total_patients}`} detail={`${metrics.workflow_completion_rate}% completion`} icon={CheckCircle2} tone="green" />
          <StatTile label="Unresolved requests" value={metrics.unresolved_requests} detail="Waiting or unassigned at current run end" icon={Users} tone="amber" />
          <StatTile label="Allocation conflicts" value={metrics.resource_conflicts} detail="Rejected allocation attempts, including retries" icon={AlertTriangle} tone="red" />
        </div>}
        {metrics && <div className="utilization-strip">{[
          ['Ambulances', metrics.ambulance_utilization], ['Doctors', metrics.doctor_utilization],
          ['Diagnostics', metrics.diagnostic_utilization], ['ICU', metrics.icu_utilization],
        ].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}%</strong></div>)}</div>}
      </section>

      <section className="page-section">
        <div className="evaluation-heading">
          <SectionTitle title="FIFO versus priority-aware scheduling" description="Means are computed across paired fixed-seed repetitions; no policy is assumed to win." />
          <label className="inline-select">Workload
            <select value={selectedCohort} onChange={(event) => setSelectedCohort(event.target.value)}>
              <option value="workload_5">5 patients</option>
              <option value="workload_20">20 patients</option>
            </select>
          </label>
        </div>
        {!cohort ? <EmptyState title="Evaluation data unavailable" description="Run scripts/evaluate_baseline.py to generate measured comparison data." /> : <>
          <div className="experiment-meta">
            <span>{cohort.FIFO.total_patients} patients per run</span>
            <span>{cohort.FIFO.runs} paired runs</span>
            <span>Seeds: {cohort.FIFO.seeds?.join(', ')}</span>
            <span>Resource setup fingerprint: {cohort.FIFO.per_seed?.[0]?.resource_fingerprint?.slice(0, 12) || 'not recorded'}</span>
          </div>
          <div className="priority-chart">
            <h3>Doctor waiting time by priority</h3>
            <div className="chart-frame"><ResponsiveContainer width="100%" height="100%">
              <BarChart data={priorityChart} margin={{ top: 8, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid stroke="#e7edef" strokeDasharray="3 3" />
                <XAxis dataKey="priority" stroke="#667985" />
                <YAxis stroke="#667985" />
                <Tooltip contentStyle={{ background: '#fff', border: '1px solid #dce4e7', borderRadius: 6, color: '#1f2a37' }} />
                <Legend />
                <Bar dataKey="FIFO" fill="#78909c" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Priority" fill="#087e8b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer></div>
          </div>
          <div className="table-wrap comparison-table-wrap"><table className="data-table">
            <thead><tr><th>Metric</th><th>FIFO mean</th><th>FIFO SD</th><th>Priority mean</th><th>Priority SD</th></tr></thead>
            <tbody>{comparisons.map(([label, fifoValue, priorityValue, suffix = '']) => <tr key={label}>
              <td>{label}</td><td>{formatValue(fifoValue, suffix)}</td><td>{formatValue(fifo.standard_deviation?.[labelToMetric(label)])}</td>
              <td>{formatValue(priorityValue, suffix)}</td><td>{formatValue(priority.standard_deviation?.[labelToMetric(label)])}</td>
            </tr>)}</tbody>
          </table></div>
          <p className="limitations-note">Results describe only these synthetic scenarios. Response time is request-to-hospital arrival; queue waits are calculated only for requests that received the resource within the run. They are not evidence of clinical or real-world performance.</p>
        </>}
      </section>
    </div>
  );
}

function labelToMetric(label) {
  return {
    'Mean queue wait (min)': 'average_waiting_time',
    'Ambulance response (min)': 'average_ambulance_response_time',
    'Doctor wait (min)': 'average_time_to_doctor',
    'Diagnostic wait (min)': 'average_time_to_diagnostics',
    'ICU wait (min)': 'average_time_to_icu',
    'Successful resource assignments': 'successful_resource_assignments',
    'Delayed patients at run end': 'delayed_patients',
    'Allocation conflicts': 'resource_conflicts',
    'Unresolved requests': 'unresolved_requests',
    'Completion rate': 'completion_rate',
    'Ambulance utilization': 'ambulance_utilization',
    'Doctor utilization': 'doctor_utilization',
    'Diagnostic utilization': 'diagnostic_utilization',
    'ICU utilization': 'icu_utilization',
  }[label];
}