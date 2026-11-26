// Session details: the verdict and the reasons behind it first, then the evidence
// (behaviour scores, fraud, open ends, grids, timing), then the raw event log.

import React, { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Bot, CheckCircle2, Clock, HelpCircle } from 'lucide-react';
import clsx from 'clsx';
import { dashboardService, fraudService } from '../services/apiService';
import TextQualityWidget from './TextQualityWidget';
import HierarchicalNavigation from './HierarchicalNavigation';
import HierarchicalFraudWidget from './HierarchicalFraudWidget';
import GridAnalysisWidget from './GridAnalysisWidget';
import TimingAnalysisWidget from './TimingAnalysisWidget';
import PerQuestionTimingTable from './PerQuestionTimingTable';
import {
  Badge,
  Card,
  ErrorBanner,
  Loading,
  PageHeader,
  RiskBadge,
  apiError,
  formatDateTime,
  tableClasses as t,
  toDate,
} from './ui';

const METHOD_LABELS = {
  keystroke_analysis: ['Typing', 'Rhythm and pauses between key presses'],
  mouse_analysis: ['Mouse and touch', 'Movement paths, clicks, and whether input came from a real device'],
  timing_analysis: ['Timing', 'How evenly and quickly pages and answers were completed'],
  device_analysis: ['Device', 'Browser signs of automation or headless browsing'],
  network_analysis: ['Network', 'Connection type and address'],
};

function latestOf(results) {
  return [...(results || [])].sort((a, b) => (toDate(b.analyzed_at)?.getTime() || 0) - (toDate(a.analyzed_at)?.getTime() || 0))[0] || null;
}

function duration(events, session) {
  const times = (events || []).map((event) => toDate(event.timestamp)?.getTime()).filter(Boolean);
  let ms = times.length > 1 ? Math.max(...times) - Math.min(...times) : null;
  if (ms === null && session.created_at && session.last_activity) {
    ms = toDate(session.last_activity).getTime() - toDate(session.created_at).getTime();
  }
  if (ms === null || ms < 0) return '–';
  const seconds = Math.round(ms / 1000);
  if (seconds < 60) return `${seconds} s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes} min ${seconds % 60} s`;
}

