import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navigation from './components/Navigation'
import Dashboard from './components/Dashboard'
import SessionList from './components/SessionList'
import SessionDetails from './components/SessionDetails'
import Integrations from './components/Integrations'
import Settings from './components/Settings'
import ApiPlayground from './components/ApiPlayground'
import QuickStartGuide from './components/QuickStartGuide'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import './styles/App.css'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/sessions" element={<SessionList />} />
            <Route path="/sessions/:sessionId" element={<SessionDetails />} />
            <Route path="/integrations" element={<Integrations />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/api-playground" element={<ApiPlayground />} />
            <Route path="/quick-start" element={<QuickStartGuide />} />
          </Routes>
          <ToastContainer position="bottom-right" autoClose={3000} />
        </main>
      </div>
    </Router>
  )
}

export default App 