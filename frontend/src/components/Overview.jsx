// Overview: the researcher's home page. Last 7 days at a glance, every survey with its
// bot rate, starts and bots per day, and the latest sessions judged bots.

import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Activity, ArrowRight, Bot, CheckCircle2, FileText, RefreshCw, ShieldCheck, Upload, Users } from 'lucide-react';
import { dashboardService, hierarchicalService, liveQualityService } from '../services/apiService';
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorBanner,
  Loading,
  PageHeader,
  RateBar,
  RiskBadge,
  StatCard,
  apiError,
  buttonClass,
  percent,
  tableClasses as t,
  timeAgo,
  toDate,
} from './ui';

const DAYS = 14;

function useOverview() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    setError('');
    try {
      const [overview, trends, surveys, quality, bots] = await Promise.all([
        dashboardService.getOverviewStats(7),
        dashboardService.getAnalyticsTrends(DAYS, 'day'),
        hierarchicalService.getSurveys({ limit: 200 }),
        liveQualityService.listSurveys().catch(() => ({ surveys: [] })),
        dashboardService.getSessionsList(1, 6, { is_bot: true }),
      ]);
      setData({ overview, trends, surveys, quality, bots });
    } catch (err) {
      setError(apiError(err, 'The overview could not be loaded.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const handle = window.setInterval(() => document.visibilityState === 'visible' && load(), 60000);
    return () => window.clearInterval(handle);
  }, []);

  return { data, error, loading, load };
}