function browserName(agent) {
  if (!agent) return '–';
  if (/HeadlessChrome/i.test(agent)) return 'Headless Chrome';
  if (/Edg\//.test(agent)) return 'Edge';
  if (/Chrome\//.test(agent)) return 'Chrome';
  if (/Firefox\//.test(agent)) return 'Firefox';
  if (/Safari\//.test(agent)) return 'Safari';
  return 'Other';
}

function osName(agent) {
  if (!agent) return '';
  if (/iPhone|iPad/.test(agent)) return 'iOS';
  if (/Android/.test(agent)) return 'Android';
  if (/Windows/.test(agent)) return 'Windows';
  if (/Mac OS X/.test(agent)) return 'macOS';
  if (/Linux/.test(agent)) return 'Linux';
  return '';
}

function ScoreBar({ value }) {
  const share = Math.max(0, Math.min(1, Number(value) || 0));
  const colour = share >= 0.7 ? 'bg-red-500' : share >= 0.4 ? 'bg-amber-500' : 'bg-green-500';
  return (
    <span className="flex items-center gap-2">
      <span className="h-1.5 w-full max-w-[10rem] overflow-hidden rounded-full bg-gray-100">
        <span className={clsx('block h-full rounded-full', colour)} style={{ width: `${share * 100}%` }} />
      </span>
      <span className="w-10 text-right tabular-nums text-gray-700">{share.toFixed(2)}</span>
    </span>
  );
}

function Fact({ label, children }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs text-gray-500">{label}</dt>
      <dd className="mt-0.5 truncate text-sm text-gray-900">{children}</dd>
    </div>
  );
}

function VerdictCard({ detection }) {
  if (!detection) {
    return (
      <Card>
        <div className="flex items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gray-100 text-gray-500">
            <HelpCircle aria-hidden="true" className="h-5 w-5" />
          </span>
          <div>
            <h2 className="text-base font-semibold text-gray-900">Not checked yet</h2>
            <p className="mt-0.5 text-sm text-gray-600">
              The respondent is still in the survey or left before the check ran. A verdict appears once the session is analysed.
            </p>
          </div>
        </div>
      </Card>
    );
  }
  const patterns = detection.flagged_patterns || {};
  const signals = Array.isArray(patterns.decisive_signals) ? patterns.decisive_signals : [];
  const isBot = detection.is_bot;
  return (
    <Card>
      <div className="flex flex-wrap items-start gap-4">
        <span className={clsx('flex h-11 w-11 shrink-0 items-center justify-center rounded-full', isBot ? 'bg-red-50 text-red-600' : 'bg-green-50 text-green-600')}>
          {isBot ? <Bot aria-hidden="true" className="h-5 w-5" /> : <CheckCircle2 aria-hidden="true" className="h-5 w-5" />}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-lg font-semibold text-gray-900">{isBot ? 'Judged a bot' : 'Looks human'}</h2>
            <RiskBadge level={detection.risk_level} />
          </div>
          <p className="mt-1 text-sm text-gray-600">{detection.analysis_summary || 'No summary was stored for this analysis.'}</p>
          {signals.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Decisive signals</p>
              <ul className="mt-1 space-y-1">
                {signals.map((signal) => (
                  <li className="flex gap-2 text-sm text-gray-800" key={signal}>
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500" />
                    {signal}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        <dl className="grid shrink-0 grid-cols-2 gap-x-6 gap-y-2 sm:grid-cols-1">
          <Fact label="Bot score">{Number(detection.confidence_score ?? 0).toFixed(2)} <span className="text-gray-400">/ 1</span></Fact>
          <Fact label="Checked">{formatDateTime(detection.analyzed_at)}</Fact>
        </dl>
      </div>
    </Card>
  );
}

function FraudCard({ fraud }) {
  if (!fraud || !fraud.fraud_analysis_available) return null;
  const pct = (value) => (value === null || value === undefined ? '–' : `${Math.round(value * 100)}%`);
  const reasons = Object.keys(fraud.flag_reasons || {});
  return (
    <Card description="Repeat devices and networks, copied answers, location and speed" title="Fraud checks">
      <div className="flex flex-wrap items-center gap-2">
        {fraud.is_duplicate && <Badge tone="danger">Duplicate</Badge>}
        <RiskBadge level={fraud.risk_level} />
        <span className="text-sm text-gray-600">Fraud score {pct(fraud.overall_fraud_score)}</span>
      </div>
      <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Fact label="Same IP address">{fraud.ip_analysis ? `${fraud.ip_analysis.usage_count || 0} sessions` : '–'}</Fact>
        <Fact label="Same device">{fraud.device_fingerprint ? `${fraud.device_fingerprint.usage_count || 0} sessions` : '–'}</Fact>
        <Fact label="Answer similarity">{fraud.duplicate_responses ? pct(fraud.duplicate_responses.similarity_score) : '–'}</Fact>
        <Fact label="Surveys per hour">
          {fraud.velocity?.responses_per_hour !== null && fraud.velocity?.responses_per_hour !== undefined ? fraud.velocity.responses_per_hour.toFixed(1) : '–'}
        </Fact>
      </dl>
      {reasons.length > 0 && (
        <p className="mt-3 text-sm text-gray-700">
          <span className="font-medium text-gray-900">Flagged for: </span>
          {reasons.map((reason) => reason.replace(/_/g, ' ')).join(', ')}
        </p>
      )}
    </Card>
  );
}

function SessionDetails({ sessionId: propSessionId }) {
  const params = useParams();
  const sessionId = propSessionId || params.sessionId;
  const inHierarchy = Boolean(params.surveyId && params.platformId && params.respondentId);

  const [details, setDetails] = useState(null);
  const [fraud, setFraud] = useState(null);
  const [error, setError] = useState('');

  async function load() {
    setError('');
    try {
      const [data, fraudData] = await Promise.all([
        dashboardService.getSessionDetails(sessionId),
        fraudService.getFraudIndicators(sessionId).catch(() => null),
      ]);
      setDetails(data);
      setFraud(fraudData);
    } catch (err) {
      setError(err?.response?.status === 404 ? 'This session was not found.' : apiError(err, 'The session could not be loaded.'));
    }
  }

  useEffect(() => {
    setDetails(null);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const session = details?.session || {};
  const events = details?.behavior_data || [];
  const detection = useMemo(() => latestOf(details?.detection_results), [details]);
  const surveyId = params.surveyId || session.survey_id;
  const platformId = params.platformId || session.platform;
  const respondentId = params.respondentId || session.respondent_id;
  const hierarchy = Boolean(surveyId && platformId && respondentId);
  const methodScores = detection?.method_scores || {};
  const otherPatterns = useMemo(() => {
    const copy = { ...(detection?.flagged_patterns || {}) };
    delete copy.decisive_signals;
    return copy;
  }, [detection]);

  return (
    <div className="space-y-6">
      {inHierarchy ? (
        <HierarchicalNavigation platformId={params.platformId} respondentId={params.respondentId} sessionId={sessionId} surveyId={params.surveyId} />
      ) : (
        <Link className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-blue-700" to="/sessions">
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />All sessions
        </Link>
      )}

      {error && <ErrorBanner onRetry={load}>{error}</ErrorBanner>}
      {!details && !error && <Loading label="Loading session…" />}

      {details && (
        <>
          <PageHeader
            description={
              <>
                {session.survey_id ? (
                  <Link className="hover:text-blue-700" to={`/quality?survey=${encodeURIComponent(session.survey_id)}`}>{session.survey_id}</Link>
                ) : 'No survey'}
                {session.platform ? ` · ${session.platform}` : ''} · started {formatDateTime(session.created_at)}
              </>
            }
            eyebrow={<span className="font-mono">Session {String(session.id || sessionId).slice(0, 8)}</span>}
            title={session.respondent_id || 'Anonymous respondent'}
          />

          <VerdictCard detection={detection} />

          <div className="grid gap-6 lg:grid-cols-5">
            <Card className="lg:col-span-3" description="0 looks human, 1 looks automated" title="Behaviour scores">
              {Object.keys(methodScores).length === 0 ? (
                <p className="text-sm text-gray-500">No behaviour scores yet.</p>
              ) : (
                <ul className="space-y-3">
                  {Object.entries(methodScores).map(([method, score]) => {
                    const [label, help] = METHOD_LABELS[method] || [method.replace(/_/g, ' '), ''];
                    return (
                      <li className="grid grid-cols-1 items-center gap-1 sm:grid-cols-[minmax(0,1fr)_14rem] sm:gap-4" key={method}>
                        <div className="min-w-0">
                          <p className={clsx('text-sm font-medium text-gray-900', !METHOD_LABELS[method] && 'capitalize')}>{label}</p>
                          {help && <p className="text-xs text-gray-500">{help}</p>}
                        </div>
                        <ScoreBar value={score} />
                      </li>
                    );
                  })}
                </ul>
              )}
            </Card>
            <Card className="lg:col-span-2" title="Session">
              <dl className="grid grid-cols-2 gap-4">
                <Fact label="Time in survey"><span className="inline-flex items-center gap-1"><Clock aria-hidden="true" className="h-3.5 w-3.5 text-gray-400" />{duration(events, session)}</span></Fact>
                <Fact label="Events recorded">{events.length.toLocaleString()}</Fact>
                <Fact label="Browser">{browserName(session.user_agent)}{osName(session.user_agent) ? ` on ${osName(session.user_agent)}` : ''}</Fact>
                <Fact label="IP address"><span className="font-mono text-xs">{session.ip_address || '–'}</span></Fact>
                <Fact label="Last activity">{formatDateTime(session.last_activity)}</Fact>
                <Fact label="Status">{session.is_completed ? 'Completed' : session.is_active ? 'Active' : 'Ended'}</Fact>
              </dl>
            </Card>
          </div>

          {hierarchy ? (
            <HierarchicalFraudWidget platformId={platformId} respondentId={respondentId} sessionId={sessionId} surveyId={surveyId} />
          ) : (
            <FraudCard fraud={fraud} />
          )}

          <TextQualityWidget sessionId={sessionId} />

          {hierarchy && (
            <>
              <GridAnalysisWidget platformId={platformId} respondentId={respondentId} sessionId={sessionId} surveyId={surveyId} />
              <TimingAnalysisWidget platformId={platformId} respondentId={respondentId} sessionId={sessionId} surveyId={surveyId} />
              <PerQuestionTimingTable platformId={platformId} respondentId={respondentId} sessionId={sessionId} surveyId={surveyId} />
            </>
          )}

          <Card bodyClassName="p-0">
            <details>
              <summary className="cursor-pointer select-none px-5 py-4 text-sm font-semibold text-gray-900 hover:bg-gray-50">
                Event log <span className="font-normal text-gray-500">({events.length.toLocaleString()} events)</span>
              </summary>
              <div className="max-h-96 overflow-auto border-t border-gray-100">
                <table className={`${t.table} min-w-[640px] text-xs`}>
                  <thead className={`${t.head} sticky top-0`}>
                    <tr>
                      <th className={t.th}>Time</th>
                      <th className={t.th}>Event</th>
                      <th className={t.th}>Element</th>
                      <th className={t.th}>Screen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {events.map((event, index) => (
                      <tr className={t.row} key={event.id || index}>
                        <td className="whitespace-nowrap px-4 py-1.5 font-mono text-gray-600">{toDate(event.timestamp)?.toLocaleTimeString() || '–'}</td>
                        <td className="px-4 py-1.5 text-gray-800">{event.event_type.replace(/_/g, ' ')}</td>
                        <td className="max-w-xs truncate px-4 py-1.5 font-mono text-gray-500">{event.element_id || '–'}</td>
                        <td className="px-4 py-1.5 text-gray-500">{event.screen_width && event.screen_height ? `${event.screen_width}×${event.screen_height}` : '–'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          </Card>

          {Object.keys(otherPatterns).length > 0 && (
            <Card bodyClassName="p-0">
              <details>
                <summary className="cursor-pointer select-none px-5 py-4 text-sm font-semibold text-gray-900 hover:bg-gray-50">
                  Technical details <span className="font-normal text-gray-500">(raw analysis output)</span>
                </summary>
                <pre className="max-h-96 overflow-auto border-t border-gray-100 bg-gray-50 px-5 py-4 text-xs text-gray-700">
                  {JSON.stringify(otherPatterns, null, 2)}
                </pre>
              </details>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

export default SessionDetails;
