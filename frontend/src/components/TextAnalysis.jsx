import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  BarChart3, 
  Users, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Calendar,
  Filter,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Search,
  ChevronDown,
  ChevronRight,
  ExternalLink
} from 'lucide-react';
import { toast } from 'react-toastify';
import { textAnalysisService } from '../services/apiService';
import { Link } from 'react-router-dom';

const TextAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Data state
  const [summaryData, setSummaryData] = useState(null);
  const [respondentsData, setRespondentsData] = useState(null);
  
  // Filter state
  const [filters, setFilters] = useState({
    surveyId: '',
    days: 30,
    page: 1,
    limit: 50
  });
  
  // UI state
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [selectedRespondents, setSelectedRespondents] = useState(new Set());

  // Load data on component mount and when filters change
  useEffect(() => {
    loadData();
  }, [filters]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [summary, respondents] = await Promise.all([
        textAnalysisService.getDashboardSummary(filters.days, filters.surveyId || null),
        textAnalysisService.getRespondentAnalysis(filters)
      ]);
      
      setSummaryData(summary);
      setRespondentsData(respondents);
    } catch (err) {
      setError(err.message);
      console.error('Error loading text analysis data:', err);
      toast.error('Failed to load text analysis data');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      page: 1 // Reset to first page when filters change
    }));
  };

  const handlePageChange = (newPage) => {
    setFilters(prev => ({ ...prev, page: newPage }));
  };

  const toggleRowExpansion = (sessionId) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sessionId)) {
        newSet.delete(sessionId);
      } else {
        newSet.add(sessionId);
      }
      return newSet;
    });
  };

  const getQualityColor = (score) => {
    if (score === null || score === undefined) return 'text-gray-600';
    if (score >= 70) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getQualityIcon = (score) => {
    if (score === null || score === undefined) return <XCircle className="w-4 h-4 text-gray-400" />;
    if (score >= 70) return <CheckCircle className="w-4 h-4 text-green-600" />;
    if (score >= 50) return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
    return <XCircle className="w-4 h-4 text-red-600" />;
  };

  const exportToCSV = () => {
    if (!respondentsData?.respondents) return;
    
    const headers = [
      'Respondent ID',
      'Session ID', 
      'Survey ID',
      'Response Count',
      'Avg Quality Score',
      'Flagged Count',
      'Flagged Percentage',
      'Flag Reasons',
      'Analyzed At'
    ];
    
    const csvData = [
      headers.join(','),
      ...respondentsData.respondents.map(respondent => [
        respondent.respondent_id || 'Anonymous',
        respondent.session_id,
        respondent.survey_id || '',
        respondent.response_count || 0,
        respondent.avg_quality_score?.toFixed(1) || 'N/A',
        respondent.flagged_count || 0,
        respondent.flagged_percentage?.toFixed(1) || '0.0',
        `"${Object.keys(respondent.flag_reasons_summary || {}).join('; ') || 'None'}"`,
        respondent.analyzed_at || 'Not analyzed'
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvData], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `text-analysis-respondents-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    
    toast.success('CSV exported successfully');
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Text Quality Analysis</h1>
        <p className="text-gray-600">
          Comprehensive analysis of survey response quality with detailed flagging and quality metrics.
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <Filter className="w-5 h-5 mr-2" />
          Filters & Controls
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Survey ID (Optional)
            </label>
            <input
              type="text"
              value={filters.surveyId}
              onChange={(e) => handleFilterChange('surveyId', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Filter by survey ID..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Time Range (Days)
            </label>
            <select
              value={filters.days}
              onChange={(e) => handleFilterChange('days', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
              <option value={365}>Last year</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Per Page
            </label>
            <select
              value={filters.limit}
              onChange={(e) => handleFilterChange('limit', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={exportToCSV}
              disabled={!respondentsData?.respondents?.length}
              className="w-full bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </button>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      {summaryData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <BarChart3 className="w-8 h-8 text-blue-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-blue-600">Total Responses</p>
                <p className="text-2xl font-bold text-blue-900">{summaryData.total_responses}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <TrendingUp className="w-8 h-8 text-green-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-green-600">Avg Quality Score</p>
                <p className={`text-2xl font-bold ${getQualityColor(summaryData.avg_quality_score)}`}>
                  {summaryData.avg_quality_score?.toFixed(1) || 'N/A'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <AlertTriangle className="w-8 h-8 text-red-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-red-600">Flagged Responses</p>
                <p className="text-2xl font-bold text-red-900">{summaryData.flagged_count}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <TrendingDown className="w-8 h-8 text-yellow-600 mr-3" />
              <div>
                <p className="text-sm font-medium text-yellow-600">Flagged Rate</p>
                <p className="text-2xl font-bold text-yellow-900">{summaryData.flagged_percentage.toFixed(1)}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quality Distribution Chart */}
      {summaryData?.quality_distribution && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quality Score Distribution</h3>
          <div className="flex items-end space-x-1 h-20">
            {Object.entries(summaryData.quality_distribution).map(([bucket, count]) => {
              const maxCount = Math.max(...Object.values(summaryData.quality_distribution));
              const height = maxCount > 0 ? (count / maxCount) * 100 : 0;
              const bucketNum = parseInt(bucket.split('-')[0]);
              
              return (
                <div key={bucket} className="flex-1 flex flex-col items-center">
                  <div 
                    className={`w-full rounded-t ${
                      bucketNum >= 70 ? 'bg-green-500' : 
                      bucketNum >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ height: `${height}%` }}
                    title={`${bucket}: ${count} responses`}
                  />
                  <div className="text-xs text-gray-500 mt-1">{bucketNum}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Respondents Table */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900">Respondent Analysis</h3>
            {loading && (
              <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />
            )}
          </div>
        </div>

        {loading && !respondentsData ? (
          <div className="p-12 text-center">
            <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-4" />
            <p className="text-gray-600">Loading respondent data...</p>
          </div>
        ) : error ? (
          <div className="p-12 text-center">
            <AlertTriangle className="w-8 h-8 text-red-500 mx-auto mb-4" />
            <p className="text-red-600 mb-4">{error}</p>
            <button 
              onClick={loadData}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        ) : !respondentsData?.respondents?.length ? (
          <div className="p-12 text-center">
            <FileText className="w-8 h-8 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No respondent data found for the selected filters.</p>
          </div>
        ) : (
          <>
            {/* Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Respondent
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Survey
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Quality Score
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Responses
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Flagged
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Analyzed
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {respondentsData.respondents.map((respondent) => {
                    const isExpanded = expandedRows.has(respondent.session_id);
                    
                    return (
                      <React.Fragment key={respondent.session_id}>
                        <tr className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {respondent.respondent_id || 'Anonymous'}
                              </div>
                              <div className="text-sm text-gray-500">
                                {respondent.session_id.substring(0, 8)}...
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {respondent.survey_id || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              {getQualityIcon(respondent.avg_quality_score)}
                              <span className={`ml-2 font-medium ${getQualityColor(respondent.avg_quality_score)}`}>
                                {respondent.avg_quality_score?.toFixed(1) || 'N/A'}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {respondent.response_count}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              {respondent.flagged_count > 0 ? (
                                <AlertTriangle className="w-4 h-4 text-red-500 mr-2" />
                              ) : (
                                <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                              )}
                              <span className={`text-sm ${
                                respondent.flagged_count > 0 ? 'text-red-600' : 'text-green-600'
                              }`}>
                                {respondent.flagged_count}/{respondent.response_count}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatDate(respondent.analyzed_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => toggleRowExpansion(respondent.session_id)}
                                className="text-blue-600 hover:text-blue-900"
                              >
                                {isExpanded ? (
                                  <ChevronDown className="w-4 h-4" />
                                ) : (
                                  <ChevronRight className="w-4 h-4" />
                                )}
                              </button>
                              <Link
                                to={`/sessions/${respondent.session_id}`}
                                className="text-blue-600 hover:text-blue-900"
                              >
                                <ExternalLink className="w-4 h-4" />
                              </Link>
                            </div>
                          </td>
                        </tr>
                        
                        {/* Expanded Row Details */}
                        {isExpanded && (
                          <tr>
                            <td colSpan="7" className="px-6 py-4 bg-gray-50">
                              <div className="space-y-4">
                                <div>
                                  <h4 className="font-medium text-gray-900 mb-2">Quality Metrics</h4>
                                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                    <div>
                                      <span className="text-gray-500">Flagged Rate:</span>
                                      <span className="ml-2 font-medium">
                                        {respondent.flagged_percentage?.toFixed(1)}%
                                      </span>
                                    </div>
                                    <div>
                                      <span className="text-gray-500">Quality Scores:</span>
                                      <span className="ml-2 font-medium">
                                        {respondent.quality_scores?.length || 0} analyzed
                                      </span>
                                    </div>
                                  </div>
                                </div>
                                
                                {Object.keys(respondent.flag_reasons_summary || {}).length > 0 && (
                                  <div>
                                    <h4 className="font-medium text-gray-900 mb-2">Flag Reasons</h4>
                                    <div className="flex flex-wrap gap-2">
                                      {Object.entries(respondent.flag_reasons_summary).map(([reason, count]) => (
                                        <span 
                                          key={reason}
                                          className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded"
                                        >
                                          {reason.replace('_', ' ')} ({count})
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {respondentsData.pagination && (
              <div className="px-6 py-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-700">
                    Showing {((respondentsData.pagination.page - 1) * respondentsData.pagination.limit) + 1} to{' '}
                    {Math.min(respondentsData.pagination.page * respondentsData.pagination.limit, respondentsData.pagination.total)} of{' '}
                    {respondentsData.pagination.total} results
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handlePageChange(respondentsData.pagination.page - 1)}
                      disabled={respondentsData.pagination.page <= 1}
                      className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <span className="px-3 py-1 text-sm">
                      Page {respondentsData.pagination.page} of {respondentsData.pagination.pages}
                    </span>
                    <button
                      onClick={() => handlePageChange(respondentsData.pagination.page + 1)}
                      disabled={respondentsData.pagination.page >= respondentsData.pagination.pages}
                      className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default TextAnalysis;
