import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import EmergencyModal from './components/EmergencyModal';
import OrchestrationModal from './components/OrchestrationModal';
import OverviewPage from './pages/OverviewPage';
import PatientQueuePage from './pages/PatientQueuePage';
import AgentMonitorPage from './pages/AgentMonitorPage';
import EventTimelinePage from './pages/EventTimelinePage';
import MetricsPage from './pages/MetricsPage';
import api from './services/api';

function getApiErrorMessage(error) {
  return error.response?.data?.detail || error.message || 'Unknown API error';
}

export default function App() {
  const queryParams = new URLSearchParams(window.location.search);
  const [activeTab, setActiveTab] = useState(queryParams.get('tab') || 'overview');
  const [strategy, setStrategy] = useState('PRIORITY_AWARE');
  const [isRunning, setIsRunning] = useState(false);
  const [isEmergencyModalOpen, setIsEmergencyModalOpen] = useState(false);
  
  // Orchestration Inspection State
  const [selectedPatientForOrchestration, setSelectedPatientForOrchestration] = useState(null);
  const [isOrchestrationModalOpen, setIsOrchestrationModalOpen] = useState(false);

  const [patients, setPatients] = useState([]);
  const [resources, setResources] = useState(null);
  const [agents, setAgents] = useState([]);
  const [events, setEvents] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [baselineData, setBaselineData] = useState(null);
  const [osStatus, setOsStatus] = useState(null);
  const [messages, setMessages] = useState([]);
  const [errorMsg, setErrorMsg] = useState(null);

  // Load all system state from API
  const refreshData = useCallback(async () => {
    try {
      const [pts, rsc, ags, evts, met, base, os, msgs] = await Promise.allSettled([
        api.getPatients(),
        api.getResources(),
        api.getAgents(),
        api.getEvents(),
        api.getMetrics(),
        api.getBaselineComparison(),
        api.getOsStatus(),
        api.getMessages(),
      ]);

      if (pts.status === 'fulfilled') setPatients(pts.value);
      if (rsc.status === 'fulfilled') setResources(rsc.value);
      if (ags.status === 'fulfilled') setAgents(ags.value);
      if (evts.status === 'fulfilled') setEvents(evts.value);
      if (met.status === 'fulfilled') setMetrics(met.value);
      if (base.status === 'fulfilled') setBaselineData(base.value);
      if (os.status === 'fulfilled') setOsStatus(os.value);
      if (msgs.status === 'fulfilled') setMessages(msgs.value);
      const failedRequest = [pts, rsc, ags, evts, met, base, os, msgs]
        .find((result) => result.status === 'rejected');
      setErrorMsg(failedRequest
        ? failedRequest.reason?.response?.data?.detail || failedRequest.reason?.message || 'Some hospital state could not be refreshed.'
        : null);
    } catch (err) {
      console.error('Failed to sync simulation state:', err);
      setErrorMsg('Cannot connect to FastAPI backend at http://127.0.0.1:8000. Please ensure the backend is running.');
    }
  }, []);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  useEffect(() => {
    const intervalId = window.setInterval(refreshData, 5000);
    return () => window.clearInterval(intervalId);
  }, [refreshData]);

  const handleRunSimulation = async () => {
    try {
      setIsRunning(true);
      await api.startSimulation(strategy);
      await refreshData();
    } catch (err) {
      console.error('Simulation execution error:', err);
      alert('Error running simulation: ' + getApiErrorMessage(err));
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
      setIsRunning(true);
      const createdPatient = await api.submitEmergency(patientData);
      await refreshData();
      
      // Immediately open the live AI orchestration modal for the user
      setSelectedPatientForOrchestration(createdPatient);
      setIsOrchestrationModalOpen(true);
      return createdPatient;
    } catch (err) {
      console.error('Emergency submission error:', err);
      throw err;
    } finally {
      setIsRunning(false);
    }
  };

  const handleOpenOrchestration = (patient) => {
    setSelectedPatientForOrchestration(patient);
    setIsOrchestrationModalOpen(true);
  };

  return (
    <div className="app-shell">
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
        <div className="app-error" role="alert">
          {errorMsg}
        </div>
      )}

      <main className="app-main">
        {activeTab === 'overview' && (
          <OverviewPage
            patients={patients}
            resources={resources}
            metrics={metrics}
            strategy={strategy}
            setActiveTab={setActiveTab}
            onViewOrchestration={handleOpenOrchestration}
            events={events}
          />
        )}

        {activeTab === 'patients' && (
          <PatientQueuePage
            patients={patients}
            onOpenEmergencyModal={() => setIsEmergencyModalOpen(true)}
            onViewOrchestration={handleOpenOrchestration}
          />
        )}

        {activeTab === 'agents' && (
          <AgentMonitorPage
            agents={agents}
            resources={resources}
            osStatus={osStatus}
            messages={messages}
            onViewOrchestration={handleOpenOrchestration}
            patients={patients}
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

      {/* Synthetic Emergency Registration Dialog */}
      <EmergencyModal
        isOpen={isEmergencyModalOpen}
        onClose={() => setIsEmergencyModalOpen(false)}
        onSubmit={handleSubmitEmergency}
      />

      {/* Autonomous Multi-Agent Orchestration & OS Inspector Dialog */}
      <OrchestrationModal
        isOpen={isOrchestrationModalOpen}
        onClose={() => setIsOrchestrationModalOpen(false)}
        patient={selectedPatientForOrchestration}
        events={events}
      />
    </div>
  );
}
