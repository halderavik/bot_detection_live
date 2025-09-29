import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens if needed
api.interceptors.request.use(
  (config) => {
    // Add any authentication headers here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// Session Management
export const sessionService = {
  // Create a new session
  createSession: async () => {
    return api.post('/detection/sessions');
  },

  // Get session status
  getSessionStatus: async (sessionId) => {
    return api.get(`/detection/sessions/${sessionId}/status`);
  },

  // Ingest events for a session
  ingestEvents: async (sessionId, events) => {
    return api.post(`/detection/sessions/${sessionId}/events`, { events });
  },

  // Analyze a session
  analyzeSession: async (sessionId) => {
    return api.post(`/detection/sessions/${sessionId}/analyze`);
  },
};

// Dashboard Analytics
export const dashboardService = {
  // Get overview statistics
  getOverviewStats: async (days = 7) => {
    return api.get(`/dashboard/overview?days=${days}`);
  },

  // Get sessions list
  getSessionsList: async (page = 1, limit = 50, filters = {}) => {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...filters,
    });
    return api.get(`/dashboard/sessions?${params}`);
  },

  // Get session details
  getSessionDetails: async (sessionId) => {
    return api.get(`/dashboard/sessions/${sessionId}/details`);
  },

  // Get analytics trends
  getAnalyticsTrends: async (days = 30, interval = 'day') => {
    return api.get(`/dashboard/analytics/trends?days=${days}&interval=${interval}`);
  },
};

// Integration Services
export const integrationService = {
  // Get Qualtrics survey info
  getQualtricsSurveyInfo: async (surveyId) => {
    return api.get(`/integrations/qualtrics/surveys/${surveyId}`);
  },

  // Get Decipher survey info
  getDecipherSurveyInfo: async (surveyId) => {
    return api.get(`/integrations/decipher/surveys/${surveyId}`);
  },

  // Get integration status
  getIntegrationStatus: async () => {
    return api.get('/integrations/status');
  },
};

// Health check
export const healthService = {
  checkHealth: async () => {
    // Call the root /health endpoint directly
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
    const healthURL = baseURL.replace('/api/v1', '') + '/health';
    return axios.get(healthURL);
  },
};

// Mock data for development (when backend is not available)
export const mockData = {
  overviewStats: {
    period: {
      start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      end_date: new Date().toISOString(),
      days: 7,
    },
    sessions: {
      total: 1250,
      active: 45,
      completed: 1205,
      avg_duration: 180,
    },
    detections: {
      total: 1250,
      bots_detected: 89,
      humans_confirmed: 1161,
      detection_rate: 7.12,
    },
    events: {
      total: 45678,
      avg_per_session: 36.5,
      keystrokes: 23456,
      mouse_events: 12345,
      scroll_events: 9877,
    },
    platforms: {
      qualtrics: 850,
      decipher: 400,
    },
  },
  sessionsList: {
    sessions: [
      {
        id: 'session-1',
        created_at: new Date().toISOString(),
        last_activity: new Date().toISOString(),
        is_active: true,
        platform: 'qualtrics',
        survey_id: 'SV_123456',
        respondent_id: 'R_789012',
        event_count: 45,
        detection: {
          is_bot: false,
          confidence_score: 0.85,
          risk_level: 'low',
          analyzed_at: new Date().toISOString(),
        },
      },
    ],
    pagination: {
      page: 1,
      limit: 50,
      total: 1250,
      pages: 25,
    },
  },
};

export default api; 