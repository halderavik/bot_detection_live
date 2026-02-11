import React, { useState, useEffect } from 'react';
import { hierarchicalService } from '../services/apiService';
import { Clock, Zap, Hourglass, AlertTriangle } from 'lucide-react';

/**
 * PerQuestionTimingTable Component
 * 
 * Displays per-question timing analysis in a table format for SessionDetails.
 * Shows question text, response time, speeder/flatliner flags, and anomalies.
 */
const PerQuestionTimingTable = ({ 
  surveyId, 
  platformId, 
  respondentId, 
  sessionId 
}) => {
  const [timingData, setTimingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortColumn, setSortColumn] = useState('question_time_ms');
  const [sortDirection, setSortDirection] = useState('desc');

  useEffect(() => {
    if (surveyId && platformId && respondentId && sessionId) {
      loadTimingData();
    }
  }, [surveyId, platformId, respondentId, sessionId]);

  const loadTimingData = async () => {
    try {
      setLoading(true);
      setError(null);

      // For per-question timing, we need to fetch session-level timing analysis
      // which should include per-question details
      const data = await hierarchicalService.getTimingAnalysisSummary(
        surveyId,
        platformId,
        respondentId,
        sessionId
      );

      setTimingData(data);
    } catch (err) {
      console.error('Error loading per-question timing data:', err);
      setError('Failed to load timing data');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (ms) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('desc');
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-blue-600" />
          Per-Question Timing Analysis
        </h3>
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-full"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-blue-600" />
          Per-Question Timing Analysis
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
          Per-Question Timing Analysis
        </h3>
        <div className="text-gray-500">No timing analysis data available for this session</div>
      </div>
    );
  }

  // Note: The API currently returns summary data, not per-question details
  // This component is prepared for when per-question details are added to the API
  // For now, we'll show a message indicating that detailed per-question data
  // would be displayed here once the API endpoint is enhanced

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Clock className="w-5 h-5 text-blue-600" />
        Per-Question Timing Analysis
      </h3>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('question_text')}
              >
                Question
                {sortColumn === 'question_text' && (
                  <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
              <th 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('question_time_ms')}
              >
                Response Time
                {sortColumn === 'question_time_ms' && (
                  <span className="ml-1">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                )}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Flags
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Anomaly
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {/* Summary row since per-question details aren't available yet */}
            <tr>
              <td colSpan="4" className="px-6 py-4 text-sm text-gray-500 text-center">
                <div className="space-y-2">
                  <p>Per-question timing details will be displayed here once available.</p>
                  <div className="grid grid-cols-3 gap-4 mt-4">
                    <div className="text-center">
                      <p className="text-xs text-gray-600">Speeders</p>
                      <p className="text-lg font-bold text-red-600">{timingData.speeders_count || 0}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-600">Flatliners</p>
                      <p className="text-lg font-bold text-orange-600">{timingData.flatliners_count || 0}</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-600">Avg Time</p>
                      <p className="text-lg font-bold text-blue-600">{formatTime(timingData.avg_response_time_ms)}</p>
                    </div>
                  </div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Note about future enhancement */}
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-700">
        <p className="font-medium mb-1">Note:</p>
        <p>
          Detailed per-question timing data will be available once the API endpoint is enhanced 
          to return individual question timing records. Currently showing summary statistics.
        </p>
      </div>
    </div>
  );
};

export default PerQuestionTimingTable;
