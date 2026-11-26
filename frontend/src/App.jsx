import React from 'react'
import { BrowserRouter, HashRouter, Navigate, Routes, Route, Link } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import Overview from './components/Overview'
import SessionList from './components/SessionList'
import SessionDetails from './components/SessionDetails'
import Integrations from './components/Integrations'
import Settings from './components/Settings'
import ApiPlayground from './components/ApiPlayground'
import QuickStartGuide from './components/QuickStartGuide'
import ReportBuilder from './components/ReportBuilder'
import TextAnalysis from './components/TextAnalysis'
import SurveyDetails from './components/SurveyDetails'
import PlatformDetails from './components/PlatformDetails'
import RespondentDetails from './components/RespondentDetails'
import SurveyTracking from './components/SurveyTracking'
import LiveQuality from './components/LiveQuality'
import { EmptyState, buttonClass } from './components/ui'
import { ToastContainer } from 'react-toastify'
import { Compass } from 'lucide-react'
import 'react-toastify/dist/ReactToastify.css'
import './styles/App.css'

function NotFound() {
  return (
    <EmptyState
      action={<Link className={buttonClass('primary')} to="/">Go to Overview</Link>}
      icon={Compass}
      title="This page doesn't exist"
    >
      The address may be old or mistyped.
    </EmptyState>
  )
}

// Reason: the production dashboard is a static page in a storage bucket, which can't send
// every path to index.html, so addresses there use a hash (index.html#/quality) and
// survive reloads and bookmarks. Local development keeps normal paths.
const Router = import.meta.env.VITE_ROUTER_MODE === 'hash' ? HashRouter : BrowserRouter

function App() {
  return (
    <Router>
      <AppShell>
        <Routes>
          <Route path="/" element={<Overview />} />
          {/* Old addresses: the dashboard and survey list are now the Overview. */}
          <Route path="/dashboard" element={<Navigate replace to="/" />} />
          <Route path="/surveys" element={<Navigate replace to="/" />} />
          <Route path="/quality" element={<LiveQuality />} />
          <Route path="/sessions" element={<SessionList />} />
          <Route path="/sessions/:sessionId" element={<SessionDetails />} />
          <Route path="/text-analysis" element={<TextAnalysis />} />
          <Route path="/reports" element={<ReportBuilder />} />
          <Route path="/tracking" element={<SurveyTracking />} />
          <Route path="/integrations" element={<Integrations />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/quick-start" element={<QuickStartGuide />} />
          <Route path="/api-playground" element={<ApiPlayground />} />
          <Route path="/surveys/:surveyId" element={<SurveyDetails />} />
          <Route path="/surveys/:surveyId/platforms/:platformId" element={<PlatformDetails />} />
          <Route path="/surveys/:surveyId/platforms/:platformId/respondents/:respondentId" element={<RespondentDetails />} />
          <Route path="/surveys/:surveyId/platforms/:platformId/respondents/:respondentId/sessions/:sessionId" element={<SessionDetails />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AppShell>
      <ToastContainer position="bottom-right" autoClose={3000} />
    </Router>
  )
}

export default App
