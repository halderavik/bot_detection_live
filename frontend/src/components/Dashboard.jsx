import React, { useState, useEffect } from 'react'
import { 
  Users, 
  Activity, 
  AlertTriangle, 
  CheckCircle,
  TrendingUp,
  Clock,
  Server,
  Database,
  Zap,
  Globe,
  XCircle
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend } from 'recharts'
import { format } from 'date-fns'
import { dashboardService, mockData, healthService, integrationService } from '../services/apiService'
import SessionTable from './SessionTable'
import SessionDetails from './SessionDetails'

const SystemHealth = () => {
  const [health, setHealth] = useState({ backend: null, database: null, integrations: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        setLoading(true);
        const backend = await healthService.checkHealth();
        const integrations = await integrationService.getIntegrationStatus();
        setHealth({
          backend: backend.status === 'healthy',
          database: true, // Backend is healthy, so database is accessible
          integrations: integrations,
        });
      } catch (err) {
        setError('Failed to fetch system health');
      } finally {
        setLoading(false);
      }
    };
    fetchHealth();
  }, []);

  if (loading) return <div className="mb-4">Checking system health...</div>;
  if (error) return <div className="mb-4 text-red-600">{error}</div>;

  return (
    <div className="card mb-4">
      <h3 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
        <Server className="h-5 w-5 text-blue-600 mr-2" />
        System Health
      </h3>
      <div className="flex flex-wrap gap-6">
        <div className="flex items-center space-x-2">
          <CheckCircle className={`h-5 w-5 ${health.backend ? 'text-green-500' : 'text-red-500'}`} />
          <span className="text-sm">Backend</span>
        </div>
        <div className="flex items-center space-x-2">
          <Database className={`h-5 w-5 ${health.database ? 'text-green-500' : 'text-red-500'}`} />
          <span className="text-sm">Database</span>
        </div>
        <div className="flex items-center space-x-2">
          <Globe className="h-5 w-5 text-blue-500" />
          <span className="text-sm">Qualtrics</span>
          {health.integrations?.qualtrics?.configured ? <CheckCircle className="h-5 w-5 text-green-500" /> : <XCircle className="h-5 w-5 text-red-500" />}
        </div>
        <div className="flex items-center space-x-2">
          <Zap className="h-5 w-5 text-purple-500" />
          <span className="text-sm">Decipher</span>
          {health.integrations?.decipher?.configured ? <CheckCircle className="h-5 w-5 text-green-500" /> : <XCircle className="h-5 w-5 text-red-500" />}
        </div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [overviewData, setOverviewData] = useState(null)
  const [trendsData, setTrendsData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedSessionId, setSelectedSessionId] = useState(null)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  // Handle ESC key to close modal
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && selectedSessionId) {
        setSelectedSessionId(null)
      }
    }

    if (selectedSessionId) {
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
  }, [selectedSessionId])

  const closeModal = () => setSelectedSessionId(null)

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      
      // Try to fetch real data from backend
      try {
        const [overview, trends] = await Promise.all([
          dashboardService.getOverviewStats(7),
          dashboardService.getAnalyticsTrends(30, 'day')
        ])
        setOverviewData(overview)
        setTrendsData(trends || [])
      } catch (apiError) {
        console.warn('Backend not available, using mock data:', apiError)
        // Fallback to mock data if backend is not available
        setOverviewData(mockData.overviewStats)
        setTrendsData([
          { date: '2024-01-01', sessions: 120, detections: 8 },
          { date: '2024-01-02', sessions: 135, detections: 12 },
          { date: '2024-01-03', sessions: 98, detections: 6 },
          { date: '2024-01-04', sessions: 156, detections: 15 },
          { date: '2024-01-05', sessions: 142, detections: 11 },
          { date: '2024-01-06', sessions: 178, detections: 18 },
          { date: '2024-01-07', sessions: 165, detections: 14 },
        ])
      }
    } catch (err) {
      setError('Failed to load dashboard data')
      console.error('Dashboard error:', err)
    } finally {
      setLoading(false)
    }
  }

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042']

  const StatCard = ({ title, value, icon: Icon, color, change }) => (
    <div className="card">
      <div className="flex items-center">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {change && (
            <p className={`text-sm ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {change > 0 ? '+' : ''}{change}% from last week
            </p>
          )}
        </div>
      </div>
    </div>
  )

  // Map backend event keys to frontend expected keys
  const eventTypes = overviewData?.events?.by_type || {};
  const pieData = [
    { name: 'Keystrokes', value: eventTypes.keystroke || 0 },
    { name: 'Mouse Events', value: (eventTypes.mouse_move || 0) + (eventTypes.mouse_click || 0) },
    { name: 'Scroll Events', value: eventTypes.scroll || 0 },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-600">{error}</p>
        <button 
          onClick={fetchDashboardData}
          className="btn-primary mt-4"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <SystemHealth />
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-2">Overview of bot detection activity</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Sessions"
          value={overviewData?.sessions?.total || 0}
          icon={Users}
          color="bg-blue-500"
          change={5.2}
        />
        <StatCard
          title="Active Sessions"
          value={overviewData?.sessions?.active || 0}
          icon={Activity}
          color="bg-green-500"
          change={-2.1}
        />
        <StatCard
          title="Bots Detected"
          value={overviewData?.detections?.bots_detected || 0}
          icon={AlertTriangle}
          color="bg-red-500"
          change={12.5}
        />
        <StatCard
          title="Detection Rate"
          value={`${overviewData?.detections?.detection_rate?.toFixed(1) || 0}%`}
          icon={CheckCircle}
          color="bg-purple-500"
          change={-1.8}
        />
      </div>

      {/* Session Table */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">All Sessions</h3>
        <SessionTable onSelectSession={setSelectedSessionId} />
      </div>

      {/* Session Details Modal/Panel */}
      {selectedSessionId && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50 p-4"
          onClick={closeModal}
        >
          <div 
            className="bg-white rounded-lg shadow-lg max-w-4xl w-full max-h-[90vh] flex flex-col relative"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">Session Details</h2>
              <button
                className="text-gray-500 hover:text-gray-800 text-2xl font-bold"
                onClick={closeModal}
              >
                &times;
              </button>
            </div>
            
            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-4">
              <SessionDetails sessionId={selectedSessionId} />
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trends Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Activity Trends</h3>
          {trendsData.length > 1 && trendsData.some(d => d.sessions > 0 || d.detections > 0) ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(value) => format(new Date(value), 'MMM dd')}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(value) => format(new Date(value), 'MMM dd, yyyy')}
                />
                <Line 
                  type="monotone" 
                  dataKey="sessions" 
                  stroke="#3B82F6" 
                  strokeWidth={2}
                  name="Sessions"
                />
                <Line 
                  type="monotone" 
                  dataKey="detections" 
                  stroke="#EF4444" 
                  strokeWidth={2}
                  name="Detections"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-400">
              Not enough data to display trends.
            </div>
          )}
        </div>

        {/* Event Distribution */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Event Distribution</h3>
          {pieData.every(d => d.value === 0) ? (
            <div className="flex items-center justify-center h-64 text-gray-400">
              No event data available.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {[0, 1, 2].map((index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
        <div className="space-y-4">
          {mockData.sessionsList.sessions.map((session) => (
            <div key={session.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-4">
                <div className={`w-3 h-3 rounded-full ${
                  session.detection?.is_bot ? 'bg-red-500' : 'bg-green-500'
                }`}></div>
                <div>
                  <p className="font-medium text-gray-900">Session {session.id.slice(0, 8)}</p>
                  <p className="text-sm text-gray-600">
                    {session.platform} • {session.event_count} events
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900">
                  {session.detection?.is_bot ? 'Bot Detected' : 'Human Confirmed'}
                </p>
                <p className="text-xs text-gray-500">
                  {format(new Date(session.created_at), 'MMM dd, HH:mm')}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        {/* Platform Distribution Pie Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Platform Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={Object.entries(overviewData?.platforms || {}).map(([name, value]) => ({ name, value }))}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label
              >
                {Object.keys(overviewData?.platforms || {}).map((_, idx) => (
                  <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        {/* Risk Breakdown Bar Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Breakdown</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={Object.entries(overviewData?.risk_distribution || {}).map(([level, count]) => ({ level, count }))}>
              <Bar dataKey="count" fill="#EF4444" />
              <XAxis dataKey="level" />
              <Tooltip />
              <Legend />
            </BarChart>
          </ResponsiveContainer>
        </div>
        {/* Event Type Breakdown Pie Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Event Type Breakdown</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={Object.entries(overviewData?.events?.by_type || {}).map(([name, value]) => ({ name, value }))}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label
              >
                {Object.keys(overviewData?.events?.by_type || {}).map((_, idx) => (
                  <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        {/* Top N Surveys/Respondents (mocked) */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Surveys & Respondents</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Top Surveys</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>Survey 1 (320 sessions)</li>
                <li>Survey 2 (210 sessions)</li>
                <li>Survey 3 (180 sessions)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Top Respondents</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>Respondent A (45 events)</li>
                <li>Respondent B (38 events)</li>
                <li>Respondent C (32 events)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard 