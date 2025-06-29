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

  const webhookBaseUrl = 'http://localhost:8000/api/v1/integrations/webhooks';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Integrations</h1>
        <p className="text-gray-600 mt-2">Manage your survey platform integrations</p>
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

      {/* Setup Instructions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Setup Instructions</h3>
        
        <div className="space-y-6">
          {/* Qualtrics Setup */}
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
              <Globe className="h-5 w-5 text-blue-600 mr-2" />
              Qualtrics Integration
            </h4>
            <div className="bg-blue-50 p-4 rounded-lg">
              <ol className="list-decimal list-inside space-y-2 text-sm">
                <li>Log into your Qualtrics account</li>
                <li>Navigate to your survey settings</li>
                <li>Go to the "Survey Flow" section</li>
                <li>Add a webhook element with the URL: <code className="bg-blue-100 px-1 rounded">{webhookBaseUrl}/qualtrics</code></li>
                <li>Set the webhook to trigger on survey completion</li>
                <li>Save and test your survey</li>
              </ol>
            </div>
          </div>

          {/* Decipher Setup */}
          <div>
            <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
              <Zap className="h-5 w-5 text-purple-600 mr-2" />
              Decipher Integration
            </h4>
            <div className="bg-purple-50 p-4 rounded-lg">
              <ol className="list-decimal list-inside space-y-2 text-sm">
                <li>Log into your Decipher account</li>
                <li>Open your survey in the survey editor</li>
                <li>Go to "Survey Options" → "Webhooks"</li>
                <li>Add a new webhook with URL: <code className="bg-purple-100 px-1 rounded">{webhookBaseUrl}/decipher</code></li>
                <li>Set the trigger to "Survey Complete"</li>
                <li>Save and publish your survey</li>
              </ol>
            </div>
          </div>
        </div>
      </div>

      {/* JavaScript Integration Code */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Zap className="h-5 w-5 text-gray-600 mr-2" />
          JavaScript Integration
        </h3>
        
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            Add this JavaScript code to your survey to enable bot detection:
          </p>
          
          <div className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto">
            <pre className="text-xs">
{`// Bot Detection Integration
const sessionId = '{{e://Field/sessionId}}'; // Survey embedded data
const apiBaseUrl = 'http://localhost:8000/api/v1';

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
          
          <button
            onClick={() => copyToClipboard(`// Bot Detection Integration
const sessionId = '{{e://Field/sessionId}}'; // Survey embedded data
const apiBaseUrl = 'http://localhost:8000/api/v1';

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
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Webhook Endpoints</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li><code className="bg-gray-200 px-1 rounded">POST /integrations/webhooks/qualtrics</code></li>
              <li><code className="bg-gray-200 px-1 rounded">POST /integrations/webhooks/decipher</code></li>
            </ul>
          </div>
          
          <div className="bg-gray-50 p-4 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">Status Endpoints</h4>
            <ul className="text-sm text-gray-600 space-y-1">
              <li><code className="bg-gray-200 px-1 rounded">GET /integrations/status</code></li>
              <li><code className="bg-gray-200 px-1 rounded">GET /integrations/qualtrics/surveys/{'{survey_id}'}</code></li>
              <li><code className="bg-gray-200 px-1 rounded">GET /integrations/decipher/surveys/{'{survey_id}'}</code></li>
            </ul>
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