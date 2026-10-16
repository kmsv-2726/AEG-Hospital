import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import EmergencyModal from './components/EmergencyModal';
import OverviewPage from './pages/OverviewPage';
import PatientQueuePage from './pages/PatientQueuePage';
import AgentMonitorPage from './pages/AgentMonitorPage';
import EventTimelinePage from './pages/EventTimelinePage';
import MetricsPage from './pages/MetricsPage';
import api from './services/api';

export default function App() {
  const queryParams = new URLSearchParams(window.location.search);
  const [activeTab, setActiveTab] = useState(queryParams.get('tab') || 'overview');
  const [strategy, setStrategy] = useState('PRIORITY_AWARE');
  const [isRunning, setIsRunning] = useState(false);
  const [isEmergencyModalOpen, setIsEmergencyModalOpen] = useState(false);

  const [patients, setPatients] = useState([]);
  const [resources, setResources] = useState(null);
  const [agents, setAgents] = useState([]);
  const [events, setEvents] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [baselineData, setBaselineData] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  // Load all system state from API
  const refreshData = useCallback(async () => {
    try {
      const [pts, rsc, ags, evts, met, base] = await Promise.allSettled([
        api.getPatients(),
        api.getResources(),
        api.getAgents(),
        api.getEvents(),
        api.getMetrics(),
        api.getBaselineComparison(),
      ]);

      if (pts.status === 'fulfilled') setPatients(pts.value);
      if (rsc.status === 'fulfilled') setResources(rsc.value);
      if (ags.status === 'fulfilled') setAgents(ags.value);
      if (evts.status === 'fulfilled') setEvents(evts.value);
      if (met.status === 'fulfilled') setMetrics(met.value);
      if (base.status === 'fulfilled') setBaselineData(base.value);
      setErrorMsg(null);
    } catch (err) {
      console.error('Failed to sync simulation state:', err);
      setErrorMsg('Cannot connect to FastAPI backend at http://127.0.0.1:8000. Please ensure the backend is running.');
    }
  }, []);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  const handleRunSimulation = async () => {
    try {
      setIsRunning(true);
      await api.startSimulation(strategy);
      await refreshData();
    } catch (err) {
      console.error('Simulation execution error:', err);
      alert('Error running simulation: ' + err.message);
    } finally {
      setIsRunning(false);
    }
  };

  const handleResetSimulation = async () => {
    try {
      setIsRunning(true);
      await api.resetSimulation();
      await refreshData();
    } catch (err) {
      console.error('Simulation reset error:', err);
    } finally {
      setIsRunning(false);
    }
  };

  const handleSubmitEmergency = async (patientData) => {
    try {
      await api.submitEmergency(patientData);
      await refreshData();
    } catch (err) {
      console.error('Emergency submission error:', err);
      alert('Failed to register emergency: ' + err.message);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        strategy={strategy}
        setStrategy={setStrategy}
        onRunSimulation={handleRunSimulation}
        onResetSimulation={handleResetSimulation}
        onOpenEmergencyModal={() => setIsEmergencyModalOpen(true)}
        isRunning={isRunning}
      />

      {errorMsg && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          borderBottom: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#fca5a5',
          padding: '10px 24px',
          fontSize: '0.825rem',
          textAlign: 'center',
        }}>
          {errorMsg}
        </div>
      )}

      <main style={{ flex: 1, maxWidth: '1440px', width: '100%', margin: '0 auto', padding: '24px 24px 60px 24px' }}>
        {activeTab === 'overview' && (
          <OverviewPage
            patients={patients}
            resources={resources}
            metrics={metrics}
            strategy={strategy}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === 'patients' && (
          <PatientQueuePage
            patients={patients}
            onOpenEmergencyModal={() => setIsEmergencyModalOpen(true)}
          />
        )}

        {activeTab === 'agents' && (
          <AgentMonitorPage
            agents={agents}
            resources={resources}
          />
        )}

        {activeTab === 'timeline' && (
          <EventTimelinePage
            events={events}
          />
        )}

        {activeTab === 'metrics' && (
          <MetricsPage
            metrics={metrics}
            baselineData={baselineData}
          />
        )}
      </main>

      <EmergencyModal
        isOpen={isEmergencyModalOpen}
        onClose={() => setIsEmergencyModalOpen(false)}
        onSubmit={handleSubmitEmergency}
      />
    </div>
  );
}
