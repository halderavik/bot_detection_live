import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  Server, 
  Users, 
  Activity, 
  AlertTriangle, 
  CheckCircle,
  BarChart3,
  ChevronRight
} from 'lucide-react';
import { hierarchicalService } from '../services/apiService';
import { toast } from 'react-toastify';
import HierarchicalNavigation from './HierarchicalNavigation';

const PlatformDetails = () => {
  const { surveyId, platformId } = useParams();
  const [platformData, setPlatformData] = useState(null);
  const [respondents, setRespondents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (surveyId && platformId) {
      loadPlatformData();
      loadRespondents();
    }
  }, [surveyId, platformId]);

  const loadPlatformData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await hierarchicalService.getPlatformDetails(surveyId, platformId);
      setPlatformData(data);
    } catch (err) {
      setError('Failed to load platform details');
      console.error('Error loading platform details:', err);
      toast.error('Failed to load platform details');
    } finally {
      setLoading(false);
    }
  };

  const loadRespondents = async () => {
    try {
      const response = await hierarchicalService.getRespondents(surveyId, platformId, { limit: 50 });
      setRespondents(response.respondents || []);
    } catch (err) {
      console.error('Error loading respondents:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !platformData) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error || 'Platform not found'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <HierarchicalNavigation 
        surveyId={surveyId} 
        platformId={platformId}
      />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Platform Details</h1>
          <p className="text-gray-600 mt-1">Platform ID: {platformId}</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Respondents</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {platformData.total_respondents}
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
                {platformData.total_sessions}
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
                {platformData.bot_detection?.bot_rate?.toFixed(1)}%
              </p>
            </div>
            {platformData.bot_detection?.bot_rate >= 20 ? (
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
                {platformData.text_quality?.avg_quality_score?.toFixed(1) || 'N/A'}
              </p>
            </div>
            <BarChart3 className="w-8 h-8 text-purple-600" />
          </div>
        </div>
      </div>

      {/* Respondents List */}
      {respondents.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
            <Users className="w-5 h-5 mr-2" />
            Respondents
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Respondent ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Sessions
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Bot Count
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {respondents.map((respondent) => (
                  <tr key={respondent.respondent_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {respondent.respondent_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {respondent.session_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {respondent.bot_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <Link
                        to={`/surveys/${surveyId}/platforms/${platformId}/respondents/${respondent.respondent_id}`}
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
    </div>
  );
};

export default PlatformDetails;