function StartsChart({ trends }) {
  const rows = (trends || []).map((day) => {
    const date = toDate(`${day.date}T00:00:00`);
    const checked = day.checked ?? day.detections ?? 0;
    const bots = day.bots ?? 0;
    return {
      label: date ? date.toLocaleDateString([], { month: 'short', day: 'numeric' }) : day.date,
      Human: Math.max(0, checked - bots),
      Bot: bots,
      'Not checked': Math.max(0, (day.sessions || 0) - checked),
    };
  });
  const total = rows.reduce((sum, row) => sum + row.Human + row.Bot + row['Not checked'], 0);
  if (!total) return <EmptyState icon={Activity} title="No sessions in the last two weeks" />;
  return (
    <div className="h-64">
      <ResponsiveContainer height="100%" width="100%">
        <BarChart data={rows} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid stroke="#f3f4f6" vertical={false} />
          <XAxis axisLine={false} dataKey="label" fontSize={11} interval="preserveStartEnd" tickLine={false} tick={{ fill: '#6b7280' }} />
          <YAxis allowDecimals={false} axisLine={false} fontSize={11} tickLine={false} tick={{ fill: '#6b7280' }} />
          <Tooltip cursor={{ fill: '#f9fafb' }} contentStyle={{ borderRadius: 8, borderColor: '#e5e7eb', fontSize: 12 }} />
          <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="Human" fill="#2563eb" radius={[0, 0, 0, 0]} stackId="s" />
          <Bar dataKey="Bot" fill="#dc2626" stackId="s" />
          <Bar dataKey="Not checked" fill="#d1d5db" radius={[3, 3, 0, 0]} stackId="s" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function SurveysTable({ surveys, titles }) {
  if (!surveys.length) {
    return (
      <EmptyState
        action={<Link className={buttonClass('primary')} to="/tracking"><Upload aria-hidden="true" className="h-4 w-4" />Add tracking to a survey</Link>}
        icon={FileText}
        title="No survey data yet"
      >
        Add tracking to a Decipher survey XML. Respondents appear here as soon as they open the survey.
      </EmptyState>
    );
  }
  return (
    <div className={t.wrap}>
      <table className={`${t.table} min-w-[760px]`}>
        <thead className={t.head}>
          <tr>
            <th className={t.th}>Survey</th>
            <th className={`${t.th} text-right`}>Respondents</th>
            <th className={`${t.th} text-right`}>Checked</th>
            <th className={t.th}>Bot rate</th>
            <th className={t.th}>Last activity</th>
            <th className={`${t.th} text-right`}><span className="sr-only">Actions</span></th>
          </tr>
        </thead>
        <tbody>
          {surveys.map((survey) => {
            const meta = titles[survey.survey_id] || {};
            const name = meta.title && meta.title !== survey.survey_id ? meta.title : survey.survey_id;
            const encoded = encodeURIComponent(survey.survey_id);
            return (
              <tr className={t.row} key={survey.survey_id}>
                <td className={t.td}>
                  <Link className="font-medium text-gray-900 hover:text-blue-700" to={`/quality?survey=${encoded}`}>{name}</Link>
                  <div className="mt-0.5 flex flex-wrap items-center gap-1.5 text-xs text-gray-500">
                    {name !== survey.survey_id && <span className="font-mono">{survey.survey_id}</span>}
                    {meta.tracked && <Badge tone="accent">Tracked XML</Badge>}
                    {meta.custom_rules && <Badge>Own rules</Badge>}
                  </div>
                </td>
                <td className={`${t.td} text-right tabular-nums`}>{(survey.respondent_count ?? 0).toLocaleString()}</td>
                <td className={`${t.td} text-right tabular-nums`}>
                  {(survey.checked_count ?? 0).toLocaleString()}
                  <span className="text-gray-400"> / {(survey.session_count ?? 0).toLocaleString()}</span>
                </td>
                <td className={t.td}>{survey.checked_count ? <RateBar value={survey.bot_rate} /> : <span className="text-gray-400">–</span>}</td>
                <td className={`${t.td} whitespace-nowrap`}>{timeAgo(survey.last_session)}</td>
                <td className={`${t.td} whitespace-nowrap text-right`}>
                  <Link className={buttonClass('secondary', 'sm')} to={`/quality?survey=${encoded}`}>
                    <ShieldCheck aria-hidden="true" className="h-3.5 w-3.5" />Live quality
                  </Link>
                  <Link className={buttonClass('ghost', 'sm', 'ml-1')} to={`/surveys/${encoded}`}>Details</Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function RecentBots({ sessions }) {
  if (!sessions.length) {
    return <EmptyState icon={CheckCircle2} title="No bots detected yet">Sessions judged bots will be listed here.</EmptyState>;
  }
  return (
    <ul className="divide-y divide-gray-100">
      {sessions.map((session) => (
        <li key={session.id}>
          <Link className="flex items-center gap-3 px-1 py-2.5 hover:bg-gray-50" to={`/sessions/${encodeURIComponent(session.id)}`}>
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-red-50 text-red-600">
              <Bot aria-hidden="true" className="h-4 w-4" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-medium text-gray-900">{session.respondent_id || session.id.slice(0, 8)}</span>
              <span className="block truncate text-xs text-gray-500">{session.survey_id || 'No survey'} · {timeAgo(session.analyzed_at || session.created_at)}</span>
            </span>
            <RiskBadge level={session.risk_level} />
          </Link>
        </li>
      ))}
    </ul>
  );
}

const Overview = () => {
  const { data, error, loading, load } = useOverview();

  const titles = useMemo(() => {
    const map = {};
    (data?.quality?.surveys || []).forEach((item) => {
      map[item.survey_id] = item;
    });
    return map;
  }, [data]);

  const surveys = useMemo(() => {
    const list = [...(data?.surveys?.surveys || [])];
    return list.sort((a, b) => (toDate(b.last_session)?.getTime() || 0) - (toDate(a.last_session)?.getTime() || 0));
  }, [data]);

  const sessions = data?.overview?.sessions || {};
  const detections = data?.overview?.detections || {};

  return (
    <div className="space-y-6">
      <PageHeader
        actions={<Button disabled={loading} icon={RefreshCw} onClick={load} variant="secondary">{loading ? 'Refreshing…' : 'Refresh'}</Button>}
        description="How genuine your survey respondents are. Numbers cover sessions that started in the last 7 days; open a survey for its live results."
        title="Overview"
      />

      {error && <ErrorBanner onRetry={load}>{error}</ErrorBanner>}
      {!data && !error && <Loading label="Loading overview…" />}

      {data && (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatCard icon={Users} label="Sessions started" note="Last 7 days" value={(sessions.total ?? 0).toLocaleString()} />
            <StatCard
              icon={CheckCircle2}
              label="Checked"
              note={sessions.total ? `${percent((100 * (detections.checked ?? 0)) / sessions.total, 0)} of sessions analysed` : 'Analysed sessions'}
              value={(detections.checked ?? 0).toLocaleString()}
            />
            <StatCard
              icon={Bot}
              label="Bots"
              note={`${percent(detections.bot_rate)} of checked sessions`}
              tone={(detections.bots_detected ?? 0) > 0 ? 'danger' : 'neutral'}
              value={(detections.bots_detected ?? 0).toLocaleString()}
            />
            <StatCard icon={Activity} label="Surveys" note={`${surveys.filter((s) => toDate(s.last_session) > new Date(Date.now() - 7 * 864e5)).length} active this week`} value={surveys.length} />
          </div>

          <Card
            actions={<Link className={buttonClass('ghost', 'sm')} to="/tracking"><Upload aria-hidden="true" className="h-3.5 w-3.5" />Add tracking</Link>}
            bodyClassName="p-0"
            description="Bot rate is bots out of checked sessions, the same on every page."
            title="Surveys"
          >
            <SurveysTable surveys={surveys} titles={titles} />
          </Card>

          <div className="grid gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2" description={`Sessions started per day over the last ${DAYS} days`} title="Starts and bots">
              <StartsChart trends={data.trends?.trends} />
            </Card>
            <Card
              actions={<Link className={buttonClass('ghost', 'sm')} to="/sessions?verdict=bot">All<ArrowRight aria-hidden="true" className="h-3.5 w-3.5" /></Link>}
              description="Most recent sessions judged bots"
              title="Latest bots"
            >
              <RecentBots sessions={data.bots?.sessions || []} />
            </Card>
          </div>
        </>
      )}
    </div>
  );
};

export default Overview;
