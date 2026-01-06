import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  User, 
  Activity, 
  AlertTriangle, 
  CheckCircle,
  BarChart3,
  Clock,
  ChevronRight
} from 'lucide-react';
import { hierarchicalService } from '../services/apiService';
import { toast } from 'react-toastify';
import HierarchicalNavigation from './HierarchicalNavigation';
import HierarchicalFraudWidget from './HierarchicalFraudWidget';

const RespondentDetails = () => {
  const { surveyId, platformId, respondentId } = useParams();
  const [respondentData, setRespondentData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (surveyId && platformId && respondentId) {
      loadRespondentData();
    }
  }, [surveyId, platformId, respondentId]);

  const loadRespondentData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await hierarchicalService.getRespondentDetails(surveyId, platformId, respondentId);
      setRespondentData(data);
    } catch (err) {
      setError('Failed to load respondent details');
      console.error('Error loading respondent details:', err);
      toast.error('Failed to load respondent details');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !respondentData) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error || 'Respondent not found'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <HierarchicalNavigation 
        surveyId={surveyId} 
        platformId={platformId}
        respondentId={respondentId}
      />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Respondent Details</h1>
          <p className="text-gray-600 mt-1">Respondent ID: {respondentId}</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Sessions</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {respondentData.total_sessions}
              </p>
            </div>
            <Activity className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Bot Rate</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {respondentData.bot_detection?.bot_rate?.toFixed(1)}%
              </p>
            </div>
            {respondentData.bot_detection?.bot_rate >= 20 ? (
              <AlertTriangle className="w-8 h-8 text-red-600" />
            ) : (
              <CheckCircle className="w-8 h-8 text-green-600" />
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Confidence</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {respondentData.bot_detection?.avg_confidence?.toFixed(3) || 'N/A'}
              </p>
            </div>
            <BarChart3 className="w-8 h-8 text-purple-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Overall Risk</p>
              <p className="text-2xl font-bold text-gray-900 mt-1 capitalize">
                {respondentData.bot_detection?.overall_risk || 'N/A'}
              </p>
            </div>
            <AlertTriangle className="w-8 h-8 text-yellow-600" />
          </div>
        </div>
      </div>

      {/* Sessions List */}
      {respondentData.sessions && respondentData.sessions.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <Activity className="w-5 h-5 mr-2" />
            All Sessions ({respondentData.sessions.length})
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Session ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Created At
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Events
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Detection
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {respondentData.sessions.map((session) => (
                  <tr key={session.session_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                      {session.session_id.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(session.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {session.event_count || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {session.latest_detection ? (
                        <div className="flex items-center">
                          {session.latest_detection.is_bot ? (
                            <AlertTriangle className="w-4 h-4 text-red-600 mr-2" />
                          ) : (
                            <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                          )}
                          <span className="text-sm">
                            {session.latest_detection.confidence_score?.toFixed(3) || 'N/A'}
                          </span>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400">No detection</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <Link
                        to={`/surveys/${surveyId}/platforms/${platformId}/respondents/${respondentId}/sessions/${session.session_id}`}
                        className="text-blue-600 hover:text-blue-900 flex items-center"
                      >
                        View Details
                        <ChevronRight className="w-4 h-4 ml-1" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Session Timeline */}
      {respondentData.session_timeline && respondentData.session_timeline.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2" />
            Session Timeline
          </h2>
          <div className="space-y-2">
            {respondentData.session_timeline.map((session, index) => (
              <div
                key={session.session_id}
                className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
              >
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-blue-600">{index + 1}</span>
                </div>
                <div className="ml-4 flex-1">
                  <p className="text-sm font-medium text-gray-900">
                    Session {session.session_id.substring(0, 8)}...
                  </p>
                  <p className="text-xs text-gray-500">{formatDate(session.created_at)}</p>
                </div>
                <div className="flex items-center space-x-2">
                  {session.is_active && (
                    <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
                      Active
                    </span>
                  )}
                  {session.is_completed && (
                    <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                      Completed
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Fraud Detection Summary */}
      <HierarchicalFraudWidget 
        surveyId={surveyId} 
        platformId={platformId} 
        respondentId={respondentId} 
      />
    </div>
  );
};

export default RespondentDetails;

