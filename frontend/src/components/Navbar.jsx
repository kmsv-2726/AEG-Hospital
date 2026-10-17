import React from 'react';
import {
  Activity,
  BarChart3,
  Bot,
  Clock3,
  Play,
  Plus,
  RotateCcw,
  ShieldPlus,
  Users,
} from 'lucide-react';

const navigation = [
  { id: 'overview', label: 'Overview', icon: Activity },
  { id: 'patients', label: 'Patient queue', icon: Users },
  { id: 'agents', label: 'Agent monitor', icon: Bot },
  { id: 'timeline', label: 'Event timeline', icon: Clock3 },
  { id: 'metrics', label: 'Evaluation', icon: BarChart3 },
];

export default function Navbar({
  activeTab,
  setActiveTab,
  strategy,
  setStrategy,
  onRunSimulation,
  onResetSimulation,
  onOpenEmergencyModal,
  isRunning,
}) {
  return (
    <header className="app-header">
      <div className="header-primary">
        <a className="brand-lockup" href="/" aria-label="Hospital simulation overview" onClick={(event) => { event.preventDefault(); setActiveTab('overview'); }}>
          <span className="brand-symbol"><ShieldPlus size={22} /></span>
          <span className="brand-copy">
            <strong>AEG Hospital</strong>
            <small>Emergency coordination simulator</small>
          </span>
        </a>
        <div className="header-controls">
          <label className="strategy-control">
            <span>Policy</span>
            <select aria-label="Scheduling policy" value={strategy} onChange={(event) => setStrategy(event.target.value)}>
              <option value="PRIORITY_AWARE">Priority-aware</option>
              <option value="FIFO">FIFO baseline</option>
            </select>
          </label>
          <button className="btn btn-secondary" onClick={onResetSimulation} disabled={isRunning} title="Reset synthetic cohort and resources">
            <RotateCcw size={16} /><span>Reset</span>
          </button>
          <button className="btn btn-primary" onClick={onRunSimulation} disabled={isRunning}>
            <Play size={15} /><span>{isRunning ? 'Running…' : 'Run simulation'}</span>
          </button>
          <button className="btn btn-accent" onClick={onOpenEmergencyModal} disabled={isRunning}>
            <Plus size={17} /><span>Add emergency</span>
          </button>
        </div>
      </div>
      <nav className="main-navigation" aria-label="Main navigation">
        {navigation.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={`nav-item ${activeTab === id ? 'is-active' : ''}`}
            aria-current={activeTab === id ? 'page' : undefined}
            onClick={() => setActiveTab(id)}
          >
            <Icon size={16} /><span>{label}</span>
          </button>
        ))}
      </nav>
    </header>
  );
}