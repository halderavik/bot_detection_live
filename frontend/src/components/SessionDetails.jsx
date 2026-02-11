import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { config } from '../config/config';
import { fraudService } from '../services/apiService';
import TextQualityWidget from './TextQualityWidget';
import HierarchicalNavigation from './HierarchicalNavigation';
import HierarchicalFraudWidget from './HierarchicalFraudWidget';
import GridAnalysisWidget from './GridAnalysisWidget';
import TimingAnalysisWidget from './TimingAnalysisWidget';
import PerQuestionTimingTable from './PerQuestionTimingTable';

function formatDate(dateStr) {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString();
}

// Helper to parse PowerShell-style flagged_patterns
function parseFlaggedPattern(str) {
  if (!str || typeof str !== 'string' || !str.startsWith('@{')) return str;
  const obj = {};
  str.slice(2, -1).split(';').forEach(pair => {
    const [k, v] = pair.split('=');
    if (k && v) obj[k.trim()] = v.trim();
  });
  return obj;
}

function SessionDetails({ sessionId: propSessionId }) {
  // Support both prop-based and route-based sessionId
  const { surveyId, platformId, respondentId, sessionId: routeSessionId } = useParams();
  const sessionId = propSessionId || routeSessionId;
  
  // Determine if we're in hierarchical context
  const isHierarchical = !!(surveyId && platformId && respondentId && routeSessionId);
  
  const [details, setDetails] = useState(null);
  const [fraudIndicators, setFraudIndicators] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSessionData();
  }, [sessionId]);

  const loadSessionData = async () => {
    try {
      setLoading(true);
      const [sessionData, fraudData] = await Promise.all([
        fetch(config.dashboard.sessionDetails(sessionId)).then(res => res.json()),
        fraudService.getFraudIndicators(sessionId).catch(() => null)
      ]);
      setDetails(sessionData);
      setFraudIndicators(fraudData);
      setError(null);
    } catch (err) {
      console.error('Error loading session data:', err);
      setError('Failed to load session details');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading session details...</div>;
  if (error) return <div className="text-red-600">{error}</div>;
  if (!details) return <div>No details found.</div>;

  const session = details.session || {};
  const behaviorData = details.behavior_data || [];
  const detectionResults = details.detection_results || [];
  const statistics = details.statistics || {};
  
  // Get the latest detection result
  const latestDetection = detectionResults.length > 0 ? detectionResults[0] : {};
  const methodScores = latestDetection.method_scores || {};
  const flaggedPatterns = latestDetection.flagged_patterns || {};

  return (
    <div className="space-y-6">
      {/* Hierarchical Navigation */}
      {isHierarchical && (
        <HierarchicalNavigation 
          surveyId={surveyId}
          platformId={platformId}
          respondentId={respondentId}
          sessionId={routeSessionId}
        />
      )}

      {/* Session Information */}
      <div>
        <h3 className="text-lg font-semibold mb-2">Session Information</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="font-semibold">Session ID:</span> <span className="font-mono text-xs">{session.id}</span></div>
          <div><span className="font-semibold">Created:</span> {formatDate(session.created_at)}</div>
          <div><span className="font-semibold">Last Activity:</span> {formatDate(session.last_activity)}</div>
          <div><span className="font-semibold">Active:</span> {session.is_active ? 'Yes' : 'No'}</div>
          <div><span className="font-semibold">Completed:</span> {session.is_completed ? 'Yes' : 'No'}</div>
          <div><span className="font-semibold">Platform:</span> {session.platform || '-'}</div>
          <div><span className="font-semibold">Survey ID:</span> {session.survey_id || '-'}</div>
          <div><span className="font-semibold">Respondent ID:</span> {session.respondent_id || '-'}</div>
          <div><span className="font-semibold">User Agent:</span> {session.user_agent || '-'}</div>
          <div><span className="font-semibold">IP Address:</span> {session.ip_address || '-'}</div>
          <div><span className="font-semibold">Referrer:</span> {session.referrer || '-'}</div>
        </div>
      </div>

      {/* Statistics */}
      <div>
        <h3 className="text-lg font-semibold mb-2">Statistics</h3>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div><span className="font-semibold">Total Events:</span> {statistics.total_events || 0}</div>
          <div><span className="font-semibold">Total Detections:</span> {statistics.total_detections || 0}</div>
          <div><span className="font-semibold">Session Duration:</span> {statistics.session_duration_minutes ? `${statistics.session_duration_minutes.toFixed(2)} min` : '-'}</div>
        </div>
      </div>

      {/* Detection Results */}
      {detectionResults.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2">Detection Results</h3>
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex flex-wrap gap-4 items-center mb-3">
              {latestDetection.is_bot === true && <span className="bg-red-100 text-red-700 px-3 py-1 rounded font-semibold">BOT DETECTED</span>}
              {latestDetection.is_bot === false && <span className="bg-green-100 text-green-700 px-3 py-1 rounded font-semibold">HUMAN</span>}
              <span className="text-sm"><span className="font-semibold">Confidence:</span> {latestDetection.confidence_score ? `${(latestDetection.confidence_score * 100).toFixed(1)}%` : '-'}</span>
              <span className="text-sm"><span className="font-semibold">Risk Level:</span> {latestDetection.risk_level || '-'}</span>
              <span className="text-sm"><span className="font-semibold">Processing Time:</span> {latestDetection.processing_time_ms ? `${latestDetection.processing_time_ms}ms` : '-'}</span>
              <span className="text-sm"><span className="font-semibold">Analyzed:</span> {formatDate(latestDetection.analyzed_at)}</span>
            </div>
            
            <div className="mb-3">
              <span className="font-semibold">Analysis Summary:</span> {latestDetection.analysis_summary || '-'}
            </div>

            {/* Method Scores */}
            {Object.keys(methodScores).length > 0 && (
              <div className="mb-3">
                <span className="font-semibold">Method Scores:</span>
                <div className="grid grid-cols-2 gap-2 mt-1">
                  {Object.entries(methodScores).map(([method, score]) => (
                    <div key={method} className="text-sm">
                      <span className="font-mono text-xs">{method}:</span> {(score * 100).toFixed(1)}%
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Flagged Patterns */}
            {Object.keys(flaggedPatterns).length > 0 && (
              <div className="mb-3">
                <span className="font-semibold">Flagged Patterns:</span>
                <div className="mt-1">
                  {Object.entries(flaggedPatterns).map(([pattern, value]) => {
                    const parsed = parseFlaggedPattern(value);
                    return (
                      <div key={pattern} className="text-sm mb-1">
                        <span className="font-mono text-xs">{pattern}:</span>
                        {typeof parsed === 'object' ? (
                          <ul className="ml-4 list-disc">
                            {Object.entries(parsed).map(([k, v]) => (
                              <li key={k}><span className="font-mono text-xs">{k}:</span> {v}</li>
                            ))}
                          </ul>
                        ) : (
                          <span> {parsed}</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Behavior Data */}
      <div>
        <h3 className="text-lg font-semibold mb-2">Event Log ({behaviorData.length} events)</h3>
        <div className="overflow-x-auto max-h-64">
          <table className="min-w-full text-xs border border-gray-200 rounded-lg">
            <thead>
              <tr className="bg-gray-100">
                <th className="px-2 py-1">Timestamp</th>
                <th className="px-2 py-1">Event Type</th>
                <th className="px-2 py-1">Element ID</th>
                <th className="px-2 py-1">Element Type</th>
                <th className="px-2 py-1">Page URL</th>
                <th className="px-2 py-1">Screen Size</th>
              </tr>
            </thead>
            <tbody>
              {behaviorData.map((event, index) => (
                <tr key={event.id || index}>
                  <td className="px-2 py-1 font-mono">{formatDate(event.timestamp)}</td>
                  <td className="px-2 py-1">{event.event_type}</td>
                  <td className="px-2 py-1 font-mono text-xs">{event.element_id || '-'}</td>
                  <td className="px-2 py-1">{event.element_type || '-'}</td>
                  <td className="px-2 py-1 text-gray-700 truncate max-w-xs">{event.page_url || '-'}</td>
                  <td className="px-2 py-1">{event.screen_width && event.screen_height ? `${event.screen_width}x${event.screen_height}` : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Fraud Detection - Use hierarchical widget if in hierarchical context, else use flat display */}
      {isHierarchical ? (
        <HierarchicalFraudWidget 
          surveyId={surveyId}
          platformId={platformId}
          respondentId={respondentId}
          sessionId={routeSessionId}
        />
      ) : (
        fraudIndicators && fraudIndicators.fraud_analysis_available && (
          <div>
            <h3 className="text-lg font-semibold mb-2">Fraud Detection Indicators</h3>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex flex-wrap gap-4 items-center mb-3">
                {fraudIndicators.is_duplicate && (
                  <span className="bg-red-100 text-red-700 px-3 py-1 rounded font-semibold">DUPLICATE</span>
                )}
                <span className="text-sm">
                  <span className="font-semibold">Fraud Score:</span>{' '}
                  {fraudIndicators.overall_fraud_score !== null ? (
                    <span className={`font-semibold ${
                      fraudIndicators.overall_fraud_score >= 0.8 ? 'text-red-600' :
                      fraudIndicators.overall_fraud_score >= 0.6 ? 'text-orange-600' :
                      'text-yellow-600'
                    }`}>
                      {(fraudIndicators.overall_fraud_score * 100).toFixed(1)}%
                    </span>
                  ) : '-'}
                </span>
                <span className="text-sm">
                  <span className="font-semibold">Risk Level:</span> {fraudIndicators.risk_level || '-'}
                </span>
              </div>

              {/* IP Analysis */}
              {fraudIndicators.ip_analysis && (
                <div className="mb-3">
                  <span className="font-semibold">IP Address Analysis:</span>
                  <div className="ml-4 text-sm">
                    <div>IP: <span className="font-mono">{fraudIndicators.ip_analysis.ip_address || '-'}</span></div>
                    <div>Usage Count: {fraudIndicators.ip_analysis.usage_count || 0}</div>
                    <div>Sessions Today: {fraudIndicators.ip_analysis.sessions_today || 0}</div>
                    <div>Risk Score: {fraudIndicators.ip_analysis.risk_score !== null ? `${(fraudIndicators.ip_analysis.risk_score * 100).toFixed(1)}%` : '-'}</div>
                    {fraudIndicators.ip_analysis.country_code && (
                      <div>Country: {fraudIndicators.ip_analysis.country_code}</div>
                    )}
                  </div>
                </div>
              )}

              {/* Device Fingerprint */}
              {fraudIndicators.device_fingerprint && (
                <div className="mb-3">
                  <span className="font-semibold">Device Fingerprint:</span>
                  <div className="ml-4 text-sm">
                    <div>Fingerprint: <span className="font-mono text-xs">{fraudIndicators.device_fingerprint.fingerprint?.substring(0, 16) || '-'}...</span></div>
                    <div>Usage Count: {fraudIndicators.device_fingerprint.usage_count || 0}</div>
                    <div>Risk Score: {fraudIndicators.device_fingerprint.risk_score !== null ? `${(fraudIndicators.device_fingerprint.risk_score * 100).toFixed(1)}%` : '-'}</div>
                  </div>
                </div>
              )}

              {/* Duplicate Responses */}
              {fraudIndicators.duplicate_responses && (
                <div className="mb-3">
                  <span className="font-semibold">Duplicate Response Detection:</span>
                  <div className="ml-4 text-sm">
                    <div>Similarity Score: {fraudIndicators.duplicate_responses.similarity_score !== null ? `${(fraudIndicators.duplicate_responses.similarity_score * 100).toFixed(1)}%` : '-'}</div>
                    <div>Duplicate Count: {fraudIndicators.duplicate_responses.duplicate_count || 0}</div>
                  </div>
                </div>
              )}

              {/* Velocity */}
              {fraudIndicators.velocity && (
                <div className="mb-3">
                  <span className="font-semibold">Velocity Analysis:</span>
                  <div className="ml-4 text-sm">
                    <div>Responses per Hour: {fraudIndicators.velocity.responses_per_hour !== null ? fraudIndicators.velocity.responses_per_hour.toFixed(2) : '-'}</div>
                    <div>Risk Score: {fraudIndicators.velocity.risk_score !== null ? `${(fraudIndicators.velocity.risk_score * 100).toFixed(1)}%` : '-'}</div>
                  </div>
                </div>
              )}

              {/* Flag Reasons */}
              {fraudIndicators.flag_reasons && Object.keys(fraudIndicators.flag_reasons).length > 0 && (
                <div className="mb-3">
                  <span className="font-semibold">Flag Reasons:</span>
                  <div className="ml-4 text-sm">
                    {Object.entries(fraudIndicators.flag_reasons).map(([reason, details]) => (
                      <div key={reason} className="mb-1">
                        <span className="font-semibold">{reason}:</span>
                        {typeof details === 'object' ? (
                          <ul className="ml-2 list-disc">
                            {Object.entries(details).map(([k, v]) => (
                              <li key={k}><span className="font-semibold">{k}:</span> {v}</li>
                            ))}
                          </ul>
                        ) : (
                          <span> {details}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )
      )}

      {/* Text Quality Analysis */}
      <div className="mt-6">
        <TextQualityWidget 
          sessionId={sessionId} 
          onDataLoad={(data) => {
            // Optionally update session data with text quality info
            console.log('Text quality data loaded:', data);
          }}
        />
      </div>

      {/* Grid Analysis Summary */}
      {isHierarchical && (
        <div className="mt-6">
          <GridAnalysisWidget 
            surveyId={surveyId}
            platformId={platformId}
            respondentId={respondentId}
            sessionId={routeSessionId}
          />
        </div>
      )}

      {/* Timing Analysis Summary */}
      {isHierarchical && (
        <div className="mt-6">
          <TimingAnalysisWidget 
            surveyId={surveyId}
            platformId={platformId}
            respondentId={respondentId}
            sessionId={routeSessionId}
          />
        </div>
      )}

      {/* Per-Question Timing Table */}
      {isHierarchical && (
        <div className="mt-6">
          <PerQuestionTimingTable 
            surveyId={surveyId}
            platformId={platformId}
            respondentId={respondentId}
            sessionId={routeSessionId}
          />
        </div>
      )}
    </div>
  );
}

export default SessionDetails; 