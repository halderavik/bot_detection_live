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
  Clock
} from 'lucide-react';
import { toast } from 'react-toastify';
import { reportService } from '../services/apiService';

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
                    Created
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {detailedReport.respondents.map((respondent) => (
                  <tr key={respondent.session_id} className="hover:bg-gray-50">
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
