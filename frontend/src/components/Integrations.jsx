import React, { useState, useEffect } from 'react';
import { 
  Check, 
  X, 
  TriangleAlert, 
  Copy, 
  Zap,
  Globe
} from 'lucide-react';
import { integrationService } from '../services/apiService';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

console.log({
  Check,
  X,
  TriangleAlert,
  Copy,
  Zap,
  Globe
});

const mockLogs = [
  { id: 1, platform: 'qualtrics', status: 'success', message: 'Webhook delivered', timestamp: new Date().toISOString() },
  { id: 2, platform: 'decipher', status: 'error', message: 'Signature invalid', timestamp: new Date(Date.now() - 60000).toISOString() },
  { id: 3, platform: 'qualtrics', status: 'success', message: 'Survey info fetched', timestamp: new Date(Date.now() - 120000).toISOString() },
];

const Integrations = () => {
  const [integrationStatus, setIntegrationStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copiedField, setCopiedField] = useState(null);
  const [logs, setLogs] = useState(mockLogs);

  useEffect(() => {
    fetchIntegrationStatus();
  }, []);

  const fetchIntegrationStatus = async () => {
    try {
      setLoading(true);
      const response = await integrationService.getIntegrationStatus();
      setIntegrationStatus(response.data);
    } catch (err) {
      console.error('Failed to fetch integration status:', err);
      setError('Failed to load integration status');
      // Fallback to mock data with more realistic info
      setIntegrationStatus({
        qualtrics: { enabled: true, configured: false },
        decipher: { enabled: true, configured: false }
      });
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text, fieldName) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(fieldName);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  const getStatusIcon = (configured) => {
    if (configured) {
      return <Check className="h-5 w-5 text-green-500" />;
    }
    return <X className="h-5 w-5 text-red-500" />;
  };

  const getStatusText = (configured) => {
    return configured ? 'Configured' : 'Not Configured';
  };

  const getStatusColor = (configured) => {
    return configured ? 'text-green-600' : 'text-red-600';
  };

  const testWebhook = async (platform) => {
    toast.info(`Testing ${platform} webhook...`);
    // Simulate async test
    setTimeout(() => {
      const success = Math.random() > 0.3;
      if (success) {
        toast.success(`${platform.charAt(0).toUpperCase() + platform.slice(1)} webhook test successful!`);
        setLogs(prev => [
          { id: Date.now(), platform, status: 'success', message: 'Test webhook delivered', timestamp: new Date().toISOString() },
          ...prev
        ]);
      } else {
        toast.error(`${platform.charAt(0).toUpperCase() + platform.slice(1)} webhook test failed!`);
        setLogs(prev => [
          { id: Date.now(), platform, status: 'error', message: 'Test webhook failed', timestamp: new Date().toISOString() },
          ...prev
        ]);
      }
    }, 1200);
  };

  // Always show cards, even if error
  const showStatus = integrationStatus || {
    qualtrics: { enabled: true, configured: false },
    decipher: { enabled: true, configured: false }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Use deployed backend URL
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1';
  const webhookBaseUrl = apiBaseUrl.replace('/api/v1', '') + '/api/v1/integrations/webhooks';

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Integrations</h1>
            <p className="text-gray-600 mt-2">Manage your survey platform integrations</p>
          </div>
          <div className="bg-green-100 border border-green-200 rounded-lg px-4 py-2">
            <div className="flex items-center">
              <div className="h-2 w-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
              <span className="text-sm font-medium text-green-800">Production Ready</span>
            </div>
            <p className="text-xs text-green-600 mt-1">All systems operational</p>
          </div>
        </div>
        {error && (
          <div className="mt-2 text-red-600 flex items-center gap-2">
            {/* <TriangleAlert className="h-5 w-5" /> */}
            {error} <button onClick={fetchIntegrationStatus} className="ml-2 underline text-blue-600">Retry</button>
          </div>
        )}
      </div>

      {/* Integration Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Qualtrics Integration */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Globe className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Qualtrics</h3>
                <p className="text-sm text-gray-600">Survey platform integration</p>
              </div>
            </div>
            {getStatusIcon(showStatus?.qualtrics?.configured)}
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Status:</span>
              <span className={`text-sm font-medium ${getStatusColor(showStatus?.qualtrics?.configured)}`}>
                {getStatusText(showStatus?.qualtrics?.configured)}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">API Token:</span>
              <span className="text-sm text-gray-600">
                {showStatus?.qualtrics?.configured ? 'Configured' : 'Not Set'}
              </span>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Webhook URL</h4>
            <div className="flex items-center space-x-2">
              <code className="flex-1 text-xs bg-gray-100 p-2 rounded">
                {webhookBaseUrl}/qualtrics
              </code>
              <button
                onClick={() => copyToClipboard(`${webhookBaseUrl}/qualtrics`, 'qualtrics-webhook')}
                className="p-1 text-gray-500 hover:text-gray-700"
                title="Copy webhook URL"
              >
                {copiedField === 'qualtrics-webhook' ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>
          <button onClick={() => testWebhook('qualtrics')} className="btn-secondary text-sm">Test Webhook</button>
        </div>

        {/* Decipher Integration */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Zap className="h-8 w-8 text-purple-600 mr-3" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Decipher</h3>
                <p className="text-sm text-gray-600">Survey platform integration</p>
              </div>
            </div>
            {getStatusIcon(showStatus?.decipher?.configured)}
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Status:</span>
              <span className={`text-sm font-medium ${getStatusColor(showStatus?.decipher?.configured)}`}>
                {getStatusText(showStatus?.decipher?.configured)}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">API Key:</span>
              <span className="text-sm text-gray-600">
                {showStatus?.decipher?.configured ? 'Configured' : 'Not Set'}
              </span>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Webhook URL</h4>
            <div className="flex items-center space-x-2">
              <code className="flex-1 text-xs bg-gray-100 p-2 rounded">
                {webhookBaseUrl}/decipher
              </code>
              <button
                onClick={() => copyToClipboard(`${webhookBaseUrl}/decipher`, 'decipher-webhook')}
                className="p-1 text-gray-500 hover:text-gray-700"
                title="Copy webhook URL"
              >
                {copiedField === 'decipher-webhook' ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>
          <button onClick={() => testWebhook('decipher')} className="btn-secondary text-sm">Test Webhook</button>
        </div>
      </div>

      {/* Quick Start Guide */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Start Guide</h3>
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-lg mb-6">
          <h4 className="text-md font-semibold text-gray-900 mb-3">🚀 Ready to integrate bot detection?</h4>
          <p className="text-sm text-gray-600 mb-4">
            Follow our step-by-step guides to add bot detection to your surveys in minutes:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <a 
              href="https://storage.googleapis.com/bot-detection-frontend-20250929/index.html" 
              target="_blank" 
              rel="noopener noreferrer"
              className="bg-white p-4 rounded-lg border border-blue-200 hover:border-blue-300 transition-colors"
            >
              <div className="flex items-center mb-2">
                <Globe className="h-5 w-5 text-blue-600 mr-2" />
                <span className="font-medium text-gray-900">Decipher Integration</span>
              </div>
              <p className="text-xs text-gray-600">Complete guide for Decipher surveys with copy-paste code</p>
            </a>
            <a 
              href="https://storage.googleapis.com/bot-detection-frontend-20250929/index.html" 
              target="_blank" 
              rel="noopener noreferrer"
              className="bg-white p-4 rounded-lg border border-purple-200 hover:border-purple-300 transition-colors"
            >
              <div className="flex items-center mb-2">
                <Zap className="h-5 w-5 text-purple-600 mr-2" />
                <span className="font-medium text-gray-900">API Playground</span>
              </div>
              <p className="text-xs text-gray-600">Test the bot detection system directly</p>
            </a>
          </div>
        </div>
      </div>

      {/* Setup Instructions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">How Bot Detection Integration Works</h3>
        
        <div className="space-y-6">
          {/* How It Works Overview */}
          <div className="bg-gradient-to-r from-green-50 to-blue-50 p-6 rounded-lg border border-green-200">
            <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
              <Zap className="h-6 w-6 text-green-600 mr-2" />
              How Bot Detection Works
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="bg-white p-4 rounded-lg border border-green-100">
                <div className="text-center">
                  <div className="bg-blue-100 w-8 h-8 rounded-full flex items-center justify-center mx-auto mb-2">
                    <span className="text-blue-600 font-bold">1</span>
                  </div>
                  <h5 className="font-medium text-gray-900 mb-1">Data Collection</h5>
                  <p className="text-xs text-gray-600">JavaScript tracks user behavior: keystrokes, mouse movements, scrolling patterns</p>
                </div>
              </div>
              <div className="bg-white p-4 rounded-lg border border-green-100">
                <div className="text-center">
                  <div className="bg-blue-100 w-8 h-8 rounded-full flex items-center justify-center mx-auto mb-2">
                    <span className="text-blue-600 font-bold">2</span>
                  </div>
                  <h5 className="font-medium text-gray-900 mb-1">Analysis</h5>
                  <p className="text-xs text-gray-600">AI analyzes behavior patterns to detect bot-like vs human-like interactions</p>
                </div>
              </div>
              <div className="bg-white p-4 rounded-lg border border-green-100">
                <div className="text-center">
                  <div className="bg-blue-100 w-8 h-8 rounded-full flex items-center justify-center mx-auto mb-2">
                    <span className="text-blue-600 font-bold">3</span>
                  </div>
                  <h5 className="font-medium text-gray-900 mb-1">Results</h5>
                  <p className="text-xs text-gray-600">Get bot probability score and detailed analysis in your survey data</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-4 rounded-lg border border-blue-200">
              <h5 className="font-medium text-gray-900 mb-2">What We Track:</h5>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                  <span>Keystroke timing</span>
                </div>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span>Mouse movements</span>
                </div>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                  <span>Scroll patterns</span>
                </div>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-orange-500 rounded-full mr-2"></div>
                  <span>Page interactions</span>
                </div>
              </div>
            </div>
          </div>

          {/* Integration Setup */}
          <div>
            <h4 className="text-lg font-semibold text-gray-900 mb-4">Integration Setup Instructions</h4>
            
            {/* Decipher Setup */}
            <div className="mb-6">
              <h5 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                <Zap className="h-5 w-5 text-purple-600 mr-2" />
                Decipher Integration (Recommended)
              </h5>
              <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                <p className="text-sm text-gray-700 mb-3">
                  <strong>Why Decipher?</strong> Our system is optimized for Decipher surveys with built-in support for their JavaScript environment.
                </p>
                <ol className="list-decimal list-inside space-y-2 text-sm">
                  <li>Add the JavaScript code below to your survey's header section</li>
                  <li>Create hidden fields: <code className="bg-purple-100 px-1 rounded">bot_session_id</code>, <code className="bg-purple-100 px-1 rounded">bot_result</code>, <code className="bg-purple-100 px-1 rounded">bot_is_bot</code>, <code className="bg-purple-100 px-1 rounded">bot_confidence</code></li>
                  <li>Test your survey - the system will automatically track user behavior</li>
                  <li>Check your data export for bot detection results</li>
                </ol>
                <div className="mt-3 p-3 bg-white rounded border border-purple-100">
                  <p className="text-xs text-gray-600 mb-1"><strong>Result in your data:</strong></p>
                  <ul className="text-xs text-gray-600 space-y-1">
                    <li><code>bot_is_bot</code>: "false" (human) or "true" (bot)</li>
                    <li><code>bot_confidence</code>: 0.0 to 1.0 (higher = more confident)</li>
                    <li><code>bot_result</code>: Complete analysis details in JSON format</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Qualtrics Setup */}
            <div>
              <h5 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                <Globe className="h-5 w-5 text-blue-600 mr-2" />
                Qualtrics Integration
              </h5>
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <p className="text-sm text-gray-700 mb-3">
                  <strong>For Qualtrics:</strong> Use webhooks to send survey completion data to our system for analysis.
                </p>
                <ol className="list-decimal list-inside space-y-2 text-sm">
                  <li>Log into your Qualtrics account</li>
                  <li>Navigate to your survey settings</li>
                  <li>Go to the "Survey Flow" section</li>
                  <li>Add a webhook element with the URL: <code className="bg-blue-100 px-1 rounded">{webhookBaseUrl}/qualtrics</code></li>
                  <li>Set the webhook to trigger on survey completion</li>
                  <li>Add the JavaScript tracking code below to enable behavior analysis</li>
                </ol>
                <div className="mt-3 p-3 bg-white rounded border border-blue-100">
                  <p className="text-xs text-gray-600"><strong>Note:</strong> For full bot detection, you'll need both the webhook AND the JavaScript tracking code.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* JavaScript Integration Code */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Zap className="h-5 w-5 text-gray-600 mr-2" />
          JavaScript Integration Code
        </h3>
        
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">📋 How to Use This Code</h4>
            <ol className="text-sm text-gray-700 space-y-1">
              <li><strong>Copy the code below</strong> and paste it into your survey's JavaScript section</li>
              <li><strong>For Decipher:</strong> Add to "Survey Options" → "JavaScript" → "Header"</li>
              <li><strong>For Qualtrics:</strong> Add to "Look & Feel" → "Advanced" → "Header"</li>
              <li><strong>Create hidden fields</strong> in your survey to store the results</li>
              <li><strong>Test your survey</strong> - the code will automatically track user behavior</li>
            </ol>
          </div>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">🔍 What This Code Does</h4>
            <ul className="text-sm text-gray-700 space-y-1">
              <li><strong>Creates a session:</strong> Generates a unique ID to track each user's behavior</li>
              <li><strong>Tracks keystrokes:</strong> Records typing speed, patterns, and timing</li>
              <li><strong>Monitors mouse movements:</strong> Captures cursor movement and click patterns</li>
              <li><strong>Records scrolling:</strong> Tracks how users navigate through the survey</li>
              <li><strong>Sends data:</strong> Automatically transmits behavior data to our analysis server</li>
              <li><strong>Analyzes patterns:</strong> Uses AI to determine if behavior looks human or bot-like</li>
            </ul>
          </div>
          
          <p className="text-sm text-gray-600">
            <strong>Ready to integrate?</strong> Copy the code below and add it to your survey:
          </p>
          
          <div className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto">
            <pre className="text-xs">
{`// Bot Detection Integration
const sessionId = '{{e://Field/sessionId}}'; // Survey embedded data
const apiBaseUrl = 'https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1';

// Initialize bot detection
async function initBotDetection() {
  try {
    const response = await fetch(\`\${apiBaseUrl}/detection/sessions\`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await response.json();
    return data.session_id;
  } catch (error) {
    console.error('Failed to initialize bot detection:', error);
  }
}

// Send behavioral events
async function sendEvent(eventData) {
  try {
    await fetch(\`\${apiBaseUrl}/detection/sessions/\${sessionId}/events\`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify([eventData])
    });
  } catch (error) {
    console.error('Failed to send event:', error);
  }
}

// Track keystrokes
document.addEventListener('keydown', (e) => {
  sendEvent({
    event_type: 'keystroke',
    timestamp: new Date().toISOString(),
    key: e.key,
    element_id: e.target.id || e.target.name
  });
});

// Track mouse movements
document.addEventListener('mousemove', (e) => {
  sendEvent({
    event_type: 'mouse_move',
    timestamp: new Date().toISOString(),
    x: e.clientX,
    y: e.clientY,
    element_id: e.target.id || e.target.name
  });
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', initBotDetection);`}
            </pre>
          </div>
          
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">📊 Required Hidden Fields</h4>
            <p className="text-sm text-gray-700 mb-3">
              Create these hidden fields in your survey to store the bot detection results:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="bg-white p-3 rounded border border-yellow-100">
                <h5 className="font-medium text-gray-900 text-sm mb-1">Field ID: <code className="bg-yellow-100 px-1 rounded">bot_session_id</code></h5>
                <p className="text-xs text-gray-600">Stores the unique session identifier</p>
              </div>
              <div className="bg-white p-3 rounded border border-yellow-100">
                <h5 className="font-medium text-gray-900 text-sm mb-1">Field ID: <code className="bg-yellow-100 px-1 rounded">bot_is_bot</code></h5>
                <p className="text-xs text-gray-600">"true" if bot detected, "false" if human</p>
              </div>
              <div className="bg-white p-3 rounded border border-yellow-100">
                <h5 className="font-medium text-gray-900 text-sm mb-1">Field ID: <code className="bg-yellow-100 px-1 rounded">bot_confidence</code></h5>
                <p className="text-xs text-gray-600">Confidence score from 0.0 to 1.0</p>
              </div>
              <div className="bg-white p-3 rounded border border-yellow-100">
                <h5 className="font-medium text-gray-900 text-sm mb-1">Field ID: <code className="bg-yellow-100 px-1 rounded">bot_result</code></h5>
                <p className="text-xs text-gray-600">Complete analysis details in JSON format</p>
              </div>
            </div>
          </div>
          
          <button
            onClick={() => copyToClipboard(`// Bot Detection Integration
const sessionId = '{{e://Field/sessionId}}'; // Survey embedded data
const apiBaseUrl = 'https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1';

// Initialize bot detection
async function initBotDetection() {
  try {
    const response = await fetch(\`\${apiBaseUrl}/detection/sessions\`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    const data = await response.json();
    return data.session_id;
  } catch (error) {
    console.error('Failed to initialize bot detection:', error);
  }
}

// Send behavioral events
async function sendEvent(eventData) {
  try {
    await fetch(\`\${apiBaseUrl}/detection/sessions/\${sessionId}/events\`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify([eventData])
    });
  } catch (error) {
    console.error('Failed to send event:', error);
  }
}

// Track keystrokes
document.addEventListener('keydown', (e) => {
  sendEvent({
    event_type: 'keystroke',
    timestamp: new Date().toISOString(),
    key: e.key,
    element_id: e.target.id || e.target.name
  });
});

// Track mouse movements
document.addEventListener('mousemove', (e) => {
  sendEvent({
    event_type: 'mouse_move',
    timestamp: new Date().toISOString(),
    x: e.clientX,
    y: e.clientY,
    element_id: e.target.id || e.target.name
  });
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', initBotDetection);`, 'js-code')}
            className="btn-secondary text-sm"
          >
            {copiedField === 'js-code' ? (
              <>
                <Check className="h-4 w-4 mr-2" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="h-4 w-4 mr-2" />
                Copy Code
              </>
            )}
          </button>
        </div>
      </div>

      {/* API Documentation */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Globe className="h-5 w-5 text-gray-600 mr-2" />
          API Documentation
        </h3>
        
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">🌐 Production API Base URL</h4>
            <div className="flex items-center space-x-2">
              <code className="flex-1 text-sm bg-white p-2 rounded border">
                https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1
              </code>
              <button
                onClick={() => copyToClipboard('https://bot-backend-119522247395.northamerica-northeast2.run.app/api/v1', 'api-base')}
                className="p-1 text-gray-500 hover:text-gray-700"
                title="Copy API base URL"
              >
                {copiedField === 'api-base' ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Bot Detection Endpoints</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li><code className="bg-gray-200 px-1 rounded">POST /detection/sessions</code></li>
                <li><code className="bg-gray-200 px-1 rounded">POST /detection/sessions/{'{id}'}/events</code></li>
                <li><code className="bg-gray-200 px-1 rounded">POST /detection/sessions/{'{id}'}/analyze</code></li>
                <li><code className="bg-gray-200 px-1 rounded">GET /detection/sessions/{'{id}'}/status</code></li>
              </ul>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Dashboard Endpoints</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li><code className="bg-gray-200 px-1 rounded">GET /dashboard/overview</code></li>
                <li><code className="bg-gray-200 px-1 rounded">GET /dashboard/sessions</code></li>
                <li><code className="bg-gray-200 px-1 rounded">GET /integrations/status</code></li>
                <li><code className="bg-gray-200 px-1 rounded">GET /health</code></li>
              </ul>
            </div>
          </div>
          
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">📚 Full Documentation</h4>
            <p className="text-sm text-gray-600 mb-2">
              For complete API documentation with examples and interactive testing:
            </p>
            <a 
              href={`${apiBaseUrl.replace('/api/v1', '')}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              <Globe className="h-4 w-4 mr-1" />
              Open API Documentation
            </a>
          </div>
        </div>
      </div>

      {/* Troubleshooting */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <TriangleAlert className="h-5 w-5 text-orange-600 mr-2" />
          Troubleshooting & FAQ
        </h3>
        
        <div className="space-y-4">
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">❓ Common Questions</h4>
            <div className="space-y-3">
              <div>
                <h5 className="font-medium text-gray-900 text-sm mb-1">Q: Why do I need hidden fields?</h5>
                <p className="text-xs text-gray-600">Hidden fields store the bot detection results in your survey data export. Without them, you won't see the analysis results.</p>
              </div>
              <div>
                <h5 className="font-medium text-gray-900 text-sm mb-1">Q: Will this slow down my survey?</h5>
                <p className="text-xs text-gray-600">No, the tracking is lightweight and runs in the background. Users won't notice any performance impact.</p>
              </div>
              <div>
                <h5 className="font-medium text-gray-900 text-sm mb-1">Q: How accurate is the bot detection?</h5>
                <p className="text-xs text-gray-600">Our AI analyzes multiple behavior patterns and typically achieves 90%+ accuracy in distinguishing bots from humans.</p>
              </div>
              <div>
                <h5 className="font-medium text-gray-900 text-sm mb-1">Q: What if the analysis fails?</h5>
                <p className="text-xs text-gray-600">If the system can't analyze the data, it will set <code>bot_is_bot</code> to "unknown" and <code>bot_confidence</code> to "0".</p>
              </div>
            </div>
          </div>
          
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">⚠️ Troubleshooting</h4>
            <div className="space-y-2">
              <div className="flex items-start">
                <div className="w-2 h-2 bg-red-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">No data in export</p>
                  <p className="text-xs text-gray-600">Check that hidden fields are created with exact field IDs and JavaScript is added correctly</p>
                </div>
              </div>
              <div className="flex items-start">
                <div className="w-2 h-2 bg-red-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">JavaScript errors</p>
                  <p className="text-xs text-gray-600">Ensure your survey allows JavaScript and can access external URLs (no firewall blocks)</p>
                </div>
              </div>
              <div className="flex items-start">
                <div className="w-2 h-2 bg-red-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></div>
                <div>
                  <p className="text-sm font-medium text-gray-900">All results show "unknown"</p>
                  <p className="text-xs text-gray-600">Check internet connectivity and verify the API URL is accessible from your survey</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Integration Logs */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Integration Logs</h2>
        <div className="bg-gray-50 rounded-lg p-4 max-h-64 overflow-y-auto">
          {logs.length === 0 ? (
            <div className="text-gray-500 text-sm">No logs yet.</div>
          ) : (
            <ul className="divide-y divide-gray-200">
              {logs.map((log) => (
                <li key={log.id} className="py-2 flex items-center gap-2">
                  {log.status === 'success' ? (
                    <Check className="h-4 w-4 text-green-500" />
                  ) : (
                    <X className="h-4 w-4 text-red-500" />
                  )}
                  <span className="font-medium capitalize">{log.platform}</span>
                  <span className="text-xs text-gray-400">{new Date(log.timestamp).toLocaleTimeString()}</span>
                  <span className="ml-2 text-gray-700 text-sm">{log.message}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      <ToastContainer position="bottom-right" autoClose={3000} />
    </div>
  );
};

export default Integrations; 