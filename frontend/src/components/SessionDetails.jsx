import React, { useEffect, useState } from 'react';
import { config } from '../config/config';
import TextQualityWidget from './TextQualityWidget';

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

function SessionDetails({ sessionId }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetch(config.dashboard.sessionDetails(sessionId))
      .then(res => res.json())
      .then(data => {
        setDetails(data);
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load session details');
        setLoading(false);
      });
  }, [sessionId]);

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
    </div>
  );
}

export default SessionDetails; 