import React, { useState, useEffect } from 'react';
import { 
  Settings as SettingsIcon,
  Save,
  Eye,
  EyeOff,
  TestTube,
  Shield,
  Database,
  Globe,
  Zap,
  AlertTriangle,
  CheckCircle,
  RefreshCw
} from 'lucide-react';

const Settings = () => {
  const [settings, setSettings] = useState({
    // Integration Settings
    qualtrics: {
      api_token: '',
      webhook_url: 'http://localhost:8000/api/v1/integrations/webhooks/qualtrics',
      enabled: false
    },
    decipher: {
      api_key: '',
      webhook_url: 'http://localhost:8000/api/v1/integrations/webhooks/decipher',
      enabled: false
    },
    
    // Detection Settings
    detection: {
      min_events_for_analysis: 50,
      confidence_threshold: 0.7,
      risk_levels: {
        low: 0.7,
        medium: 0.3,
        high: 0.0
      },
      enabled_methods: {
        keystroke_analysis: true,
        mouse_analysis: true,
        timing_analysis: true,
        device_analysis: true,
        network_analysis: true
      }
    },
    
    // System Settings
    system: {
      session_timeout_minutes: 30,
      max_events_per_session: 1000,
      data_retention_days: 90,
      auto_cleanup_enabled: true,
      debug_mode: false
    },
    
    // Notification Settings
    notifications: {
      email_notifications: false,
      webhook_notifications: false,
      bot_detection_alerts: true,
      system_health_alerts: true,
      daily_reports: false
    }
  });

  const [showPasswords, setShowPasswords] = useState({
    qualtrics: false,
    decipher: false
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testResults, setTestResults] = useState({});

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      // This would fetch settings from the backend
      // For now, using default settings
      console.log('Loading settings...');
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);
      // This would save settings to the backend
      console.log('Saving settings:', settings);
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      console.log('Settings saved successfully');
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setSaving(false);
    }
  };

  const testIntegration = async (platform) => {
    try {
      setTestResults(prev => ({ ...prev, [platform]: 'testing' }));
      
      // Simulate API test
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const success = Math.random() > 0.3; // 70% success rate for demo
      setTestResults(prev => ({ 
        ...prev, 
        [platform]: success ? 'success' : 'error' 
      }));
    } catch (error) {
      setTestResults(prev => ({ ...prev, [platform]: 'error' }));
    }
  };

  const updateSetting = (section, key, value) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
  };

  const updateNestedSetting = (section, key, subKey, value) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: {
          ...prev[section][key],
          [subKey]: value
        }
      }
    }));
  };

  const getTestResultIcon = (result) => {
    switch (result) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'testing':
        return <RefreshCw className="h-4 w-4 animate-spin text-blue-500" />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">Configure system settings and integrations</p>
      </div>

      {/* Integration Settings */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <Globe className="h-5 w-5 text-blue-600 mr-2" />
          Integration Settings
        </h2>
        
        <div className="space-y-6">
          {/* Qualtrics Settings */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Qualtrics</h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => testIntegration('qualtrics')}
                  className="btn-secondary text-sm flex items-center"
                  disabled={testResults.qualtrics === 'testing'}
                >
                  <TestTube className="h-4 w-4 mr-1" />
                  Test Connection
                </button>
                {getTestResultIcon(testResults.qualtrics)}
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Token
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.qualtrics ? 'text' : 'password'}
                    value={settings.qualtrics.api_token}
                    onChange={(e) => updateSetting('qualtrics', 'api_token', e.target.value)}
                    className="w-full pr-10 border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter Qualtrics API token"
                  />
                  <button
                    onClick={() => setShowPasswords(prev => ({ ...prev, qualtrics: !prev.qualtrics }))}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPasswords.qualtrics ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Webhook URL
                </label>
                <input
                  type="text"
                  value={settings.qualtrics.webhook_url}
                  onChange={(e) => updateSetting('qualtrics', 'webhook_url', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            
            <div className="mt-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.qualtrics.enabled}
                  onChange={(e) => updateSetting('qualtrics', 'enabled', e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">Enable Qualtrics integration</span>
              </label>
            </div>
          </div>

          {/* Decipher Settings */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Decipher</h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => testIntegration('decipher')}
                  className="btn-secondary text-sm flex items-center"
                  disabled={testResults.decipher === 'testing'}
                >
                  <TestTube className="h-4 w-4 mr-1" />
                  Test Connection
                </button>
                {getTestResultIcon(testResults.decipher)}
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Key
                </label>
                <div className="relative">
                  <input
                    type={showPasswords.decipher ? 'text' : 'password'}
                    value={settings.decipher.api_key}
                    onChange={(e) => updateSetting('decipher', 'api_key', e.target.value)}
                    className="w-full pr-10 border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter Decipher API key"
                  />
                  <button
                    onClick={() => setShowPasswords(prev => ({ ...prev, decipher: !prev.decipher }))}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPasswords.decipher ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Webhook URL
                </label>
                <input
                  type="text"
                  value={settings.decipher.webhook_url}
                  onChange={(e) => updateSetting('decipher', 'webhook_url', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            
            <div className="mt-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.decipher.enabled}
                  onChange={(e) => updateSetting('decipher', 'enabled', e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">Enable Decipher integration</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Detection Settings */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <Shield className="h-5 w-5 text-green-600 mr-2" />
          Detection Settings
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Minimum Events for Analysis
            </label>
            <input
              type="number"
              value={settings.detection.min_events_for_analysis}
              onChange={(e) => updateSetting('detection', 'min_events_for_analysis', parseInt(e.target.value))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
              min="10"
              max="500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Confidence Threshold
            </label>
            <input
              type="number"
              step="0.1"
              value={settings.detection.confidence_threshold}
              onChange={(e) => updateSetting('detection', 'confidence_threshold', parseFloat(e.target.value))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
              min="0"
              max="1"
            />
          </div>
        </div>

        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Risk Level Thresholds</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(settings.detection.risk_levels).map(([level, threshold]) => (
              <div key={level}>
                <label className="block text-sm font-medium text-gray-700 mb-1 capitalize">
                  {level} Risk
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={threshold}
                  onChange={(e) => updateNestedSetting('detection', 'risk_levels', level, parseFloat(e.target.value))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
                  min="0"
                  max="1"
                />
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Detection Methods</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(settings.detection.enabled_methods).map(([method, enabled]) => (
              <label key={method} className="flex items-center">
                <input
                  type="checkbox"
                  checked={enabled}
                  onChange={(e) => updateNestedSetting('detection', 'enabled_methods', method, e.target.checked)}
                  className="rounded border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700 capitalize">
                  {method.replace('_', ' ')} Analysis
                </span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* System Settings */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <Database className="h-5 w-5 text-purple-600 mr-2" />
          System Settings
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Session Timeout (minutes)
            </label>
            <input
              type="number"
              value={settings.system.session_timeout_minutes}
              onChange={(e) => updateSetting('system', 'session_timeout_minutes', parseInt(e.target.value))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
              min="5"
              max="1440"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Max Events per Session
            </label>
            <input
              type="number"
              value={settings.system.max_events_per_session}
              onChange={(e) => updateSetting('system', 'max_events_per_session', parseInt(e.target.value))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
              min="100"
              max="10000"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data Retention (days)
            </label>
            <input
              type="number"
              value={settings.system.data_retention_days}
              onChange={(e) => updateSetting('system', 'data_retention_days', parseInt(e.target.value))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500"
              min="1"
              max="365"
            />
          </div>
        </div>

        <div className="mt-6 space-y-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.system.auto_cleanup_enabled}
              onChange={(e) => updateSetting('system', 'auto_cleanup_enabled', e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="ml-2 text-sm text-gray-700">Enable automatic data cleanup</span>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.system.debug_mode}
              onChange={(e) => updateSetting('system', 'debug_mode', e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="ml-2 text-sm text-gray-700">Enable debug mode</span>
          </label>
        </div>
      </div>

      {/* Notification Settings */}
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <Zap className="h-5 w-5 text-yellow-600 mr-2" />
          Notification Settings
        </h2>
        
        <div className="space-y-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.notifications.email_notifications}
              onChange={(e) => updateSetting('notifications', 'email_notifications', e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="ml-2 text-sm text-gray-700">Email notifications</span>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.notifications.webhook_notifications}
              onChange={(e) => updateSetting('notifications', 'webhook_notifications', e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="ml-2 text-sm text-gray-700">Webhook notifications</span>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.notifications.bot_detection_alerts}
              onChange={(e) => updateSetting('notifications', 'bot_detection_alerts', e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="ml-2 text-sm text-gray-700">Bot detection alerts</span>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.notifications.system_health_alerts}
              onChange={(e) => updateSetting('notifications', 'system_health_alerts', e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="ml-2 text-sm text-gray-700">System health alerts</span>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.notifications.daily_reports}
              onChange={(e) => updateSetting('notifications', 'daily_reports', e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="ml-2 text-sm text-gray-700">Daily summary reports</span>
          </label>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={saveSettings}
          disabled={saving}
          className="btn-primary flex items-center"
        >
          {saving ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin mr-2" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save Settings
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default Settings; 