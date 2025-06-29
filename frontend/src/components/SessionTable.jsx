import React, { useEffect, useState, useCallback } from 'react';

function formatDate(dateStr) {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString();
}

function SessionTable({ onSelectSession }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSessions = useCallback(() => {
    setLoading(true);
    fetch('http://localhost:8000/api/v1/dashboard/sessions')
      .then(res => res.json())
      .then(data => {
        setSessions(data.sessions || []);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to load sessions');
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchSessions();
    const interval = setInterval(fetchSessions, 15000); // Poll every 15s
    return () => clearInterval(interval);
  }, [fetchSessions]);

  if (loading) return <div>Loading sessions...</div>;
  if (error) return <div className="text-red-600">{error}</div>;
  if (!sessions.length) return <div>No sessions found.</div>;

  return (
    <div>
      {/* Session Count */}
      <div className="flex justify-between items-center mb-3">
        <span className="text-sm text-gray-600">
          {sessions.length} session{sessions.length !== 1 ? 's' : ''} found
        </span>
        {sessions.length > 10 && (
          <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
            Scroll to see more
          </span>
        )}
      </div>
      
      <div className="overflow-x-auto">
        <div className="max-h-96 overflow-y-auto border border-gray-200 rounded-lg">
          <table className="min-w-full bg-white">
            <thead className="bg-gray-100 sticky top-0 z-10">
              <tr>
                <th className="px-2 py-2" title="Unique session identifier">Session ID</th>
                <th className="px-2 py-2" title="Session creation time">Created At</th>
                <th className="px-2 py-2" title="Last event or activity time">Last Activity</th>
                <th className="px-2 py-2" title="Is the session currently active?">Active</th>
                <th className="px-2 py-2" title="Survey platform (Qualtrics, Decipher, etc)">Platform</th>
                <th className="px-2 py-2" title="Survey ID if available">Survey ID</th>
                <th className="px-2 py-2" title="Respondent ID if available">Respondent ID</th>
                <th className="px-2 py-2" title="Number of events recorded">Event Count</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map(session => (
                <tr
                  key={session.id}
                  className="hover:bg-blue-50 cursor-pointer border-b border-gray-100"
                  onClick={() => onSelectSession(session.id)}
                >
                  <td className="px-2 py-1 font-mono text-xs">{session.id}</td>
                  <td className="px-2 py-1">{formatDate(session.created_at)}</td>
                  <td className="px-2 py-1">{formatDate(session.last_activity)}</td>
                  <td className="px-2 py-1">
                    {session.is_active ? (
                      <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs">Active</span>
                    ) : (
                      <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">Inactive</span>
                    )}
                  </td>
                  <td className="px-2 py-1">{session.platform || '-'}</td>
                  <td className="px-2 py-1">{session.survey_id || '-'}</td>
                  <td className="px-2 py-1">{session.respondent_id || '-'}</td>
                  <td className="px-2 py-1">{session.event_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default SessionTable; 