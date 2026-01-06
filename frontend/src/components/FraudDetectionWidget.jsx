import React, { useEffect, useState } from 'react';
import { fraudService } from '../services/apiService';

function FraudDetectionWidget({ surveyId = null, days = 7 }) {
  const [summary, setSummary] = useState(null);
  const [duplicates, setDuplicates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, [surveyId, days]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [summaryData, duplicatesData] = await Promise.all([
        fraudService.getFraudDashboardSummary(surveyId, days),
        fraudService.getDuplicateSessions(surveyId, 10)
      ]);
      setSummary(summaryData);
      setDuplicates(duplicatesData.sessions || []);
      setError(null);
    } catch (err) {
      console.error('Error loading fraud data:', err);
      setError('Failed to load fraud detection data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Fraud Detection Summary</h3>
        <div>Loading fraud detection data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Fraud Detection Summary</h3>
        <div className="text-red-600">{error}</div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Fraud Detection Summary</h3>
        <div>No fraud data available</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <h4 className="text-sm font-medium text-gray-600 mb-1">Total Analyzed</h4>
          <p className="text-2xl font-bold">{summary.total_sessions_analyzed || 0}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-4">
          <h4 className="text-sm font-medium text-gray-600 mb-1">Duplicates</h4>
          <p className="text-2xl font-bold text-orange-600">{summary.duplicate_sessions || 0}</p>
          <p className="text-xs text-gray-500 mt-1">
            {summary.duplicate_rate ? `${summary.duplicate_rate.toFixed(1)}%` : '0%'} rate
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-4">
          <h4 className="text-sm font-medium text-gray-600 mb-1">High Risk</h4>
          <p className="text-2xl font-bold text-red-600">{summary.high_risk_sessions || 0}</p>
          <p className="text-xs text-gray-500 mt-1">
            {summary.high_risk_rate ? `${summary.high_risk_rate.toFixed(1)}%` : '0%'} rate
          </p>
        </div>
        
        <div className="bg-white rounded-lg shadow p-4">
          <h4 className="text-sm font-medium text-gray-600 mb-1">Avg Fraud Score</h4>
          <p className="text-2xl font-bold">
            {summary.average_fraud_score ? summary.average_fraud_score.toFixed(2) : '0.00'}
          </p>
        </div>
      </div>

      {/* Top Suspicious IPs */}
      {summary.top_suspicious_ips && summary.top_suspicious_ips.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Top Suspicious IP Addresses</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IP Address
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Sessions
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk Score
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {summary.top_suspicious_ips.map((ip, index) => (
                  <tr key={index}>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-mono">
                      {ip.ip}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      {ip.count}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        ip.risk_score >= 0.8 ? 'bg-red-100 text-red-800' :
                        ip.risk_score >= 0.6 ? 'bg-orange-100 text-orange-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {(ip.risk_score * 100).toFixed(0)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Duplicate Sessions */}
      {duplicates.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Duplicate Sessions</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Session ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Survey ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IP Address
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fraud Score
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {duplicates.map((session) => (
                  <tr key={session.session_id}>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-mono">
                      {session.session_id.substring(0, 8)}...
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      {session.survey_id || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-mono">
                      {session.ip_address || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      {session.fraud_score !== null ? (
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          session.fraud_score >= 0.8 ? 'bg-red-100 text-red-800' :
                          session.fraud_score >= 0.6 ? 'bg-orange-100 text-orange-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {(session.fraud_score * 100).toFixed(0)}%
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      {new Date(session.created_at).toLocaleDateString()}
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
}

export default FraudDetectionWidget;
