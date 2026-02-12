import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  BarChart3, 
  Users, 
  Bot, 
  User, 
  Calendar,
  Filter,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Clock,
  MessageSquare,
  TrendingUp,
  ShieldAlert,
  LayoutGrid,
  XCircle
} from 'lucide-react';
import { toast } from 'react-toastify';
import { reportService, textAnalysisService } from '../services/apiService';

const ReportBuilder = () => {
  const [surveys, setSurveys] = useState([]);
  const [selectedSurvey, setSelectedSurvey] = useState('');
  const [reportType, setReportType] = useState('summary');
  const [loading, setLoading] = useState(false);
  const [summaryReport, setSummaryReport] = useState(null);
  const [detailedReport, setDetailedReport] = useState(null);
  const [filters, setFilters] = useState({
    includeInactive: false,
    dateFrom: '',
    dateTo: ''
  });
  const [selectedRespondent, setSelectedRespondent] = useState(null);

  // Load available surveys on component mount
  useEffect(() => {
    loadSurveys();
  }, []);

  const loadSurveys = async () => {
    try {
      setLoading(true);
      const response = await reportService.getAvailableSurveys();
      setSurveys(response.surveys || []);
    } catch (error) {
      console.error('Error loading surveys:', error);
      toast.error('Failed to load available surveys');
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    if (!selectedSurvey) {
      toast.error('Please select a survey');
      return;
    }

    try {
      setLoading(true);
      
      if (reportType === 'summary') {
        const response = await reportService.getSummaryReport(selectedSurvey, filters);
        setSummaryReport(response);
        setDetailedReport(null);
      } else {
        const response = await reportService.getDetailedReport(selectedSurvey, filters);
        setDetailedReport(response);
        setSummaryReport(null);
      }
      
      toast.success('Report generated successfully');
    } catch (error) {
      console.error('Error generating report:', error);
      toast.error('Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const downloadCSV = async () => {
    if (!selectedSurvey) {
      toast.error('Please select a survey');
      return;
    }

    try {
      setLoading(true);
      const response = await reportService.downloadDetailedReportCSV(selectedSurvey, filters);

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `survey_${selectedSurvey}_detailed_report.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('CSV report downloaded successfully');
    } catch (error) {
      console.error('Error downloading CSV:', error);
      toast.error('Failed to download CSV report');
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = async () => {
    if (!selectedSurvey) {
      toast.error('Please select a survey');
      return;
    }

    try {
      setLoading(true);
      const response = await reportService.downloadSummaryReportPDF(selectedSurvey, filters);

      // For now, show a message since PDF generation is not implemented
      toast.info('PDF generation is not yet implemented. Use the summary view for now.');
    } catch (error) {
      console.error('Error downloading PDF:', error);
      toast.error('Failed to download PDF report');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'high':
      case 'critical':
        return 'text-red-600 bg-red-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'low':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Report Builder</h1>
        <p className="text-gray-600">
          Generate comprehensive reports for your surveys including summary statistics and detailed respondent data.
        </p>
      </div>

      {/* Report Configuration */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <FileText className="w-5 h-5 mr-2" />
          Report Configuration
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {/* Survey Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Survey
            </label>
            <select
              value={selectedSurvey}
              onChange={(e) => setSelectedSurvey(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            >
              <option value="">Choose a survey...</option>
              {surveys.map((survey) => (
                <option key={survey.survey_id} value={survey.survey_id}>
                  {survey.survey_id} ({survey.session_count} sessions)
                </option>
              ))}
            </select>
          </div>

          {/* Report Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Report Type
            </label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            >
              <option value="summary">Summary Report</option>
              <option value="detailed">Detailed Report</option>
            </select>
          </div>

          {/* Include Inactive */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="includeInactive"
              checked={filters.includeInactive}
              onChange={(e) => setFilters({...filters, includeInactive: e.target.checked})}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="includeInactive" className="ml-2 block text-sm text-gray-700">
              Include Inactive Sessions
            </label>
          </div>

          {/* Generate Button */}
          <div className="flex items-end">
            <button
              onClick={generateReport}
              disabled={loading || !selectedSurvey}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <BarChart3 className="w-4 h-4 mr-2" />
              )}
              Generate Report
            </button>
          </div>
        </div>

        {/* Date Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date From
            </label>
            <input
              type="datetime-local"
              value={filters.dateFrom}
              onChange={(e) => setFilters({...filters, dateFrom: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date To
            </label>
            <input
              type="datetime-local"
              value={filters.dateTo}
              onChange={(e) => setFilters({...filters, dateTo: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Summary Report */}
      {summaryReport && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              Summary Report
            </h2>
            <button
              onClick={downloadPDF}
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 flex items-center"
            >
              <Download className="w-4 h-4 mr-2" />
              Download PDF
            </button>
          </div>

          {/* Summary Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center">
                <Users className="w-8 h-8 text-blue-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-blue-600">Total Respondents</p>
                  <p className="text-2xl font-bold text-blue-900">{summaryReport.total_respondents}</p>
                </div>
              </div>
            </div>

            <div className="bg-red-50 p-4 rounded-lg">
              <div className="flex items-center">
                <Bot className="w-8 h-8 text-red-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-red-600">Bot Detections</p>
                  <p className="text-2xl font-bold text-red-900">{summaryReport.bot_detections}</p>
                </div>
              </div>
            </div>

            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center">
                <User className="w-8 h-8 text-green-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-green-600">Human Respondents</p>
                  <p className="text-2xl font-bold text-green-900">{summaryReport.human_respondents}</p>
                </div>
              </div>
            </div>

            <div className="bg-yellow-50 p-4 rounded-lg">
              <div className="flex items-center">
                <AlertTriangle className="w-8 h-8 text-yellow-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-yellow-600">Bot Detection Rate</p>
                  <p className="text-2xl font-bold text-yellow-900">{summaryReport.bot_detection_rate.toFixed(1)}%</p>
                </div>
              </div>
            </div>
          </div>

          {/* Additional Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Activity Distribution</h3>
              <div className="space-y-2">
                {Object.entries(summaryReport.activity_distribution).map(([activity, count]) => (
                  <div key={activity} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <span className="font-medium capitalize">{activity.replace('_', ' ')}</span>
                    <span className="text-blue-600 font-semibold">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Risk Level Distribution</h3>
              <div className="space-y-2">
                {Object.entries(summaryReport.risk_distribution).map(([risk, count]) => (
                  <div key={risk} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(risk)}`}>
                      {risk.toUpperCase()}
                    </span>
                    <span className="text-blue-600 font-semibold">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Text Quality Analysis Section */}
          {summaryReport.text_quality_summary && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <MessageSquare className="w-5 h-5 mr-2 text-blue-600" />
                Text Quality Analysis
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                <div className="bg-blue-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-blue-900">
                    {summaryReport.text_quality_summary.total_responses}
                  </div>
                  <div className="text-sm font-medium text-blue-600">Total Text Responses</div>
                </div>
                
                <div className="bg-green-50 p-4 rounded-lg text-center">
                  <div className={`text-2xl font-bold ${
                    summaryReport.text_quality_summary.avg_quality_score >= 70 ? 'text-green-600' :
                    summaryReport.text_quality_summary.avg_quality_score >= 50 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {summaryReport.text_quality_summary.avg_quality_score?.toFixed(1) || 'N/A'}
                  </div>
                  <div className="text-sm font-medium text-green-600">Avg Quality Score</div>
                </div>
                
                <div className="bg-red-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-red-900">
                    {summaryReport.text_quality_summary.flagged_count}
                  </div>
                  <div className="text-sm font-medium text-red-600">Flagged Responses</div>
                </div>
                
                <div className="bg-yellow-50 p-4 rounded-lg text-center">
                  <div className={`text-2xl font-bold ${
                    summaryReport.text_quality_summary.flagged_percentage > 30 ? 'text-red-600' :
                    summaryReport.text_quality_summary.flagged_percentage > 15 ? 'text-yellow-600' : 'text-green-600'
                  }`}>
                    {summaryReport.text_quality_summary.flagged_percentage?.toFixed(1) || '0.0'}%
                  </div>
                  <div className="text-sm font-medium text-yellow-600">Flagged Rate</div>
                </div>
              </div>

              {/* Quality Distribution Chart */}
              {summaryReport.text_quality_summary.quality_distribution && (
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-3">Quality Score Distribution</h4>
                  <div className="flex items-end space-x-1 h-16 bg-gray-50 p-4 rounded-lg">
                    {Object.entries(summaryReport.text_quality_summary.quality_distribution).map(([bucket, count]) => {
                      const maxCount = Math.max(...Object.values(summaryReport.text_quality_summary.quality_distribution));
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
            </div>
          )}

          {/* Fraud & Duplicate Detection Section */}
          {summaryReport.fraud_summary && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <ShieldAlert className="w-5 h-5 mr-2 text-amber-600" />
                Fraud & Duplicate Detection
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <div className="bg-amber-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-amber-900">
                    {summaryReport.fraud_summary.duplicate_sessions ?? 0}
                  </div>
                  <div className="text-sm font-medium text-amber-600">Duplicate Sessions</div>
                </div>
                <div className="bg-red-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-red-900">
                    {summaryReport.fraud_summary.high_risk_sessions ?? 0}
                  </div>
                  <div className="text-sm font-medium text-red-600">High Risk Sessions</div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {summaryReport.fraud_summary.average_fraud_score != null
                      ? (summaryReport.fraud_summary.average_fraud_score * 100).toFixed(1)
                      : 'N/A'}%
                  </div>
                  <div className="text-sm font-medium text-gray-600">Avg Fraud Score</div>
                </div>
                <div className="bg-amber-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-amber-900">
                    {(summaryReport.fraud_summary.duplicate_rate ?? 0).toFixed(1)}%
                  </div>
                  <div className="text-sm font-medium text-amber-600">Duplicate Rate</div>
                </div>
              </div>
              {summaryReport.fraud_summary.fraud_methods && (
                <div>
                  <h4 className="text-md font-medium text-gray-900 mb-3">Fraud Method Breakdown</h4>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(summaryReport.fraud_summary.fraud_methods).map(([method, count]) => (
                      <span
                        key={method}
                        className="px-3 py-1 bg-gray-100 rounded-full text-sm"
                        title={method}
                      >
                        {method.replace(/_/g, ' ')}: <strong>{count}</strong>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Grid Analysis Section */}
          {summaryReport.grid_analysis_summary && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <LayoutGrid className="w-5 h-5 mr-2 text-indigo-600" />
                Grid / Matrix Analysis
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <div className="bg-indigo-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-indigo-900">
                    {summaryReport.grid_analysis_summary.total_responses ?? 0}
                  </div>
                  <div className="text-sm font-medium text-indigo-600">Total Grid Responses</div>
                </div>
                <div className="bg-amber-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-amber-900">
                    {summaryReport.grid_analysis_summary.straight_lined_count ?? 0}
                  </div>
                  <div className="text-sm font-medium text-amber-600">Straight-Lined</div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-gray-900">
                    {(summaryReport.grid_analysis_summary.straight_lined_percentage ?? 0).toFixed(1)}%
                  </div>
                  <div className="text-sm font-medium text-gray-600">Straight-Line Rate</div>
                </div>
                <div className="bg-indigo-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-indigo-900">
                    {(summaryReport.grid_analysis_summary.avg_variance_score ?? 0).toFixed(2)}
                  </div>
                  <div className="text-sm font-medium text-indigo-600">Avg Variance Score</div>
                </div>
              </div>
            </div>
          )}

          {/* Timing Analysis Section */}
          {summaryReport.timing_analysis_summary && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Clock className="w-5 h-5 mr-2 text-teal-600" />
                Timing Analysis
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <div className="bg-teal-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-teal-900">
                    {summaryReport.timing_analysis_summary.total_analyses ?? 0}
                  </div>
                  <div className="text-sm font-medium text-teal-600">Total Timing Analyses</div>
                </div>
                <div className="bg-amber-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-amber-900">
                    {summaryReport.timing_analysis_summary.speeders_count ?? 0}
                  </div>
                  <div className="text-sm font-medium text-amber-600">Speeders</div>
                </div>
                <div className="bg-amber-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-amber-900">
                    {summaryReport.timing_analysis_summary.flatliners_count ?? 0}
                  </div>
                  <div className="text-sm font-medium text-amber-600">Flatliners</div>
                </div>
                <div className="bg-red-50 p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-red-900">
                    {summaryReport.timing_analysis_summary.anomalies_count ?? 0}
                  </div>
                  <div className="text-sm font-medium text-red-600">Timing Anomalies</div>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="text-sm text-gray-600">
                  Speeder rate: <strong>{(summaryReport.timing_analysis_summary.speeders_percentage ?? 0).toFixed(1)}%</strong>
                </div>
                <div className="text-sm text-gray-600">
                  Flatliner rate: <strong>{(summaryReport.timing_analysis_summary.flatliners_percentage ?? 0).toFixed(1)}%</strong>
                </div>
              </div>
            </div>
          )}

          {/* Date Range */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
              <Calendar className="w-5 h-5 mr-2" />
              Report Period
            </h3>
            <p className="text-gray-600">
              From: {formatDate(summaryReport.date_range.from)} - To: {formatDate(summaryReport.date_range.to)}
            </p>
            {summaryReport.average_session_duration && (
              <p className="text-gray-600 mt-1">
                Average Session Duration: {summaryReport.average_session_duration.toFixed(2)} minutes
              </p>
            )}
            {summaryReport.average_events_per_session && (
              <p className="text-gray-600">
                Average Events per Session: {summaryReport.average_events_per_session.toFixed(1)}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Detailed Report */}
      {detailedReport && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center">
              <FileText className="w-5 h-5 mr-2" />
              Detailed Report
            </h2>
            <button
              onClick={downloadCSV}
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 flex items-center"
            >
              <Download className="w-4 h-4 mr-2" />
              Download CSV
            </button>
          </div>

          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg text-center">
              <p className="text-sm font-medium text-blue-600">Total Respondents</p>
              <p className="text-2xl font-bold text-blue-900">{detailedReport.total_respondents}</p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg text-center">
              <p className="text-sm font-medium text-red-600">Bot Detections</p>
              <p className="text-2xl font-bold text-red-900">{detailedReport.summary_stats.bot_detections}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg text-center">
              <p className="text-sm font-medium text-green-600">Human Respondents</p>
              <p className="text-2xl font-bold text-green-900">{detailedReport.summary_stats.human_respondents}</p>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg text-center">
              <p className="text-sm font-medium text-yellow-600">Bot Rate</p>
              <p className="text-2xl font-bold text-yellow-900">{detailedReport.summary_stats.bot_detection_rate.toFixed(1)}%</p>
            </div>
          </div>

          {/* Respondents Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Respondent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Confidence
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Events
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Text Quality
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fraud
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Grid
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timing
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {detailedReport.respondents.map((respondent) => (
                  <tr key={respondent.session_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => setSelectedRespondent(respondent)}
                        className="text-left w-full rounded hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 cursor-pointer"
                        aria-label={`View details for respondent ${respondent.respondent_id || respondent.session_id}`}
                      >
                        <div className="text-sm font-medium text-gray-900">
                          {respondent.respondent_id || 'Anonymous'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {respondent.session_id.substring(0, 8)}...
                        </div>
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {respondent.is_bot ? (
                          <Bot className="w-4 h-4 text-red-500 mr-2" />
                        ) : (
                          <User className="w-4 h-4 text-green-500 mr-2" />
                        )}
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(respondent.risk_level)}`}>
                          {respondent.is_bot ? 'BOT' : 'HUMAN'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {(respondent.confidence_score * 100).toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {respondent.total_events}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {respondent.session_duration_minutes.toFixed(1)}m
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {respondent.text_response_count ? (
                        <div className="flex items-center space-x-2">
                          <div className={`text-sm font-medium ${
                            respondent.avg_text_quality_score >= 70 ? 'text-green-600' :
                            respondent.avg_text_quality_score >= 50 ? 'text-yellow-600' : 'text-red-600'
                          }`}>
                            {respondent.avg_text_quality_score?.toFixed(1) || 'N/A'}
                          </div>
                          {respondent.flagged_text_responses > 0 && (
                            <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded">
                              {respondent.flagged_text_responses} flagged
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400 text-sm">No text data</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="space-y-0.5">
                        {respondent.fraud_score != null && (
                          <div>Score: {(respondent.fraud_score * 100).toFixed(0)}%</div>
                        )}
                        {respondent.is_duplicate === true && (
                          <span className="px-2 py-0.5 text-xs bg-amber-100 text-amber-800 rounded">Duplicate</span>
                        )}
                        {respondent.fraud_risk_level && (
                          <div className="text-xs text-gray-500">{respondent.fraud_risk_level}</div>
                        )}
                        {respondent.fraud_score == null && respondent.is_duplicate != true && !respondent.fraud_risk_level && (
                          <span className="text-gray-400">—</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="space-y-0.5">
                        {respondent.grid_straight_lining === true && (
                          <span className="px-2 py-0.5 text-xs bg-amber-100 text-amber-800 rounded">Straight-line</span>
                        )}
                        {respondent.grid_variance_score != null && (
                          <div className="text-xs">Variance: {respondent.grid_variance_score.toFixed(2)}</div>
                        )}
                        {respondent.grid_straight_lining !== true && respondent.grid_variance_score == null && (
                          <span className="text-gray-400">—</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      <div className="flex flex-wrap gap-1">
                        {respondent.timing_speeder && (
                          <span className="px-2 py-0.5 text-xs bg-amber-100 text-amber-800 rounded">Speeder</span>
                        )}
                        {respondent.timing_flatliner && (
                          <span className="px-2 py-0.5 text-xs bg-gray-200 text-gray-700 rounded">Flatliner</span>
                        )}
                        {respondent.timing_anomaly_count > 0 && (
                          <span className="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded">
                            {respondent.timing_anomaly_count} anomalies
                          </span>
                        )}
                        {!respondent.timing_speeder && !respondent.timing_flatliner && (respondent.timing_anomaly_count == null || respondent.timing_anomaly_count === 0) && (
                          <span className="text-gray-400">—</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(respondent.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Respondent Detail Modal */}
      {selectedRespondent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900">
                Respondent details – {selectedRespondent.respondent_id || 'Anonymous'}
              </h3>
              <button
                type="button"
                onClick={() => setSelectedRespondent(null)}
                className="text-gray-400 hover:text-gray-600 focus:outline-none"
                aria-label="Close"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6 space-y-6">
              {/* Session info */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Session info</h4>
                <div className="bg-gray-50 rounded-lg p-4 grid grid-cols-2 gap-2 text-sm">
                  <div><span className="text-gray-500">Session ID:</span> {selectedRespondent.session_id}</div>
                  <div><span className="text-gray-500">Created:</span> {formatDate(selectedRespondent.created_at)}</div>
                  <div><span className="text-gray-500">Last activity:</span> {formatDate(selectedRespondent.last_activity)}</div>
                  <div><span className="text-gray-500">Duration:</span> {selectedRespondent.session_duration_minutes?.toFixed(1) ?? '—'} min</div>
                  <div><span className="text-gray-500">Total events:</span> {selectedRespondent.total_events}</div>
                  {selectedRespondent.event_breakdown && Object.keys(selectedRespondent.event_breakdown).length > 0 && (
                    <div className="col-span-2"><span className="text-gray-500">Event breakdown:</span> {JSON.stringify(selectedRespondent.event_breakdown)}</div>
                  )}
                </div>
              </div>

              {/* Bot detection */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Bot detection</h4>
                <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">Status:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRiskLevelColor(selectedRespondent.risk_level)}`}>
                      {selectedRespondent.is_bot ? 'BOT' : 'HUMAN'}
                    </span>
                  </div>
                  <div><span className="text-gray-500">Confidence:</span> {(selectedRespondent.confidence_score * 100).toFixed(1)}%</div>
                  <div><span className="text-gray-500">Risk level:</span> {selectedRespondent.risk_level}</div>
                  {selectedRespondent.method_scores && Object.keys(selectedRespondent.method_scores).length > 0 && (
                    <div><span className="text-gray-500">Method scores:</span> <pre className="inline text-xs">{JSON.stringify(selectedRespondent.method_scores)}</pre></div>
                  )}
                  {selectedRespondent.analysis_summary && <div><span className="text-gray-500">Analysis:</span> {selectedRespondent.analysis_summary}</div>}
                  {selectedRespondent.bot_explanation && <div><span className="text-gray-500">Why:</span> {selectedRespondent.bot_explanation}</div>}
                </div>
              </div>

              {/* Text quality & responses of interest */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Text quality</h4>
                <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
                  <div><span className="text-gray-500">Text responses:</span> {selectedRespondent.text_response_count ?? '—'}</div>
                  <div><span className="text-gray-500">Avg quality score:</span> {selectedRespondent.avg_text_quality_score != null ? selectedRespondent.avg_text_quality_score.toFixed(1) : '—'}</div>
                  <div><span className="text-gray-500">Flagged:</span> {selectedRespondent.flagged_text_responses ?? '—'}</div>
                </div>
                {selectedRespondent.text_responses_of_interest && selectedRespondent.text_responses_of_interest.length > 0 && (
                  <div className="mt-2">
                    <h5 className="text-xs font-semibold text-gray-600 mb-2">Responses of interest</h5>
                    <div className="space-y-3">
                      {selectedRespondent.text_responses_of_interest.map((r, idx) => (
                        <div key={idx} className="border border-gray-200 rounded p-3 text-sm bg-white">
                          {r.question_preview && <div className="text-gray-600 mb-1"><span className="font-medium">Q:</span> {r.question_preview}</div>}
                          <div className="mb-1"><span className="font-medium">Response:</span> {r.response_preview}</div>
                          <div className="flex flex-wrap gap-2 text-xs">
                            <span>Score: {r.quality_score != null ? r.quality_score.toFixed(1) : 'N/A'}</span>
                            {r.is_flagged && <span className="px-1.5 py-0.5 bg-red-100 text-red-700 rounded">Flagged</span>}
                            {r.flag_reasons && Object.keys(r.flag_reasons).length > 0 && (
                              <span className="text-amber-700">Reasons: {Object.keys(r.flag_reasons).join(', ')}</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Fraud */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Fraud</h4>
                <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
                  <div><span className="text-gray-500">Score:</span> {selectedRespondent.fraud_score != null ? (selectedRespondent.fraud_score * 100).toFixed(0) + '%' : '—'}</div>
                  <div><span className="text-gray-500">Duplicate:</span> {selectedRespondent.is_duplicate === true ? 'Yes' : selectedRespondent.is_duplicate === false ? 'No' : '—'}</div>
                  {selectedRespondent.fraud_risk_level && <div><span className="text-gray-500">Risk level:</span> {selectedRespondent.fraud_risk_level}</div>}
                  {selectedRespondent.fraud_flag_reasons && Object.keys(selectedRespondent.fraud_flag_reasons).length > 0 && (
                    <div><span className="text-gray-500">Flag reasons:</span> <pre className="text-xs mt-1">{JSON.stringify(selectedRespondent.fraud_flag_reasons, null, 2)}</pre></div>
                  )}
                  {selectedRespondent.fraud_velocity_summary && (selectedRespondent.fraud_velocity_summary.responses_per_hour != null || selectedRespondent.fraud_velocity_summary.velocity_risk_score != null) && (
                    <div><span className="text-gray-500">Velocity:</span> responses/hr={selectedRespondent.fraud_velocity_summary.responses_per_hour ?? '—'}, risk={selectedRespondent.fraud_velocity_summary.velocity_risk_score != null ? selectedRespondent.fraud_velocity_summary.velocity_risk_score.toFixed(2) : '—'}</div>
                  )}
                </div>
              </div>

              {/* Grid */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Grid</h4>
                <div className="bg-gray-50 rounded-lg p-4 text-sm">
                  <div><span className="text-gray-500">Straight-lining:</span> {selectedRespondent.grid_straight_lining === true ? 'Yes' : selectedRespondent.grid_straight_lining === false ? 'No' : '—'}</div>
                  {selectedRespondent.grid_variance_score != null && <div><span className="text-gray-500">Variance score:</span> {selectedRespondent.grid_variance_score.toFixed(2)}</div>}
                  {selectedRespondent.grid_explanation && <div className="mt-2"><span className="text-gray-500">Why:</span> {selectedRespondent.grid_explanation}</div>}
                </div>
              </div>

              {/* Timing */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Timing</h4>
                <div className="bg-gray-50 rounded-lg p-4 text-sm">
                  <div><span className="text-gray-500">Speeder:</span> {selectedRespondent.timing_speeder === true ? 'Yes' : selectedRespondent.timing_speeder === false ? 'No' : '—'}</div>
                  <div><span className="text-gray-500">Flatliner:</span> {selectedRespondent.timing_flatliner === true ? 'Yes' : selectedRespondent.timing_flatliner === false ? 'No' : '—'}</div>
                  <div><span className="text-gray-500">Anomalies:</span> {selectedRespondent.timing_anomaly_count ?? '—'}</div>
                  {selectedRespondent.timing_explanation && <div className="mt-2"><span className="text-gray-500">Why:</span> {selectedRespondent.timing_explanation}</div>}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* No Report State */}
      {!summaryReport && !detailedReport && !loading && (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Report Generated</h3>
          <p className="text-gray-600 mb-6">
            Select a survey and click "Generate Report" to view survey analytics and respondent data.
          </p>
        </div>
      )}
    </div>
  );
};

export default ReportBuilder;
