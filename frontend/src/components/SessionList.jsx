// Sessions: every tracked session with its latest verdict, filterable and paged.
// Filters live in the URL, so a filtered list can be bookmarked or shared.

import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, RefreshCw, Search, Users, X } from 'lucide-react';
import { dashboardService } from '../services/apiService';
import {
  Button,
  Card,
  EmptyState,
  ErrorBanner,
  Loading,
  PageHeader,
  RiskBadge,
  VerdictBadge,
  apiError,
  formatDateTime,
  inputClass,
  tableClasses as t,
  timeAgo,
} from './ui';

const LIMIT = 25;
const VERDICTS = [
  { id: '', label: 'All' },
  { id: 'bot', label: 'Bots' },
  { id: 'human', label: 'Humans' },
  { id: 'unchecked', label: 'Not checked' },
];

function useDebounced(value, ms = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const handle = window.setTimeout(() => setDebounced(value), ms);
    return () => window.clearTimeout(handle);
  }, [value, ms]);
  return debounced;
}

function SessionList() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const verdict = params.get('verdict') || '';
  const risk = params.get('risk') || '';
  const platform = params.get('platform') || '';
  const page = Math.max(1, Number(params.get('page')) || 1);
  const [search, setSearch] = useState(params.get('q') || '');
  const query = useDebounced(search.trim());

  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const update = (changes) => {
    const next = new URLSearchParams(params);
    Object.entries(changes).forEach(([key, value]) => (value ? next.set(key, value) : next.delete(key)));
    if (!('page' in changes)) next.delete('page');
    setParams(next, { replace: true });
  };

  useEffect(() => {
    if ((params.get('q') || '') !== query) update({ q: query });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  async function load() {
    setLoading(true);
    setError('');
    const filters = {};
    if (verdict === 'bot') filters.is_bot = true;
    if (verdict === 'human') filters.is_bot = false;
    if (verdict === 'unchecked') filters.risk_level = 'unknown';
    else if (risk) filters.risk_level = risk;
    if (platform) filters.platform = platform;
    if (query) filters.search = query;
    try {
      setData(await dashboardService.getSessionsList(page, LIMIT, filters));
    } catch (err) {
      setError(apiError(err, 'Sessions could not be loaded.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [verdict, risk, platform, page, query]);

  const sessions = data?.sessions || [];
  const pagination = data?.pagination || { total: 0, pages: 0 };
  const filtered = Boolean(verdict || risk || platform || query);

  return (
    <div className="space-y-6">
      <PageHeader
        actions={<Button disabled={loading} icon={RefreshCw} onClick={load}>{loading ? 'Refreshing…' : 'Refresh'}</Button>}
        description="Every tracked session, newest first, with its latest verdict. Click a session for its events and the reasons behind the verdict."
        title="Sessions"
      />

      <Card bodyClassName="p-0">
        <div className="flex flex-wrap items-center gap-3 border-b border-gray-100 px-4 py-3">
          <label className="relative min-w-[14rem] flex-1 sm:max-w-xs">
            <span className="sr-only">Search sessions</span>
            <Search aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input
              className={`${inputClass} pl-9`}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Session, respondent or survey id"
              value={search}
            />
          </label>
          <div className="flex rounded-lg border border-gray-200 bg-gray-50 p-0.5" role="radiogroup" aria-label="Verdict">
            {VERDICTS.map((item) => (
              <button
                aria-checked={verdict === item.id}
                className={`rounded-md px-3 py-1.5 text-xs font-medium ${verdict === item.id ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600 hover:text-gray-900'}`}
                key={item.id || 'all'}
                onClick={() => update({ verdict: item.id, risk: item.id === 'unchecked' ? '' : risk })}
                role="radio"
                type="button"
              >
                {item.label}
              </button>
            ))}
          </div>
          <select
            aria-label="Risk level"
            className={`${inputClass} w-auto`}
            disabled={verdict === 'unchecked'}
            onChange={(event) => update({ risk: event.target.value })}
            value={risk}
          >
            <option value="">Any risk</option>
            <option value="low">Low risk</option>
            <option value="medium">Medium risk</option>
            <option value="high">High risk</option>
            <option value="critical">Critical risk</option>
          </select>
          <select aria-label="Platform" className={`${inputClass} w-auto`} onChange={(event) => update({ platform: event.target.value })} value={platform}>
            <option value="">Any platform</option>
            <option value="decipher">Decipher</option>
            <option value="qualtrics">Qualtrics</option>
          </select>
          {filtered && (
            <Button
              icon={X}
              onClick={() => {
                setSearch('');
                setParams({}, { replace: true });
              }}
              size="sm"
              variant="ghost"
            >
              Clear filters
            </Button>
          )}
          <span className="ml-auto text-xs text-gray-500">{pagination.total.toLocaleString()} sessions</span>
        </div>

        {error && <div className="p-4"><ErrorBanner onRetry={load}>{error}</ErrorBanner></div>}
        {!data && !error && <Loading label="Loading sessions…" />}
        {data && sessions.length === 0 && (
          <EmptyState icon={Users} title={filtered ? 'No sessions match these filters' : 'No sessions yet'}>
            {filtered ? 'Try clearing a filter.' : 'Sessions appear as soon as respondents open a tracked survey.'}
          </EmptyState>
        )}
        {sessions.length > 0 && (
          <div className={t.wrap}>
            <table className={`${t.table} min-w-[820px]`}>
              <thead className={t.head}>
                <tr>
                  <th className={t.th}>Respondent</th>
                  <th className={t.th}>Survey</th>
                  <th className={t.th}>Verdict</th>
                  <th className={t.th}>Risk</th>
                  <th className={`${t.th} text-right`}>Bot score</th>
                  <th className={`${t.th} text-right`}>Events</th>
                  <th className={t.th}>Started</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((session) => {
                  const href = `/sessions/${encodeURIComponent(session.id)}`;
                  return (
                    <tr
                      className={`${t.row} cursor-pointer`}
                      key={session.id}
                      onClick={(event) => {
                        if (!event.target.closest('a')) navigate(href);
                      }}
                    >
                      <td className={t.td}>
                        <Link className="font-medium text-gray-900 hover:text-blue-700" to={href}>{session.respondent_id || 'Anonymous'}</Link>
                        <div className="font-mono text-[11px] text-gray-400">{session.id.slice(0, 8)}</div>
                      </td>
                      <td className={t.td}>
                        <div className="max-w-[14rem] truncate">{session.survey_id || '–'}</div>
                        <div className="text-xs capitalize text-gray-400">{session.platform || ''}</div>
                      </td>
                      <td className={t.td}><VerdictBadge analyzed={session.analyzed} isBot={session.is_bot} /></td>
                      <td className={t.td}><RiskBadge level={session.risk_level} /></td>
                      <td className={`${t.td} text-right tabular-nums`}>
                        {session.confidence_score === null || session.confidence_score === undefined ? '–' : Number(session.confidence_score).toFixed(2)}
                      </td>
                      <td className={`${t.td} text-right tabular-nums`}>{session.event_count.toLocaleString()}</td>
                      <td className={`${t.td} whitespace-nowrap`} title={formatDateTime(session.created_at)}>{timeAgo(session.created_at)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {pagination.pages > 1 && (
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 px-4 py-3 text-sm text-gray-600">
            <span>
              {(page - 1) * LIMIT + 1}–{Math.min(page * LIMIT, pagination.total)} of {pagination.total.toLocaleString()}
            </span>
            <div className="flex items-center gap-2">
              <Button disabled={page <= 1} icon={ChevronLeft} onClick={() => update({ page: String(page - 1) })} size="sm">Previous</Button>
              <span className="text-xs">Page {page} of {pagination.pages}</span>
              <Button disabled={page >= pagination.pages} onClick={() => update({ page: String(page + 1) })} size="sm">
                Next<ChevronRight aria-hidden="true" className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

export default SessionList;
