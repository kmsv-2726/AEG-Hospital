import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  getHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },

  getPatients: async () => {
    const res = await apiClient.get('/patients');
    return res.data;
  },

  registerPatient: async (patientData) => {
    const res = await apiClient.post('/patients', patientData);
    return res.data;
  },

  submitEmergency: async (emergencyData) => {
    const res = await apiClient.post('/emergency', emergencyData);
    return res.data;
  },

  getResources: async () => {
    const res = await apiClient.get('/resources');
    return res.data;
  },

  getAgents: async () => {
    const res = await apiClient.get('/agents');
    return res.data;
  },

  getEvents: async () => {
    const res = await apiClient.get('/events');
    return res.data;
  },

  startSimulation: async (strategy = 'PRIORITY_AWARE') => {
    const res = await apiClient.post('/simulation/start', { strategy, step_delay_ms: 0 });
    return res.data;
  },

  resetSimulation: async () => {
    const res = await apiClient.post('/simulation/reset', { preserve_scenario: true });
    return res.data;
  },

  getMetrics: async () => {
    const res = await apiClient.get('/metrics');
    return res.data;
  },

  getBaselineComparison: async () => {
    const res = await apiClient.get('/baseline');
    return res.data;
  },
};

export default api;
