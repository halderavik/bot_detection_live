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

// Survey tracking: add live tracking to a Decipher survey XML
export const trackingService = {
  getDecipherOptions: async () => {
    return api.get('/tracking/decipher/options');
  },

  // file: File; options: { surveyId, terminate, afterPage, signals[], privacyNotice, privacyText }
  addDecipherTracking: async (file, options = {}) => {
    const form = new FormData();
    form.append('file', file);
    if (options.surveyId) form.append('survey_id', options.surveyId);
    form.append('terminate', options.terminate ? 'true' : 'false');
    form.append('after_page', String(options.afterPage || 2));
    if (options.signals && options.signals.length) form.append('signals', options.signals.join(','));
    form.append('privacy_notice', options.privacyNotice ? 'true' : 'false');
    if (options.privacyText) form.append('privacy_text', options.privacyText);
    // Reason: the default JSON header would stop the browser from writing the multipart boundary.
    return api.post('/tracking/decipher', form, {
      headers: { 'Content-Type': undefined },
      timeout: 60000,
    });
  },

  // body: { xml, survey_id, survey_path, create_new }
  uploadToDecipher: async (body) => {
    return api.post('/tracking/decipher/upload', body, { timeout: 120000 });
  },
};

// Settings page: integration keys, tracking options, bot threshold. Saving needs the admin token.
export const settingsService = {
  get: async () => api.get('/settings'),
  checkToken: async (token) => api.post('/settings/check', null, { headers: { 'X-Admin-Token': token } }),
  save: async (token, changes) => api.put('/settings', { changes }, { headers: { 'X-Admin-Token': token } }),
};

// Live quality: per-survey rules, live results, CSV export, and LQ_ variables in a data file.
// The survey id goes in the query string because ids are often titles with spaces.
export const liveQualityService = {
  listSurveys: async () => {
    return api.get('/quality/surveys');
  },

  getResults: async (surveyId) => {
    return api.get('/quality/results', { params: { survey_id: surveyId }, timeout: 120000 });
  },

  exportUrl: (surveyId) => `${config.apiBaseUrl}/quality/export?survey_id=${encodeURIComponent(surveyId)}`,

  getRules: async (surveyId) => {
    return api.get('/quality/rules', { params: { survey_id: surveyId } });
  },

  saveRules: async (surveyId, rules) => {
    return api.put('/quality/rules', rules, { params: { survey_id: surveyId } });
  },

  resetRules: async (surveyId) => {
    return api.delete('/quality/rules', { params: { survey_id: surveyId } });
  },

  // Returns { blob, filename, report }. Reason: the shared client keeps only the body,
  // and the merge report travels in the X-Quality-Report header.
  mergeDataFile: async (surveyId, file) => {
    const form = new FormData();
    form.append('file', file);
    const response = await axios.post(`${config.apiBaseUrl}/quality/merge`, form, {
      params: { survey_id: surveyId },
      responseType: 'blob',
      timeout: 300000,
    });
    const disposition = response.headers['content-disposition'] || '';
    const match = /filename="([^"]+)"/.exec(disposition);
    let report = null;
    try {
      report = JSON.parse(response.headers['x-quality-report'] || 'null');
    } catch (e) {
      report = null;
    }
    return { blob: response.data, filename: match ? match[1] : file.name, report };
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
  },

  // Hierarchical Fraud Detection Methods
  getSurveyFraudSummary: async (surveyId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    return api.get(`/surveys/${surveyId}/fraud/summary?${params}`);
  },

  getPlatformFraudSummary: async (surveyId, platformId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    return api.get(`/surveys/${surveyId}/platforms/${platformId}/fraud/summary?${params}`);
  },

  getRespondentFraudSummary: async (surveyId, platformId, respondentId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    return api.get(`/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/fraud/summary?${params}`);
  },

  getSessionFraudByHierarchy: async (surveyId, platformId, respondentId, sessionId) => {
    return api.get(`/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/sessions/${sessionId}/fraud`);
  },

  // Hierarchical Grid Analysis Methods
  getGridAnalysisSummary: async (surveyId, platformId = null, respondentId = null, sessionId = null, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    
    let url;
    if (sessionId && respondentId && platformId) {
      // Session level
      url = `/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/sessions/${sessionId}/grid-analysis`;
    } else if (respondentId && platformId) {
      // Respondent level
      url = `/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/grid-analysis/summary`;
    } else if (platformId) {
      // Platform level
      url = `/surveys/${surveyId}/platforms/${platformId}/grid-analysis/summary`;
    } else {
      // Survey level
      url = `/surveys/${surveyId}/grid-analysis/summary`;
    }
    
    return api.get(`${url}${params.toString() ? '?' + params.toString() : ''}`);
  },

  // Hierarchical Timing Analysis Methods
  getTimingAnalysisSummary: async (surveyId, platformId = null, respondentId = null, sessionId = null, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.dateFrom) params.append('date_from', filters.dateFrom);
    if (filters.dateTo) params.append('date_to', filters.dateTo);
    
    let url;
    if (sessionId && respondentId && platformId) {
      // Session level
      url = `/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/sessions/${sessionId}/timing-analysis`;
    } else if (respondentId && platformId) {
      // Respondent level
      url = `/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/timing-analysis/summary`;
    } else if (platformId) {
      // Platform level
      url = `/surveys/${surveyId}/platforms/${platformId}/timing-analysis/summary`;
    } else {
      // Survey level
      url = `/surveys/${surveyId}/timing-analysis/summary`;
    }
    
    return api.get(`${url}${params.toString() ? '?' + params.toString() : ''}`);
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

// Fraud Detection Service
export const fraudService = {
  // Get fraud indicators for a session
  getFraudIndicators: async (sessionId) => {
    return api.get(`/fraud/sessions/${sessionId}`);
  },

  // Get sessions by IP address
  getSessionsByIp: async (ipAddress) => {
    return api.get(`/fraud/ip/${ipAddress}`);
  },

  // Get sessions by device fingerprint
  getSessionsByFingerprint: async (fingerprint) => {
    return api.get(`/fraud/fingerprint/${fingerprint}`);
  },

  // Get fraud dashboard summary
  getFraudDashboardSummary: async (surveyId = null, days = 7) => {
    const params = new URLSearchParams({ days: days.toString() });
    if (surveyId) params.append('survey_id', surveyId);
    return api.get(`/fraud/dashboard/summary?${params}`);
  },

  // Get duplicate sessions
  getDuplicateSessions: async (surveyId = null, limit = 50) => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (surveyId) params.append('survey_id', surveyId);
    return api.get(`/fraud/dashboard/duplicates?${params}`);
  },

  // Analyze session fraud
  analyzeSessionFraud: async (sessionId) => {
    return api.post(`/fraud/analyze/${sessionId}`);
  }
};

export default api; 