import React, { useState, useEffect } from 'react';
import { hierarchicalService } from '../services/apiService';
import { BarChart3, TrendingDown, AlertTriangle, Activity } from 'lucide-react';

/**
 * GridAnalysisWidget Component
 * 
 * Displays grid/matrix question analysis summary at different hierarchy levels:
 * - Survey level
 * - Platform level
 * - Respondent level
 * - Session level
 */
const GridAnalysisWidget = ({ 
  surveyId, 
  platformId = null, 
  respondentId = null, 
  sessionId = null,
  filters = {}
}) => {
  const [gridData, setGridData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadGridData();
  }, [surveyId, platformId, respondentId, sessionId, filters]);

  const loadGridData = async () => {
    if (!surveyId) return;

    try {
      setLoading(true);
      setError(null);

      const data = await hierarchicalService.getGridAnalysisSummary(
        surveyId,
        platformId,
        respondentId,
        sessionId,
        filters
      );

      setGridData(data);
    } catch (err) {
      console.error('Error loading grid analysis data:', err);
      setError('Failed to load grid analysis data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-600" />
          Grid Analysis Summary
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
          <BarChart3 className="w-5 h-5 text-blue-600" />
          Grid Analysis Summary
        </h3>
        <div className="text-red-600 bg-red-50 border border-red-200 rounded p-3">
          {error}
        </div>
      </div>
    );
  }

  if (!gridData || gridData.total_responses === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-600" />
          Grid Analysis Summary
        </h3>
        <div className="text-gray-500">No grid question data available</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <BarChart3 className="w-5 h-5 text-blue-600" />
        Grid Analysis Summary
      </h3>

      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <p className="text-sm font-medium text-gray-600 mb-1">Total Responses</p>
            <p className="text-2xl font-bold text-gray-900">
              {gridData.total_responses || 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {gridData.unique_questions || 0} unique questions
            </p>
          </div>

          <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
            <p className="text-sm font-medium text-gray-600 mb-1 flex items-center gap-1">
              <AlertTriangle className="w-4 h-4" />
              Straight-Lined
            </p>
            <p className="text-2xl font-bold text-orange-600">
              {gridData.straight_lined_count || 0}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {gridData.straight_lined_percentage ? gridData.straight_lined_percentage.toFixed(1) : '0'}% of responses
            </p>
          </div>

          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
            <p className="text-sm font-medium text-gray-600 mb-1 flex items-center gap-1">
              <TrendingDown className="w-4 h-4" />
              Avg Variance
            </p>
            <p className="text-2xl font-bold text-purple-600">
              {gridData.avg_variance_score ? gridData.avg_variance_score.toFixed(2) : '0.00'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {gridData.avg_variance_score < 0.3 ? 'Low variance' : gridData.avg_variance_score > 0.7 ? 'High variance' : 'Moderate variance'}
            </p>
          </div>

          <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
            <p className="text-sm font-medium text-gray-600 mb-1 flex items-center gap-1">
              <Activity className="w-4 h-4" />
              Satisficing Score
            </p>
            <p className="text-2xl font-bold text-indigo-600">
              {gridData.avg_satisficing_score ? gridData.avg_satisficing_score.toFixed(2) : '0.00'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {gridData.avg_satisficing_score >= 0.7 ? 'High satisficing' : gridData.avg_satisficing_score < 0.3 ? 'Low satisficing' : 'Moderate satisficing'}
            </p>
          </div>
        </div>

        {/* Pattern Distribution */}
        {gridData.pattern_distribution && Object.keys(gridData.pattern_distribution).length > 0 && (
          <div className="border rounded-lg p-4">
            <h4 className="font-semibold mb-3">Pattern Distribution</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(gridData.pattern_distribution).map(([pattern, count]) => (
                <div key={pattern} className="bg-gray-50 rounded p-3">
                  <p className="text-xs text-gray-600 mb-1 capitalize">
                    {pattern.replace(/_/g, ' ')}
                  </p>
                  <p className="text-xl font-bold text-gray-900">{count}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Alert for High Straight-Lining */}
        {gridData.straight_lined_percentage && gridData.straight_lined_percentage > 50 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-yellow-800 mb-1">High Straight-Lining Detected</h4>
                <p className="text-sm text-yellow-700">
                  {gridData.straight_lined_percentage.toFixed(1)}% of grid responses show straight-lining behavior, 
                  which may indicate satisficing or bot activity.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Alert for High Satisficing */}
        {gridData.avg_satisficing_score && gridData.avg_satisficing_score >= 0.7 && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-orange-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-orange-800 mb-1">High Satisficing Behavior</h4>
                <p className="text-sm text-orange-700">
                  Average satisficing score of {gridData.avg_satisficing_score.toFixed(2)} indicates 
                  respondents may be providing minimal effort responses.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GridAnalysisWidget;
