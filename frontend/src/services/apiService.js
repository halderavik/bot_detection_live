import axios from 'axios';
import { config } from '../config/config';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: config.apiBaseUrl,
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
  // Get overview statistics - using the actual backend endpoint
  getOverviewStats: async (days = 7) => {
    return api.get(`/dashboard/overview?days=${days}`);
  },

  // Get sessions list - using the actual backend endpoint
  getSessionsList: async (page = 1, limit = 50, filters = {}) => {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...filters,
    });
    return api.get(`/dashboard/sessions?${params}`);
  },

  // Get session details - using the actual backend endpoint
  getSessionDetails: async (sessionId) => {
    return api.get(`/dashboard/sessions/${sessionId}/details`);
  },

  // Get analytics trends - using the actual backend endpoint
  getAnalyticsTrends: async (days = 30, interval = 'day') => {
    return api.get(`/dashboard/analytics/trends?days=${days}&interval=${interval}`);
  },

  // Get metrics summary - using the new backend endpoint
  getMetricsSummary: async (startDate = null, endDate = null) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    return api.get(`/dashboard/metrics/summary?${params}`);
  },

  // Get time series data - using the new backend endpoint
  getTimeseriesData: async (interval = 'hour', days = 7) => {
    return api.get(`/dashboard/metrics/timeseries?interval=${interval}&days=${days}`);
  },

  // Get event breakdown - using the new backend endpoint
  getEventBreakdown: async (startDate = null, endDate = null) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    return api.get(`/dashboard/metrics/event-breakdown?${params}`);
  },

  // Get recent sessions - using the new backend endpoint
  getRecentSessions: async (limit = 10) => {
    return api.get(`/dashboard/sessions/recent?limit=${limit}`);
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
    try {
      const response = await api.get('/integrations/status');
      console.log('Integration status response:', response);
      return response;
    } catch (error) {
      console.error('Integration status failed:', error);
      // Return default status if integration check fails
      return {
        qualtrics: { enabled: false, configured: false },
        decipher: { enabled: false, configured: false }
      };
    }
  },
};

// Hierarchical Services (V2 API)
export const hierarchicalService = {
  // Survey level
  getSurveys: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);
    return api.get(`/surveys?${params}`);
  },

  getSurveyDetails: async (surveyId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    return api.get(`/surveys/${surveyId}?${params}`);
  },

  getSurveySummary: async (surveyId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    return api.get(`/surveys/${surveyId}/summary?${params}`);
  },

  // Platform level
  getPlatforms: async (surveyId) => {
    return api.get(`/surveys/${surveyId}/platforms`);
  },

  getPlatformDetails: async (surveyId, platformId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    return api.get(`/surveys/${surveyId}/platforms/${platformId}?${params}`);
  },

  getPlatformSummary: async (surveyId, platformId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    return api.get(`/surveys/${surveyId}/platforms/${platformId}/summary?${params}`);
  },

  // Respondent level
  getRespondents: async (surveyId, platformId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);
    return api.get(`/surveys/${surveyId}/platforms/${platformId}/respondents?${params}`);
  },

  getRespondentDetails: async (surveyId, platformId, respondentId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    return api.get(`/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}?${params}`);
  },

  getRespondentSummary: async (surveyId, platformId, respondentId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    return api.get(`/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/summary?${params}`);
  },

  getRespondentSessions: async (surveyId, platformId, respondentId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);
    return api.get(`/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/sessions?${params}`);
  },

  // Session level (hierarchical path)
  getSessionByHierarchy: async (surveyId, platformId, respondentId, sessionId) => {
    return api.get(`/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/sessions/${sessionId}`);
  }
};

// Report Services
export const reportService = {
  // Get available surveys for report generation
  getAvailableSurveys: async () => {
    return api.get('/reports/surveys');
  },

  // Generate summary report
  getSummaryReport: async (surveyId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.includeInactive) params.append('include_inactive', 'true');
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    
    return api.get(`/reports/summary/${surveyId}?${params}`);
  },

  // Generate detailed report
  getDetailedReport: async (surveyId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.includeInactive) params.append('include_inactive', 'true');
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    
    return api.get(`/reports/detailed/${surveyId}?${params}`);
  },

  // Download detailed report as CSV
  downloadDetailedReportCSV: async (surveyId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.includeInactive) params.append('include_inactive', 'true');
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    
    return api.get(`/reports/detailed/${surveyId}/csv?${params}`, {
      responseType: 'blob'
    });
  },

  // Download summary report as PDF
  downloadSummaryReportPDF: async (surveyId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.includeInactive) params.append('include_inactive', 'true');
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    
    return api.get(`/reports/summary/${surveyId}/pdf?${params}`);
  },

  // Generate report with custom request
  generateReport: async (request) => {
    return api.post('/reports/generate', request);
  },
};

// Health check
export const healthService = {
  checkHealth: async () => {
    try {
      // Call the root /health endpoint directly
      const response = await axios.get(config.healthUrl, { timeout: 5000 });
      console.log('Health check response:', response.data);
      return response.data; // Return the data part of the response
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  },
};

// Text Analysis Services
export const textAnalysisService = {
  // Get dashboard summary statistics
  getDashboardSummary: async (days = 7, surveyId = null) => {
    const params = new URLSearchParams();
    params.append('days', days.toString());
    if (surveyId) {
      params.append('survey_id', surveyId);
    }
    return api.get(`/text-analysis/dashboard/summary?${params}`);
  },

  // Get respondent-level analysis data
  getRespondentAnalysis: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.surveyId) params.append('survey_id', filters.surveyId);
    if (filters.days) params.append('days', filters.days.toString());
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.limit) params.append('limit', filters.limit.toString());
    
    return api.get(`/text-analysis/dashboard/respondents?${params}`);
  },

  // Get session text quality summary
  getSessionSummary: async (sessionId) => {
    return api.get(`/text-analysis/sessions/${sessionId}/summary`);
  },

  // Submit survey question
  submitQuestion: async (questionData) => {
    return api.post('/text-analysis/questions', questionData);
  },

  // Submit survey response
  submitResponse: async (responseData) => {
    return api.post('/text-analysis/responses', responseData);
  },

  // Get text analysis statistics
  getStats: async () => {
    return api.get('/text-analysis/stats');
  },

  // Batch analyze responses
  batchAnalyze: async (questionsAndAnswers) => {
    return api.post('/text-analysis/batch-analyze', questionsAndAnswers);
  },

  // Get text analysis health
  getHealth: async () => {
    return api.get('/text-analysis/health');
  },

  // Hierarchical text analysis methods (V2 API)
  getTextAnalysisBySurvey: async (surveyId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    return api.get(`/surveys/${surveyId}/text-analysis/summary?${params}`);
  },

  getTextAnalysisByPlatform: async (surveyId, platformId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    return api.get(`/surveys/${surveyId}/platforms/${platformId}/text-analysis/summary?${params}`);
  },

  getTextAnalysisByRespondent: async (surveyId, platformId, respondentId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    return api.get(`/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/text-analysis/summary?${params}`);
  },

  getTextAnalysisBySession: async (surveyId, platformId, respondentId, sessionId) => {
    return api.get(`/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/sessions/${sessionId}/text-analysis`);
  }
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