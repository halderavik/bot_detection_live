/**
 * Text Quality Widget Component
 * 
 * Displays text quality analysis results including quality scores,
 * flagged responses, and quality trends for survey sessions.
 */

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  BarChart3,
  Filter,
  Download
} from 'lucide-react';
import { textAnalysisService } from '../services/apiService';

const TextQualityWidget = ({ sessionId, onDataLoad }) => {
  const [qualityData, setQualityData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // 'all', 'flagged', 'high_quality', 'low_quality'
  const [selectedResponse, setSelectedResponse] = useState(null);

  useEffect(() => {
    if (sessionId) {
      loadQualityData();
    }
  }, [sessionId]);

  const loadQualityData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await textAnalysisService.getSessionSummary(sessionId);
      setQualityData(data);
      
      if (onDataLoad) {
        onDataLoad(data);
      }
    } catch (err) {
      const status = err.response?.status;
      const message = status ? `Failed to load quality data: ${status}` : err.message || 'Failed to load quality data';
      setError(message);
      console.error('Error loading text quality data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getQualityColor = (score) => {
    if (score >= 70) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getQualityIcon = (score) => {
    if (score >= 70) return <CheckCircle className="w-4 h-4 text-green-600" />;
    if (score >= 50) return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
    return <XCircle className="w-4 h-4 text-red-600" />;
  };

  const getFilteredResponses = () => {
    if (!qualityData?.responses) return [];
    
    switch (filter) {
      case 'flagged':
        return qualityData.responses.filter(r => r.is_flagged);
      case 'high_quality':
        return qualityData.responses.filter(r => r.quality_score >= 70);
      case 'low_quality':
        return qualityData.responses.filter(r => r.quality_score < 50);
      default:
        return qualityData.responses;
    }
  };

  const getFlagReasons = (flagReasons) => {
    if (!flagReasons || Object.keys(flagReasons).length === 0) return [];
    return Object.keys(flagReasons).map(flag => ({
      type: flag,
      confidence: flagReasons[flag]?.confidence || 0,
      reason: flagReasons[flag]?.reason || 'No reason provided'
    }));
  };

  const exportQualityData = () => {
    if (!qualityData) return;
    
    const csvData = [
      ['Response ID', 'Quality Score', 'Flagged', 'Flag Reasons', 'Analyzed At', 'Text Preview'].join(','),
      ...qualityData.responses.map(r => [
        r.response_id,
        r.quality_score || 'N/A',
        r.is_flagged ? 'Yes' : 'No',
        r.flag_reasons ? Object.keys(r.flag_reasons).join('; ') : 'None',
        r.analyzed_at || 'N/A',
        `"${r.truncated_text || ''}"`
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvData], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `text-quality-${sessionId}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded w-5/6"></div>
            <div className="h-3 bg-gray-200 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center text-red-600">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
          <p className="text-sm">Failed to load text quality data</p>
          <p className="text-xs text-gray-500 mt-1">{error}</p>
          <button 
            onClick={loadQualityData}
            className="mt-2 px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!qualityData || qualityData.total_responses === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <BarChart3 className="w-5 h-5 mr-2" />
          Text Quality Analysis
        </h3>
        <div className="text-center text-gray-500 py-8">
          <BarChart3 className="w-12 h-12 mx-auto mb-2 text-gray-300" />
          <p>No text responses analyzed yet</p>
          <p className="text-sm">Text quality analysis will appear here once responses are submitted</p>
        </div>
      </div>
    );
  }

  const filteredResponses = getFilteredResponses();
  const avgQuality = qualityData.avg_quality_score || 0;
  const flaggedPercentage = qualityData.flagged_percentage || 0;

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            Text Quality Analysis
          </h3>
          <button
            onClick={exportQualityData}
            className="flex items-center px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
          >
            <Download className="w-4 h-4 mr-1" />
            Export
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="p-6 border-b border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{qualityData.total_responses}</div>
            <div className="text-sm text-gray-500">Total Responses</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${getQualityColor(avgQuality)}`}>
              {avgQuality.toFixed(1)}
            </div>
            <div className="text-sm text-gray-500">Avg Quality Score</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{qualityData.flagged_count}</div>
            <div className="text-sm text-gray-500">Flagged Responses</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${flaggedPercentage > 30 ? 'text-red-600' : flaggedPercentage > 15 ? 'text-yellow-600' : 'text-green-600'}`}>
              {flaggedPercentage.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500">Flagged Rate</div>
          </div>
        </div>
      </div>

      {/* Quality Trend Chart */}
      <div className="p-6 border-b border-gray-200">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Quality Distribution</h4>
        <div className="flex items-end space-x-1 h-20">
          {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(bucket => {
            const bucketMin = bucket * 10;
            const bucketMax = (bucket + 1) * 10 - 1;
            const count = qualityData.responses.filter(r => 
              r.quality_score >= bucketMin && r.quality_score <= bucketMax
            ).length;
            const maxCount = Math.max(...[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(b => 
              qualityData.responses.filter(r => 
                r.quality_score >= b * 10 && r.quality_score <= (b + 1) * 10 - 1
              ).length
            ));
            const height = maxCount > 0 ? (count / maxCount) * 100 : 0;
            
            return (
              <div key={bucket} className="flex-1 flex flex-col items-center">
                <div 
                  className={`w-full rounded-t ${
                    bucketMin >= 70 ? 'bg-green-500' : 
                    bucketMin >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ height: `${height}%` }}
                  title={`${bucketMin}-${bucketMax}: ${count} responses`}
                />
                <div className="text-xs text-gray-500 mt-1">{bucketMin}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Filters */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <Filter className="w-4 h-4 text-gray-400" />
          <div className="flex space-x-2">
            {[
              { key: 'all', label: 'All Responses' },
              { key: 'flagged', label: 'Flagged Only' },
              { key: 'high_quality', label: 'High Quality' },
              { key: 'low_quality', label: 'Low Quality' }
            ].map(filterOption => (
              <button
                key={filterOption.key}
                onClick={() => setFilter(filterOption.key)}
                className={`px-3 py-1 text-sm rounded ${
                  filter === filterOption.key
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {filterOption.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Response List */}
      <div className="p-6">
        <h4 className="text-sm font-medium text-gray-900 mb-3">
          Responses ({filteredResponses.length})
        </h4>
        <div className="space-y-3">
          {filteredResponses.map((response) => {
            const flagReasons = getFlagReasons(response.flag_reasons);
            
            return (
              <div 
                key={response.response_id}
                className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                  selectedResponse?.response_id === response.response_id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedResponse(
                  selectedResponse?.response_id === response.response_id ? null : response
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-2">
                      {getQualityIcon(response.quality_score)}
                      <span className={`font-medium ${getQualityColor(response.quality_score)}`}>
                        {response.quality_score?.toFixed(1) || 'N/A'}
                      </span>
                      {response.is_flagged && (
                        <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded">
                          Flagged
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 truncate">
                      {response.truncated_text || 'No text preview available'}
                    </p>
                    {flagReasons.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {flagReasons.map((flag, index) => (
                          <span 
                            key={index}
                            className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded"
                          >
                            {flag.type.replace('_', ' ')}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="ml-4 text-xs text-gray-500">
                    {response.analyzed_at ? 
                      new Date(response.analyzed_at).toLocaleDateString() : 
                      'Not analyzed'
                    }
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {filteredResponses.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            <BarChart3 className="w-8 h-8 mx-auto mb-2 text-gray-300" />
            <p>No responses match the current filter</p>
          </div>
        )}
      </div>

      {/* Response Detail Modal */}
      {selectedResponse && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Response Analysis Details</h3>
                <button
                  onClick={() => setSelectedResponse(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Response Text
                  </label>
                  <div className="p-3 bg-gray-50 rounded border text-sm">
                    {selectedResponse.truncated_text || 'No text available'}
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Quality Score
                    </label>
                    <div className={`text-2xl font-bold ${getQualityColor(selectedResponse.quality_score)}`}>
                      {selectedResponse.quality_score?.toFixed(1) || 'N/A'}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Status
                    </label>
                    <div className="flex items-center space-x-2">
                      {getQualityIcon(selectedResponse.quality_score)}
                      <span className={selectedResponse.is_flagged ? 'text-red-600' : 'text-green-600'}>
                        {selectedResponse.is_flagged ? 'Flagged' : 'Clean'}
                      </span>
                    </div>
                  </div>
                </div>

                {getFlagReasons(selectedResponse.flag_reasons).length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Flag Reasons
                    </label>
                    <div className="space-y-2">
                      {getFlagReasons(selectedResponse.flag_reasons).map((flag, index) => (
                        <div key={index} className="p-3 bg-yellow-50 border border-yellow-200 rounded">
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-yellow-800">
                              {flag.type.replace('_', ' ').toUpperCase()}
                            </span>
                            <span className="text-sm text-yellow-600">
                              {(flag.confidence * 100).toFixed(0)}% confidence
                            </span>
                          </div>
                          <p className="text-sm text-yellow-700">{flag.reason}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TextQualityWidget;
