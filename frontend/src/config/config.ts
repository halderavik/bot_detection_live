/**
 * Centralized configuration for the Bot Detection Frontend
 * All URLs and environment-specific values are managed here
 */

// Environment variables with fallbacks
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1';
const FRONTEND_BASE_URL = import.meta.env.VITE_FRONTEND_BASE_URL || 'https://storage.googleapis.com/bot-detection-frontend-20251208';
const APP_NAME = import.meta.env.VITE_APP_NAME || 'Bot Detection Dashboard';

// Derived URLs
const API_BASE = API_BASE_URL.replace('/api/v1', '');
const API_DOCS_URL = `${API_BASE}/docs`;
const TRACKING_CLIENT_URL = `${API_BASE}/static/tracking-client.js`;

// Webhook URLs
const WEBHOOK_BASE_URL = `${API_BASE}/api/v1/integrations/webhooks`;
const QUALTRICS_WEBHOOK_URL = `${WEBHOOK_BASE_URL}/qualtrics`;
const DECIPHER_WEBHOOK_URL = `${WEBHOOK_BASE_URL}/decipher`;

// Dashboard URLs
const DASHBOARD_SESSIONS_EXPORT_URL = `${API_BASE}/api/v1/dashboard/sessions/export`;
const DASHBOARD_SESSION_DETAILS_URL = (sessionId: string) => `${API_BASE}/api/v1/dashboard/sessions/${sessionId}/details`;

// Health check URL
const HEALTH_URL = `${API_BASE}/health`;

export const config = {
  // App info
  appName: APP_NAME,
  
  // Base URLs
  apiBaseUrl: API_BASE_URL,
  frontendBaseUrl: FRONTEND_BASE_URL,
  apiBase: API_BASE,
  
  // Documentation
  apiDocsUrl: API_DOCS_URL,
  
  // Client SDK
  trackingClientUrl: TRACKING_CLIENT_URL,
  
  // Webhooks
  webhooks: {
    base: WEBHOOK_BASE_URL,
    qualtrics: QUALTRICS_WEBHOOK_URL,
    decipher: DECIPHER_WEBHOOK_URL,
  },
  
  // Dashboard endpoints
  dashboard: {
    sessionsExport: DASHBOARD_SESSIONS_EXPORT_URL,
    sessionDetails: DASHBOARD_SESSION_DETAILS_URL,
  },
  
  // Health
  healthUrl: HEALTH_URL,
  
  // Environment info
  isDevelopment: import.meta.env.DEV,
  isProduction: import.meta.env.PROD,
} as const;

// Helper functions for dynamic URLs
export const getApiUrl = (endpoint: string) => `${API_BASE}${endpoint}`;
export const getWebhookUrl = (platform: 'qualtrics' | 'decipher') => 
  platform === 'qualtrics' ? QUALTRICS_WEBHOOK_URL : DECIPHER_WEBHOOK_URL;

// Export individual values for backward compatibility
export const {
  apiBaseUrl,
  frontendBaseUrl,
  apiBase,
  apiDocsUrl,
  trackingClientUrl,
  webhooks,
  dashboard,
  healthUrl,
  appName,
} = config;
