import React from 'react';
import { 
  Activity, 
  Users, 
  Bot, 
  Clock, 
  BarChart3, 
  ShieldAlert, 
  RotateCcw, 
  Play, 
  PlusCircle 
} from 'lucide-react';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  strategy, 
  setStrategy, 
  onRunSimulation, 
  onResetSimulation, 
  onOpenEmergencyModal,
  isRunning 
}) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'patients', label: 'Patient Queue', icon: Users },
    { id: 'agents', label: 'Agent Monitor', icon: Bot },
    { id: 'timeline', label: 'Event Timeline', icon: Clock },
    { id: 'metrics', label: 'Metrics & Evaluation', icon: BarChart3 },
  ];

  return (
    <header style={{
      background: 'rgba(15, 23, 42, 0.85)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border-subtle)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      padding: '12px 24px',
    }}>
      <div style={{
        maxWidth: '1440px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #06b6d4, #6366f1)',
            padding: '8px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(6, 182, 212, 0.4)'
          }}>
            <ShieldAlert size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: '1.05rem', letterSpacing: '-0.02em', color: '#ffffff' }}>
              AEG SMART HOSPITAL <span style={{ color: 'var(--cyan-primary)', fontSize: '0.8rem', fontWeight: 600, padding: '2px 6px', background: 'rgba(6,182,212,0.15)', borderRadius: '4px', marginLeft: '6px' }}>MAS AI</span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Emergency Response & Resource Optimization Engine
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', gap: '6px', background: 'rgba(0,0,0,0.3)', padding: '4px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 14px',
                  borderRadius: '8px',
                  border: 'none',
                  background: isActive ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(99, 102, 241, 0.2))' : 'transparent',
                  color: isActive ? '#38bdf8' : 'var(--text-muted)',
                  borderBottom: isActive ? '2px solid var(--cyan-primary)' : '2px solid transparent',
                  cursor: 'pointer',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: '0.85rem',
                  transition: 'all 0.2s ease',
                }}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Global Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Strategy Selector */}
          <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(15, 23, 42, 0.9)', padding: '4px 8px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginRight: '6px', fontWeight: 600 }}>STRATEGY:</span>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#38bdf8',
                fontWeight: 600,
                fontSize: '0.8rem',
                cursor: 'pointer',
                outline: 'none',
                fontFamily: 'var(--font-mono)'
              }}
            >
              <option value="PRIORITY_AWARE" style={{ background: '#0f172a', color: '#fff' }}>Priority-Aware MAS</option>
              <option value="FIFO" style={{ background: '#0f172a', color: '#fff' }}>FIFO Baseline</option>
            </select>
          </div>

          {/* New Emergency Button */}
          <button 
            className="btn btn-secondary" 
            onClick={onOpenEmergencyModal}
            title="Inject simulated patient"
            style={{ fontSize: '0.8rem', padding: '7px 12px' }}
          >
            <PlusCircle size={15} color="var(--cyan-primary)" />
            <span>New Emergency</span>
          </button>

          {/* Reset Button */}
          <button 
            className="btn btn-secondary" 
            onClick={onResetSimulation}
            disabled={isRunning}
            title="Reset scenario state"
            style={{ fontSize: '0.8rem', padding: '7px 12px' }}
          >
            <RotateCcw size={15} />
            <span>Reset</span>
          </button>

          {/* Run Button */}
          <button 
            className="btn btn-primary" 
            onClick={onRunSimulation}
            disabled={isRunning}
            style={{ fontSize: '0.8rem', padding: '7px 14px' }}
          >
            <Play size={15} fill="#fff" />
            <span>{isRunning ? 'Simulating...' : 'Run Simulation'}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
