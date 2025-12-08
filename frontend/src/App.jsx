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
import ReportBuilder from './components/ReportBuilder'
import TextAnalysis from './components/TextAnalysis'
import SurveyList from './components/SurveyList'
import SurveyDetails from './components/SurveyDetails'
import PlatformDetails from './components/PlatformDetails'
import RespondentDetails from './components/RespondentDetails'
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
            <Route path="/text-analysis" element={<TextAnalysis />} />
            <Route path="/integrations" element={<Integrations />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/api-playground" element={<ApiPlayground />} />
            <Route path="/quick-start" element={<QuickStartGuide />} />
            <Route path="/reports" element={<ReportBuilder />} />
            {/* Hierarchical API Routes (V2) */}
            <Route path="/surveys" element={<SurveyList />} />
            <Route path="/surveys/:surveyId" element={<SurveyDetails />} />
            <Route path="/surveys/:surveyId/platforms/:platformId" element={<PlatformDetails />} />
            <Route path="/surveys/:surveyId/platforms/:platformId/respondents/:respondentId" element={<RespondentDetails />} />
            <Route path="/surveys/:surveyId/platforms/:platformId/respondents/:respondentId/sessions/:sessionId" element={<SessionDetails />} />
          </Routes>
          <ToastContainer position="bottom-right" autoClose={3000} />
        </main>
      </div>
    </Router>
  )
}

export default App 