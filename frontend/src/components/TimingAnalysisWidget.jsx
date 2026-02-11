import React, { useState, useEffect } from 'react';
import { hierarchicalService } from '../services/apiService';
import { Clock, AlertTriangle, Zap, Hourglass } from 'lucide-react';

/**
 * TimingAnalysisWidget Component
 * 
 * Displays timing analysis summary at different hierarchy levels:
 * - Survey level
 * - Platform level
 * - Respondent level
 * - Session level
 */
const TimingAnalysisWidget = ({ 
  surveyId, 
  platformId = null, 
  respondentId = null, 
  sessionId = null,
  filters = {}
}) => {
  const [timingData, setTimingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTimingData();
  }, [surveyId, platformId, respondentId, sessionId, filters]);

  const loadTimingData = async () => {
    if (!surveyId) return;

    try {
      setLoading(true);
      setError(null);

      const data = await hierarchicalService.getTimingAnalysisSummary(
        surveyId,
        platformId,
        respondentId,
        sessionId,
        filters
      );

      setTimingData(data);
    } catch (err) {
      console.error('Error loading timing analysis data:', err);
      setError('Failed to load timing analysis data');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (ms) => {
    if (!ms) return '0s';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-blue-600" />
          Timing Analysis Summary
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
          <Clock className="w-5 h-5 text-blue-600" />
          Timing Analysis Summary
        </h3>
        <div className="text-red-600 bg-red-50 border border-red-200 rounded p-3">
          {error}
        </div>
      </div>
    );
  }

  if (!timingData || timingData.total_analyses === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-blue-600" />
          Timing Analysis Summary
        </h3>
        <div className="text-gray-500">No timing analysis data available</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Clock className="w-5 h-5 text-blue-600" />
        Timing Analysis Summary
      </h3>

      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <p className="text-sm font-medium text-gray-600 mb-1">Total Analyses</p>
            <p className="text-2xl font-bold text-gray-900">
              {timingData.total_analyses || 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {timingData.unique_questions || 0} unique questions
            </p>
          </div>

          <div className="bg-red-50 rounded-lg p-4 border border-red-200">
            <p className="text-sm font-medium text-gray-600 mb-1 flex items-center gap-1">
              <Zap className="w-4 h-4" />
              Speeders
            </p>
            <p className="text-2xl font-bold text-red-600">
              {timingData.speeders_count || 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {timingData.speeders_percentage ? timingData.speeders_percentage.toFixed(1) : '0'}% of responses
            </p>
          </div>

          <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
            <p className="text-sm font-medium text-gray-600 mb-1 flex items-center gap-1">
              <Hourglass className="w-4 h-4" />
              Flatliners
            </p>
            <p className="text-2xl font-bold text-orange-600">
              {timingData.flatliners_count || 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {timingData.flatliners_percentage ? timingData.flatliners_percentage.toFixed(1) : '0'}% of responses
            </p>
          </div>

          <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
            <p className="text-sm font-medium text-gray-600 mb-1">Avg Response Time</p>
            <p className="text-2xl font-bold text-indigo-600">
              {formatTime(timingData.avg_response_time_ms)}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Median: {formatTime(timingData.median_response_time_ms)}
            </p>
          </div>
        </div>

        {/* Timing Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border rounded-lg p-4">
            <h4 className="font-semibold mb-3">Response Time Statistics</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Average:</span>
                <span className="font-semibold">{formatTime(timingData.avg_response_time_ms)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Median:</span>
                <span className="font-semibold">{formatTime(timingData.median_response_time_ms)}</span>
              </div>
            </div>
          </div>

          <div className="border rounded-lg p-4">
            <h4 className="font-semibold mb-3">Anomaly Detection</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Anomalies Detected:</span>
                <span className="font-semibold text-orange-600">
                  {timingData.anomalies_count || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Anomaly Rate:</span>
                <span className="font-semibold">
                  {timingData.anomalies_percentage ? timingData.anomalies_percentage.toFixed(1) : '0'}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Alert for High Speeder Rate */}
        {timingData.speeders_percentage && timingData.speeders_percentage > 20 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-red-800 mb-1">High Speeder Rate Detected</h4>
                <p className="text-sm text-red-700">
                  {timingData.speeders_percentage.toFixed(1)}% of responses are speeders (response time &lt; 2 seconds), 
                  which may indicate bot activity or low-quality responses.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Alert for High Flatliner Rate */}
        {timingData.flatliners_percentage && timingData.flatliners_percentage > 10 && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-orange-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-orange-800 mb-1">High Flatliner Rate Detected</h4>
                <p className="text-sm text-orange-700">
                  {timingData.flatliners_percentage.toFixed(1)}% of responses are flatliners (response time &gt; 5 minutes), 
                  which may indicate disengagement or multitasking.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TimingAnalysisWidget;
