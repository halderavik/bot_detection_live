import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { config } from '../config/config';

// Move CodeBlock definition to the top
const CodeBlock = ({ code, language, onCopy, isCopied }) => (
  <div className="relative">
    <div className="absolute top-2 right-2">
      <button
        onClick={onCopy}
        className={`text-xs px-2 py-1 rounded transition-colors ${
          isCopied 
            ? 'bg-green-100 text-green-700' 
            : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
        }`}
      >
        {isCopied ? 'Copied!' : 'Copy'}
      </button>
    </div>
    <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
      <code>{code}</code>
    </pre>
  </div>
);

const QuickStartGuide = () => {
  const [activeStep, setActiveStep] = useState(1);
  const [copiedCode, setCopiedCode] = useState('');

  const steps = [
    {
      id: 1,
      title: 'Setup & Installation',
      description: 'Get your bot detection system up and running',
      content: (
        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h4 className="font-semibold text-green-800 mb-2">✅ Prerequisites</h4>
            <ul className="text-sm text-green-700 space-y-1">
              <li>• Node.js 16+ and npm</li>
              <li>• Python 3.8+ and pip</li>
              <li>• PostgreSQL database</li>
              <li>• Git</li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-gray-800 mb-2">1. Clone the Repository</h4>
            <CodeBlock
              code={`git clone https://github.com/your-org/bot-detection-system.git\ncd bot-detection-system`}
              language="bash"
              onCopy={() => setCopiedCode('clone')}
              isCopied={copiedCode === 'clone'}
            />
          </div>

          <div>
            <h4 className="font-semibold text-gray-800 mb-2">2. Start the Backend</h4>
            <CodeBlock
              code={`cd backend\npython -m venv venv\nvenv\\Scripts\\activate  # Windows\npip install -r requirements.txt\npython main.py`}
              language="bash"
              onCopy={() => setCopiedCode('backend')}
              isCopied={copiedCode === 'backend'}
            />
          </div>

          <div>
            <h4 className="font-semibold text-gray-800 mb-2">3. Start the Frontend</h4>
            <CodeBlock
              code={`cd frontend\nnpm install\nnpm run dev`}
              language="bash"
              onCopy={() => setCopiedCode('frontend')}
              isCopied={copiedCode === 'frontend'}
            />
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-blue-800 mb-2">🎯 What's Next?</h4>
            <p className="text-sm text-blue-700">
              Your system should now be running at:
            </p>
            <ul className="text-sm text-blue-700 mt-2 space-y-1">
              <li>• Frontend: <code className="bg-blue-100 px-1 rounded">{config.frontendBaseUrl}</code></li>
              <li>• Backend API: <code className="bg-blue-100 px-1 rounded">{config.apiBaseUrl}</code></li>
              <li>• API Docs: <code className="bg-blue-100 px-1 rounded">{config.apiDocsUrl}</code></li>
            </ul>
          </div>
        </div>
      )
    },
    {
      id: 2,
      title: 'JavaScript Integration',
      description: 'Add bot detection to your web application',
      content: (
        <div className="space-y-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h4 className="font-semibold text-yellow-800 mb-2">📋 Overview</h4>
            <p className="text-sm text-yellow-700">
              The JavaScript client automatically collects user behavior data and sends it to the bot detection API.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-gray-800 mb-2">1. Include the Tracking Script</h4>
            <CodeBlock
              code={`<script src="${config.trackingClientUrl}"></script>\n<script>\n  // Initialize bot detection\n  BotDetection.init({\n    apiUrl: '${config.apiBaseUrl}',\n    sessionId: 'your-session-id', // Optional: auto-generated if not provided\n    autoStart: true\n  });\n</script>`}
              language="html"
              onCopy={() => setCopiedCode('js-init')}
              isCopied={copiedCode === 'js-init'}
            />
          </div>

          <div>
            <h4 className="font-semibold text-gray-800 mb-2">2. Manual Event Tracking (Optional)</h4>
            <CodeBlock
              code={`// Track custom events\nBotDetection.trackEvent('form_submit', {\n  formId: 'login-form',\n  fieldCount: 3\n});\n\n// Track page views\nBotDetection.trackPageView('/dashboard');\n\n// Get session status\nconst status = await BotDetection.getSessionStatus();\nconsole.log('Session status:', status);`}
              language="javascript"
              onCopy={() => setCopiedCode('js-events')}
              isCopied={copiedCode === 'js-events'}
            />
          </div>

          <div>
            <h4 className="font-semibold text-gray-800 mb-2">3. React/Next.js Integration</h4>
            <CodeBlock
              code={`import { useEffect } from 'react';\n\nfunction MyComponent() {\n  useEffect(() => {\n    // Initialize bot detection when component mounts\n    if (window.BotDetection) {\n      window.BotDetection.init({\n        apiUrl: process.env.REACT_APP_API_URL,\n        sessionId: 'react-session-' + Date.now()\n      });\n    }\n  }, []);\n\n  return <div>Your component content</div>;\n}`}
              language="javascript"
              onCopy={() => setCopiedCode('js-react')}
              isCopied={copiedCode === 'js-react'}
            />
          </div>
        </div>
      )
    },
    {
      id: 3,
      title: 'Python Integration',
      description: 'Integrate bot detection into your Python applications',
      content: (
        <div className="space-y-4">
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h4 className="font-semibold text-purple-800 mb-2">🐍 Python SDK</h4>
            <p className="text-sm text-purple-700">
              Use the Python client SDK for server-side applications, automation tools, and data analysis.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-gray-800 mb-2">1. Install the SDK</h4>
            <CodeBlock
              code={`pip install bot-detection-client\n# or from local development\npip install -e client-sdk/python/`}
              language="bash"
              onCopy={() => setCopiedCode('py-install')}
              isCopied={copiedCode === 'py-install'}
            />
          </div>

          <div>
            <h4 className="font-semibold text-gray-800 mb-2">2. Basic Usage</h4>
            <CodeBlock
              code={`from bot_detection_client import BotDetectionClient\n\n# Initialize client\nclient = BotDetectionClient(\n    api_url="${config.apiBaseUrl}",\n    api_key="your-api-key"  # Optional for development\n)\n\n# Create a session\nsession = await client.create_session()\nprint(f"Session ID: {session['id']}")\n\n# Send events\nevents = [\n    {\n        "type": "keystroke",\n        "timestamp": "2024-01-15T10:30:00Z",\n        "data": {\n            "key": "a",\n            "keyCode": 65,\n            "timeSinceLastKey": 150\n        }\n    }\n]\n\nawait client.ingest_events(session['id'], events)\n\n# Analyze session\nresult = await client.analyze_session(session['id'])\nprint(f"Bot detected: {result['is_bot']}")\nprint(f"Confidence: {result['confidence_score']}")`}
              language="python"
              onCopy={() => setCopiedCode('py-basic')}
              isCopied={copiedCode === 'py-basic'}
            />
          </div>

          <div>
            <h4 className="font-semibold text-gray-800 mb-2">3. Flask/FastAPI Integration</h4>
            <CodeBlock
              code={`from flask import Flask, request\nfrom bot_detection_client import BotDetectionClient\n\napp = Flask(__name__)\nclient = BotDetectionClient(api_url="${config.apiBaseUrl}")\n\n@app.route('/submit-form', methods=['POST'])\nasync def submit_form():\n    # Create session for form submission\n    session = await client.create_session()\n    \n    # Get events from request\n    events = request.json.get('events', [])\n    \n    # Send events to bot detection\n    await client.ingest_events(session['id'], events)\n    \n    # Analyze for bot activity\n    result = await client.analyze_session(session['id'])\n    \n    if result['is_bot']:\n        return {"error": "Bot activity detected"}, 403\n    \n    # Process legitimate form submission\n    return {"success": True, "session_id": session['id']}`}
              language="python"
              onCopy={() => setCopiedCode('py-flask')}
              isCopied={copiedCode === 'py-flask'}
            />
          </div>
        </div>
      )
    },
    {
      id: 4,
      title: 'Survey Platform Integration',
      description: 'Integrate with Qualtrics and Decipher survey platforms',
      content: (
        <div className="space-y-4">
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
            <h4 className="font-semibold text-indigo-800 mb-2">📊 Survey Integration</h4>
            <p className="text-sm text-indigo-700">
              Automatically detect bots in your survey responses using webhook integrations.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-gray-800 mb-2">1. Qualtrics Integration</h4>
            <CodeBlock
              code={`# Configure webhook URL in Qualtrics\nWebhook URL: ${config.webhooks.qualtrics}\nMethod: POST\n\n# Add to survey flow\nSurvey Flow > Add a Web Service > \n- URL: {{webhook_url}}\n- Method: POST\n- Body: {{ResponseID}}, {{SurveyID}}, {{ResponseData}}`}
              language="text"
              onCopy={() => setCopiedCode('qualtrics')}
              isCopied={copiedCode === 'qualtrics'}
            />
          </div>

          <div>
            <h4 className="font-semibold text-gray-800 mb-2">2. Decipher Integration</h4>
            <CodeBlock
              code={`# Configure webhook in Decipher\nWebhook URL: ${config.webhooks.decipher}\nAuthentication: Bearer token (optional)\n\n# Add to survey logic\nsurvey.onComplete = function() {\n    fetch('{{webhook_url}}', {\n        method: 'POST',\n        headers: {\n            'Content-Type': 'application/json',\n            'Authorization': 'Bearer {{your_token}}'\n        },\n        body: JSON.stringify({\n            surveyId: survey.id,\n            responseId: survey.responseId,\n            data: survey.data\n        })\n    });\n};`}
              language="javascript"
              onCopy={() => setCopiedCode('decipher')}
              isCopied={copiedCode === 'decipher'}
            />
          </div>

          <div>
            <h4 className="font-semibold text-gray-800 mb-2">3. Test Integration</h4>
            <CodeBlock
              code={`# Test webhook endpoint\ncurl -X POST ${config.webhooks.qualtrics} \\\n  -H "Content-Type: application/json" \\\n  -d '{\n    "surveyId": "SV_123456",\n    "responseId": "R_789012",\n    "events": [\n      {\n        "type": "keystroke",\n        "timestamp": "2024-01-15T10:30:00Z",\n        "data": {"key": "a", "keyCode": 65}\n      }\n    ]\n  }'`}
              language="bash"
              onCopy={() => setCopiedCode('test-webhook')}
              isCopied={copiedCode === 'test-webhook'}
            />
          </div>
        </div>
      )
    },
    {
      id: 5,
      title: 'Dashboard & Monitoring',
      description: 'Monitor and analyze bot detection results',
      content: (
        <div className="space-y-4">
          <div className="bg-teal-50 border border-teal-200 rounded-lg p-4">
            <h4 className="font-semibold text-teal-800 mb-2">📈 Dashboard Features</h4>
            <p className="text-sm text-teal-700">
              Use the web dashboard to monitor sessions, view analytics, and manage integrations.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">Dashboard Overview</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Real-time session monitoring</li>
                <li>• Bot detection statistics</li>
                <li>• Performance metrics</li>
                <li>• Integration status</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-800 mb-2">Session Management</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• View session details</li>
                <li>• Analyze event patterns</li>
                <li>• Export session data</li>
                <li>• Compare sessions</li>
              </ul>
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-gray-800 mb-2">API Endpoints for Monitoring</h4>
            <CodeBlock
              code={`# Get dashboard overview\nGET /api/v1/dashboard/overview?days=7\n\n# Get sessions list\nGET /api/v1/dashboard/sessions?page=1&limit=50\n\n# Get session details\nGET /api/v1/dashboard/sessions/{sessionId}/details\n\n# Get analytics trends\nGET /api/v1/dashboard/analytics/trends?days=30&interval=day\n\n# Check system health\nGET /api/v1/health`}
              language="bash"
              onCopy={() => setCopiedCode('monitoring')}
              isCopied={copiedCode === 'monitoring'}
            />
          </div>

          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <h4 className="font-semibold text-orange-800 mb-2">🔧 Configuration</h4>
            <p className="text-sm text-orange-700 mb-2">
              Customize your bot detection settings:
            </p>
            <ul className="text-sm text-orange-700 space-y-1">
              <li>• Adjust detection thresholds</li>
              <li>• Configure integration settings</li>
              <li>• Set up webhook URLs</li>
              <li>• Manage API keys</li>
            </ul>
          </div>
        </div>
      )
    }
  ];

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Quick Start Guide</h1>
        <p className="text-gray-600 mb-6">
          Get up and running with the Bot Detection System in minutes. Follow these steps to integrate bot detection into your applications.
        </p>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <button
                  onClick={() => setActiveStep(step.id)}
                  className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors ${
                    activeStep === step.id
                      ? 'border-blue-500 bg-blue-500 text-white'
                      : activeStep > step.id
                      ? 'border-green-500 bg-green-500 text-white'
                      : 'border-gray-300 bg-white text-gray-500'
                  }`}
                >
                  {activeStep > step.id ? (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    step.id
                  )}
                </button>
                {index < steps.length - 1 && (
                  <div className={`flex-1 h-0.5 mx-4 ${
                    activeStep > step.id ? 'bg-green-500' : 'bg-gray-300'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="mb-6">
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {steps.find(s => s.id === activeStep)?.title}
            </h2>
            <p className="text-gray-600">
              {steps.find(s => s.id === activeStep)?.description}
            </p>
          </div>
          {steps.find(s => s.id === activeStep)?.content}
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={() => setActiveStep(Math.max(1, activeStep - 1))}
            disabled={activeStep === 1}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <button
            onClick={() => setActiveStep(Math.min(steps.length, activeStep + 1))}
            disabled={activeStep === steps.length}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {activeStep === steps.length ? 'Finish' : 'Next'}
          </button>
        </div>

        {/* Additional Resources */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold text-gray-900 mb-3">Additional Resources</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <a
              href="/api-playground"
              className="p-3 bg-white rounded-lg border hover:border-blue-300 transition-colors"
            >
              <h4 className="font-medium text-gray-900">API Playground</h4>
              <p className="text-sm text-gray-600">Test API endpoints interactively</p>
            </a>
            <a
              href={config.apiDocsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="p-3 bg-white rounded-lg border hover:border-blue-300 transition-colors"
            >
              <h4 className="font-medium text-gray-900">API Documentation</h4>
              <p className="text-sm text-gray-600">Complete API reference</p>
            </a>
            <a
              href="/integrations"
              className="p-3 bg-white rounded-lg border hover:border-blue-300 transition-colors"
            >
              <h4 className="font-medium text-gray-900">Integrations</h4>
              <p className="text-sm text-gray-600">Configure survey platforms</p>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuickStartGuide; 