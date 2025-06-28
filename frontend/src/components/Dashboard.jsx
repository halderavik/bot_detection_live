import React, { useState, useEffect } from 'react'
import { 
  Users, 
  Activity, 
  AlertTriangle, 
  CheckCircle,
  TrendingUp,
  Clock
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { format } from 'date-fns'
import apiService from '../services/apiService'

const Dashboard = () => {
  const [overviewData, setOverviewData] = useState(null)
  const [trendsData, setTrendsData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const [overview, trends] = await Promise.all([
        apiService.getDashboardOverview(),
        apiService.getAnalyticsTrends()
      ])
      setOverviewData(overview)
      setTrendsData(trends.trends || [])
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
          value={`${overviewData?.detections?.bot_rate?.toFixed(1) || 0}%`}
          icon={CheckCircle}
          color="bg-purple-500"
          change={-1.8}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trends Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Activity Trends</h3>
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
        </div>

        {/* Event Distribution */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Event Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={Object.entries(overviewData?.events?.by_type || {}).map(([type, count]) => ({
                  name: type,
                  value: count
                }))}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {Object.entries(overviewData?.events?.by_type || {}).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
        <div className="space-y-4">
          {overviewData?.recent_sessions?.slice(0, 5).map((session) => (
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
                <p className="text-sm text-gray-600">
                  {format(new Date(session.created_at), 'MMM dd, HH:mm')}
                </p>
                {session.detection && (
                  <p className={`text-sm font-medium ${
                    session.detection.is_bot ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {session.detection.is_bot ? 'Bot Detected' : 'Human'}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Dashboard 