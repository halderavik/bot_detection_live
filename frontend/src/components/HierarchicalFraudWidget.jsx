import React, { useState, useEffect } from 'react';
import { hierarchicalService } from '../services/apiService';
import { AlertTriangle, Shield, Activity, TrendingUp, AlertCircle } from 'lucide-react';

/**
 * HierarchicalFraudWidget Component
 * 
 * Displays fraud detection summary at different hierarchy levels:
 * - Survey level
 * - Platform level
 * - Respondent level
 * - Session level
 */
const HierarchicalFraudWidget = ({ 
  surveyId, 
  platformId = null, 
  respondentId = null, 
  sessionId = null,
  filters = {}
}) => {
  const [fraudData, setFraudData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadFraudData();
  }, [surveyId, platformId, respondentId, sessionId, filters]);

  const loadFraudData = async () => {
    if (!surveyId) return;

    try {
      setLoading(true);
      setError(null);

      let data;
      if (sessionId && respondentId && platformId) {
        // Session level
        data = await hierarchicalService.getSessionFraudByHierarchy(
          surveyId, 
          platformId, 
          respondentId, 
          sessionId
        );
      } else if (respondentId && platformId) {
        // Respondent level
        data = await hierarchicalService.getRespondentFraudSummary(
          surveyId, 
          platformId, 
          respondentId, 
          filters
        );
      } else if (platformId) {
        // Platform level
        data = await hierarchicalService.getPlatformFraudSummary(
          surveyId, 
          platformId, 
          filters
        );
      } else {
        // Survey level
        data = await hierarchicalService.getSurveyFraudSummary(surveyId, filters);
      }

      setFraudData(data);
    } catch (err) {
      console.error('Error loading fraud data:', err);
      setError('Failed to load fraud detection data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-600" />
          Fraud Detection Summary
        </h3>
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-600" />
          Fraud Detection Summary
        </h3>
        <div className="text-red-600 bg-red-50 border border-red-200 rounded p-3">
          {error}
        </div>
      </div>
    );
  }

  if (!fraudData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-600" />
          Fraud Detection Summary
        </h3>
        <div className="text-gray-500">No fraud data available</div>
      </div>
    );
  }

  // Session level display (detailed view)
  if (sessionId && fraudData.fraud_analysis_available !== false) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-blue-600" />
          Session Fraud Analysis
        </h3>

        {fraudData.fraud_analysis_available === false ? (
          <div className="text-gray-500 bg-gray-50 border border-gray-200 rounded p-4">
            {fraudData.message || 'No fraud analysis has been performed for this session'}
          </div>
        ) : (
          <div className="space-y-6">
            {/* Overall Score Card */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Overall Fraud Score</p>
                  <p className="text-3xl font-bold mt-1">
                    {fraudData.overall_fraud_score !== null 
                      ? (fraudData.overall_fraud_score * 100).toFixed(1) 
                      : 'N/A'}%
                  </p>
                  <p className="text-sm mt-1">
                    Risk Level: <span className={`font-semibold ${
                      fraudData.risk_level === 'CRITICAL' ? 'text-red-600' :
                      fraudData.risk_level === 'HIGH' ? 'text-red-500' :
                      fraudData.risk_level === 'MEDIUM' ? 'text-orange-500' :
                      'text-green-600'
                    }`}>
                      {fraudData.risk_level || 'LOW'}
                    </span>
                  </p>
                </div>
                <div className="text-right">
                  {fraudData.is_duplicate && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-orange-100 text-orange-800">
                      <AlertTriangle className="w-4 h-4 mr-1" />
                      Duplicate
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Detailed Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* IP Analysis */}
              {fraudData.ip_analysis && (
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold mb-3 flex items-center gap-2">
                    <Activity className="w-4 h-4" />
                    IP Address Analysis
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">IP Address:</span>
                      <span className="font-mono font-medium">{fraudData.ip_analysis.ip_address || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Usage Count:</span>
                      <span className="font-semibold">{fraudData.ip_analysis.usage_count || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Sessions Today:</span>
                      <span className="font-semibold">{fraudData.ip_analysis.sessions_today || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Risk Score:</span>
                      <span className={`font-semibold ${
                        fraudData.ip_analysis.risk_score >= 0.7 ? 'text-red-600' :
                        fraudData.ip_analysis.risk_score >= 0.4 ? 'text-orange-600' :
                        'text-green-600'
                      }`}>
                        {fraudData.ip_analysis.risk_score !== null 
                          ? (fraudData.ip_analysis.risk_score * 100).toFixed(1) + '%'
                          : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Device Fingerprint */}
              {fraudData.device_fingerprint && (
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold mb-3 flex items-center gap-2">
                    <Shield className="w-4 h-4" />
                    Device Fingerprint
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Fingerprint:</span>
                      <span className="font-mono text-xs truncate max-w-[150px]">
                        {fraudData.device_fingerprint.fingerprint 
                          ? fraudData.device_fingerprint.fingerprint.substring(0, 16) + '...' 
                          : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Usage Count:</span>
                      <span className="font-semibold">{fraudData.device_fingerprint.usage_count || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Risk Score:</span>
                      <span className={`font-semibold ${
                        fraudData.device_fingerprint.risk_score >= 0.7 ? 'text-red-600' :
                        fraudData.device_fingerprint.risk_score >= 0.4 ? 'text-orange-600' :
                        'text-green-600'
                      }`}>
                        {fraudData.device_fingerprint.risk_score !== null 
                          ? (fraudData.device_fingerprint.risk_score * 100).toFixed(1) + '%'
                          : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Duplicate Responses */}
              {fraudData.duplicate_responses && (
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold mb-3 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    Duplicate Responses
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Similarity Score:</span>
                      <span className="font-semibold">
                        {fraudData.duplicate_responses.similarity_score !== null 
                          ? (fraudData.duplicate_responses.similarity_score * 100).toFixed(1) + '%'
                          : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Duplicate Count:</span>
                      <span className="font-semibold text-orange-600">
                        {fraudData.duplicate_responses.duplicate_count || 0}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Velocity */}
              {fraudData.velocity && (
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold mb-3 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    Response Velocity
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Responses/Hour:</span>
                      <span className="font-semibold">{fraudData.velocity.responses_per_hour || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Risk Score:</span>
                      <span className={`font-semibold ${
                        fraudData.velocity.risk_score >= 0.7 ? 'text-red-600' :
                        fraudData.velocity.risk_score >= 0.4 ? 'text-orange-600' :
                        'text-green-600'
                      }`}>
                        {fraudData.velocity.risk_score !== null 
                          ? (fraudData.velocity.risk_score * 100).toFixed(1) + '%'
                          : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Flag Reasons */}
            {fraudData.flag_reasons && Object.keys(fraudData.flag_reasons).length > 0 && (
              <div className="border rounded-lg p-4 bg-yellow-50 border-yellow-200">
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-yellow-600" />
                  Flag Reasons
                </h4>
                <div className="space-y-1">
                  {Object.entries(fraudData.flag_reasons).map(([reason, details]) => (
                    <div key={reason} className="text-sm">
                      <span className="font-medium text-gray-700">{reason.replace(/_/g, ' ')}:</span>
                      <span className="ml-2 text-gray-600">
                        {typeof details === 'object' ? JSON.stringify(details) : details}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Aggregated level display (Survey/Platform/Respondent)
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Shield className="w-5 h-5 text-blue-600" />
        Fraud Detection Summary
      </h3>

      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <p className="text-sm font-medium text-gray-600 mb-1">Sessions Analyzed</p>
            <p className="text-2xl font-bold text-gray-900">
              {fraudData.total_sessions_analyzed || 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              of {fraudData.total_sessions || 0} total
            </p>
          </div>

          <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
            <p className="text-sm font-medium text-gray-600 mb-1">Duplicate Sessions</p>
            <p className="text-2xl font-bold text-orange-600">
              {fraudData.duplicate_sessions || 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {fraudData.duplicate_rate ? `${fraudData.duplicate_rate.toFixed(1)}%` : '0%'} rate
            </p>
          </div>

          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
            <p className="text-sm font-medium text-gray-600 mb-1">High Risk Sessions</p>
            <p className="text-2xl font-bold text-red-600">
              {fraudData.high_risk_sessions || 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {fraudData.high_risk_rate ? `${fraudData.high_risk_rate.toFixed(1)}%` : '0%'} rate
            </p>
          </div>

          <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
            <p className="text-sm font-medium text-gray-600 mb-1">Avg Fraud Score</p>
            <p className="text-2xl font-bold text-indigo-600">
              {fraudData.average_fraud_score 
                ? fraudData.average_fraud_score.toFixed(2) 
                : '0.00'}
            </p>
          </div>
        </div>

        {/* Risk Distribution */}
        {fraudData.risk_distribution && (
          <div className="border rounded-lg p-4">
            <h4 className="font-semibold mb-3">Risk Distribution</h4>
            <div className="grid grid-cols-4 gap-4">
              {Object.entries(fraudData.risk_distribution).map(([level, count]) => (
                <div key={level} className="text-center">
                  <p className="text-2xl font-bold text-gray-900">{count}</p>
                  <p className={`text-sm font-medium ${
                    level === 'CRITICAL' ? 'text-red-600' :
                    level === 'HIGH' ? 'text-red-500' :
                    level === 'MEDIUM' ? 'text-orange-500' :
                    'text-green-600'
                  }`}>
                    {level}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Fraud Methods */}
        {fraudData.fraud_methods && (
          <div className="border rounded-lg p-4">
            <h4 className="font-semibold mb-3">Fraud Detection Methods</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
              {Object.entries(fraudData.fraud_methods).map(([method, count]) => (
                <div key={method} className="bg-gray-50 rounded p-3">
                  <p className="text-xs text-gray-600 mb-1">
                    {method.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </p>
                  <p className="text-xl font-bold text-gray-900">{count}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HierarchicalFraudWidget;
