import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { config } from '../config/config';

const ApiPlayground = () => {
  const [selectedEndpoint, setSelectedEndpoint] = useState('');
  const [requestMethod, setRequestMethod] = useState('GET');
  const [requestUrl, setRequestUrl] = useState('');
  const [requestBody, setRequestBody] = useState('');
  const [response, setResponse] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [responseTime, setResponseTime] = useState(0);

  // API endpoint templates
  const endpointTemplates = {
    'Create Session': {
      method: 'POST',
      url: '/api/v1/detection/sessions',
      body: '',
      description: 'Create a new bot detection session'
    },
    'Get Session Status': {
      method: 'GET',
      url: '/api/v1/detection/sessions/{sessionId}/status',
      body: '',
      description: 'Get the current status of a session'
    },
    'Ingest Events': {
      method: 'POST',
      url: '/api/v1/detection/sessions/{sessionId}/events',
      body: JSON.stringify([
        {
          event_type: 'keystroke',
          timestamp: new Date().toISOString(),
          key: 'a',
          element_id: 'input-1',
          element_type: 'input',
          page_url: 'https://example.com',
          screen_width: 1920,
          screen_height: 1080
        }
      ], null, 2),
      description: 'Send events to a session for analysis'
    },
    'Analyze Session': {
      method: 'POST',
      url: '/api/v1/detection/sessions/{sessionId}/analyze',
      body: '',
      description: 'Perform bot detection analysis on a session'
    },
    'Get Dashboard Overview': {
      method: 'GET',
      url: '/api/v1/dashboard/overview?days=7',
      body: '',
      description: 'Get dashboard overview statistics'
    },
    'Get Sessions List': {
      method: 'GET',
      url: '/api/v1/dashboard/sessions?page=1&limit=50',
      body: '',
      description: 'Get paginated list of sessions'
    },
    'Get Session Details': {
      method: 'GET',
      url: '/api/v1/dashboard/sessions/{sessionId}/details',
      body: '',
      description: 'Get detailed information about a session'
    },
    'Get Analytics Trends': {
      method: 'GET',
      url: '/api/v1/dashboard/analytics/trends?days=30&interval=day',
      body: '',
      description: 'Get analytics trends data'
    },
    'Health Check': {
      method: 'GET',
      url: '/health',
      body: '',
      description: 'Check API health status'
    },
    'Get Integration Status': {
      method: 'GET',
      url: '/api/v1/integrations/status',
      body: '',
      description: 'Get status of all integrations'
    },
    'Submit Survey Question': {
      method: 'POST',
      url: '/api/v1/text-analysis/questions',
      body: JSON.stringify({
        session_id: 'test-session-123',
        question_text: 'What is your favorite color?',
        question_type: 'open_ended',
        element_id: 'question-1',
        element_type: 'textarea',
        page_url: 'https://example.com/survey',
        page_title: 'Survey Page'
      }, null, 2),
      description: 'Submit a survey question for text analysis tracking'
    },
    'Submit Survey Response': {
      method: 'POST',
      url: '/api/v1/text-analysis/responses',
      body: JSON.stringify({
        session_id: 'test-session-123',
        question_id: 'question-456',
        response_text: 'I really like blue because it reminds me of the ocean.',
        response_time_ms: 2500
      }, null, 2),
      description: 'Submit a survey response for real-time text quality analysis'
    },
    'Get Text Analysis Stats': {
      method: 'GET',
      url: '/api/v1/text-analysis/stats',
      body: '',
      description: 'Get OpenAI API usage statistics and performance metrics'
    },
    'Batch Analyze Responses': {
      method: 'POST',
      url: '/api/v1/text-analysis/batch-analyze',
      body: JSON.stringify([
        {
          question: 'What is your favorite color?',
          answer: 'I really like blue because it reminds me of the ocean.'
        },
        {
          question: 'Describe your ideal vacation.',
          answer: 'I want to go to Hawaii and relax on the beach.'
        }
      ], null, 2),
      description: 'Analyze multiple question-answer pairs in batch'
    },
    'Get Text Analysis Dashboard Summary': {
      method: 'GET',
      url: '/api/v1/text-analysis/dashboard/summary?days=7',
      body: '',
      description: 'Get aggregated text quality statistics for dashboard'
    },
    'Get Respondent Analysis': {
      method: 'GET',
      url: '/api/v1/text-analysis/dashboard/respondents?days=30&page=1&limit=50',
      body: '',
      description: 'Get respondent-level text analysis data with all findings'
    },
    'Get Text Analysis Health': {
      method: 'GET',
      url: '/api/v1/text-analysis/health',
      body: '',
      description: 'Check text analysis service health and OpenAI availability'
    },
    'Get Survey Text Analysis Summary': {
      method: 'GET',
      url: '/api/v1/surveys/{surveyId}/text-analysis/summary',
      body: '',
      description: 'Get text analysis summary for a survey (hierarchical V2)'
    },
    'Get Platform Text Analysis Summary': {
      method: 'GET',
      url: '/api/v1/surveys/{surveyId}/platforms/{platformId}/text-analysis/summary',
      body: '',
      description: 'Get text analysis summary for a platform within a survey (hierarchical V2)'
    },
    'Get Respondent Text Analysis Summary': {
      method: 'GET',
      url: '/api/v1/surveys/{surveyId}/platforms/{platformId}/respondents/{respondentId}/text-analysis/summary',
      body: '',
      description: 'Get text analysis summary for a respondent (hierarchical V2)'
    },
    'Get Session Text Analysis (Hierarchical)': {
      method: 'GET',
      url: '/api/v1/surveys/{surveyId}/platforms/{platformId}/respondents/{respondentId}/sessions/{sessionId}/text-analysis',
      body: '',
      description: 'Get text analysis summary for a session via hierarchical path (V2)'
    }
  };

  const handleEndpointSelect = (endpointName) => {
    const template = endpointTemplates[endpointName];
    setSelectedEndpoint(endpointName);
    setRequestMethod(template.method);
    setRequestUrl(template.url);
    setRequestBody(template.body);
  };

  const handleSendRequest = async () => {
    setIsLoading(true);
    setResponse('');
    setResponseTime(0);

    try {
      const startTime = Date.now();
      
      // Replace placeholders in URL
      let finalUrl = requestUrl;
      if (finalUrl.includes('{sessionId}')) {
        finalUrl = finalUrl.replace('{sessionId}', 'test-session-123');
      }
      if (finalUrl.includes('{surveyId}')) {
        finalUrl = finalUrl.replace('{surveyId}', 'SV_1234567890abcdef');
      }
      if (finalUrl.includes('{platformId}')) {
        finalUrl = finalUrl.replace('{platformId}', 'qualtrics');
      }
      if (finalUrl.includes('{respondentId}')) {
        finalUrl = finalUrl.replace('{respondentId}', 'RSP_1234567890abcdef');
      }

      // Use the deployed backend URL from config
      const apiBase = config.apiBase;
      
      const requestConfig = {
        method: requestMethod.toLowerCase(),
        url: `${apiBase}${finalUrl}`,
        headers: {
          'Content-Type': 'application/json',
        },
      };

      if (requestBody && requestMethod !== 'GET') {
        try {
          requestConfig.data = JSON.parse(requestBody);
        } catch (e) {
          toast.error('Invalid JSON in request body');
          setIsLoading(false);
          return;
        }
      }

      const response = await fetch(requestConfig.url, {
        method: requestConfig.method,
        headers: requestConfig.headers,
        body: requestConfig.method !== 'GET' ? JSON.stringify(requestConfig.data) : undefined,
      });

      const endTime = Date.now();
      setResponseTime(endTime - startTime);

      const responseData = await response.text();
      
      let formattedResponse;
      try {
        const parsed = JSON.parse(responseData);
        formattedResponse = JSON.stringify(parsed, null, 2);
      } catch {
        formattedResponse = responseData;
      }

      setResponse(`Status: ${response.status} ${response.statusText}\n\n${formattedResponse}`);
      
      if (response.ok) {
        toast.success('Request completed successfully');
      } else {
        toast.error(`Request failed: ${response.status}`);
      }
    } catch (error) {
      setResponse(`Error: ${error.message}`);
      toast.error('Request failed');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const formatJson = () => {
    try {
      const parsed = JSON.parse(requestBody);
      setRequestBody(JSON.stringify(parsed, null, 2));
      toast.success('JSON formatted');
    } catch (e) {
      toast.error('Invalid JSON');
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">API Playground</h1>
        <p className="text-gray-600 mb-6">
          Test and explore the Bot Detection API endpoints with this interactive playground.
        </p>

        {/* Endpoint Templates */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">Quick Templates</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.keys(endpointTemplates).map((endpoint) => (
              <button
                key={endpoint}
                onClick={() => handleEndpointSelect(endpoint)}
                className={`p-3 text-left rounded-lg border transition-colors ${
                  selectedEndpoint === endpoint
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                <div className="font-medium text-sm">{endpoint}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {endpointTemplates[endpoint].description}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Request Configuration */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Request Panel */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-800">Request</h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Method
              </label>
              <select
                value={requestMethod}
                onChange={(e) => setRequestMethod(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                URL
              </label>
              <input
                type="text"
                value={requestUrl}
                onChange={(e) => setRequestUrl(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="/api/v1/endpoint"
              />
            </div>

            {requestMethod !== 'GET' && (
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Request Body (JSON)
                  </label>
                  <div className="space-x-2">
                    <button
                      onClick={formatJson}
                      className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded"
                    >
                      Format
                    </button>
                    <button
                      onClick={() => copyToClipboard(requestBody)}
                      className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded"
                    >
                      Copy
                    </button>
                  </div>
                </div>
                <textarea
                  value={requestBody}
                  onChange={(e) => setRequestBody(e.target.value)}
                  rows={8}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder="Enter JSON request body..."
                />
              </div>
            )}

            <button
              onClick={handleSendRequest}
              disabled={isLoading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Sending...' : 'Send Request'}
            </button>
          </div>

          {/* Response Panel */}
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-800">Response</h2>
              {responseTime > 0 && (
                <span className="text-sm text-gray-500">
                  Response time: {responseTime}ms
                </span>
              )}
            </div>
            
            <div className="relative">
              <div className="absolute top-2 right-2">
                <button
                  onClick={() => copyToClipboard(response)}
                  className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded"
                >
                  Copy
                </button>
              </div>
              <textarea
                value={response}
                readOnly
                rows={12}
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 font-mono text-sm"
                placeholder="Response will appear here..."
              />
            </div>
          </div>
        </div>

        {/* API Documentation Link */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <h3 className="font-semibold text-blue-900 mb-2">Need More Help?</h3>
          <p className="text-blue-700 text-sm mb-3">
            For detailed API documentation, examples, and SDK usage, visit the full API docs.
          </p>
          <a
            href={config.apiDocsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            Open API Documentation
          </a>
        </div>
      </div>
    </div>
  );
};

export default ApiPlayground; 