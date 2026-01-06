import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  FileText, 
  Users, 
  Activity, 
  AlertTriangle, 
  CheckCircle,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Server,
  ChevronRight
} from 'lucide-react';
import { hierarchicalService } from '../services/apiService';
import { toast } from 'react-toastify';
import HierarchicalNavigation from './HierarchicalNavigation';
import HierarchicalFraudWidget from './HierarchicalFraudWidget';

const SurveyDetails = () => {
  const { surveyId } = useParams();
  const [surveyData, setSurveyData] = useState(null);
  const [platforms, setPlatforms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (surveyId) {
      loadSurveyData();
      loadPlatforms();
    }
  }, [surveyId]);

  const loadSurveyData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await hierarchicalService.getSurveyDetails(surveyId);
      setSurveyData(data);
    } catch (err) {
      setError('Failed to load survey details');
      console.error('Error loading survey details:', err);
      toast.error('Failed to load survey details');
    } finally {
      setLoading(false);
    }
  };

  const loadPlatforms = async () => {
    try {
      const response = await hierarchicalService.getPlatforms(surveyId);
      setPlatforms(response.platforms || []);
    } catch (err) {
      console.error('Error loading platforms:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !surveyData) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error || 'Survey not found'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <HierarchicalNavigation surveyId={surveyId} />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Survey Details</h1>
          <p className="text-gray-600 mt-1">Survey ID: {surveyId}</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Respondents</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {surveyData.total_respondents}
              </p>
            </div>
            <Users className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Sessions</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {surveyData.total_sessions}
              </p>
            </div>
            <Activity className="w-8 h-8 text-green-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Bot Rate</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {surveyData.bot_detection?.bot_rate?.toFixed(1)}%
              </p>
            </div>
            {surveyData.bot_detection?.bot_rate >= 20 ? (
              <AlertTriangle className="w-8 h-8 text-red-600" />
            ) : (
              <CheckCircle className="w-8 h-8 text-green-600" />
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Quality Score</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {surveyData.text_quality?.avg_quality_score?.toFixed(1) || 'N/A'}
              </p>
            </div>
            <BarChart3 className="w-8 h-8 text-purple-600" />
          </div>
        </div>
      </div>

      {/* Platform Distribution */}
      {platforms.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <Server className="w-5 h-5 mr-2" />
            Platforms
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {platforms.map((platform) => (
              <Link
                key={platform.platform_id}
                to={`/surveys/${surveyId}/platforms/${platform.platform_id}`}
                className="border border-gray-200 rounded-lg p-4 hover:border-blue-500 hover:shadow-md transition-all"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{platform.platform_id}</p>
                    <p className="text-sm text-gray-600 mt-1">
                      {platform.respondent_count} respondents • {platform.session_count} sessions
                    </p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bot Detection Metrics */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Bot Detection Metrics</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Total Detections</span>
              <span className="font-medium">{surveyData.bot_detection?.total_detections || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Bot Count</span>
              <span className="font-medium text-red-600">
                {surveyData.bot_detection?.bot_count || 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Human Count</span>
              <span className="font-medium text-green-600">
                {surveyData.bot_detection?.human_count || 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Average Confidence</span>
              <span className="font-medium">
                {surveyData.bot_detection?.avg_confidence?.toFixed(3) || 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Text Quality Metrics */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Text Quality Metrics</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Total Responses</span>
              <span className="font-medium">{surveyData.text_quality?.total_responses || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Average Quality Score</span>
              <span className="font-medium">
                {surveyData.text_quality?.avg_quality_score?.toFixed(2) || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Flagged Count</span>
              <span className="font-medium text-yellow-600">
                {surveyData.text_quality?.flagged_count || 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Flagged Percentage</span>
              <span className="font-medium">
                {surveyData.text_quality?.flagged_percentage?.toFixed(2) || 0}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Distribution */}
      {surveyData.risk_distribution && Object.keys(surveyData.risk_distribution).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Risk Level Distribution</h2>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(surveyData.risk_distribution).map(([level, count]) => (
              <div key={level} className="text-center p-4 border border-gray-200 rounded-lg">
                <p className="text-2xl font-bold text-gray-900">{count}</p>
                <p className="text-sm text-gray-600 capitalize mt-1">{level}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fraud Detection Summary */}
      <HierarchicalFraudWidget surveyId={surveyId} />
    </div>
  );
};

export default SurveyDetails;

