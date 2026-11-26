// Live quality: every survey, live bot and fraud results under the survey's rules, and exports.

import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import clsx from 'clsx';
import { Download, Pause, Play, RefreshCw, Search } from 'lucide-react';
import { liveQualityService } from '../services/apiService';
import {
  Badge,
  FlagsChart,
  KpiGrid,
  LiveDot,
  QualityChart,
  RespondentTable,
  StartsChart,
  ago,
  errorText,
  useLiveResults,
  useNow,
} from './quality/QualityParts';
import QualityRulesCard from './quality/QualityRules';
import QualityDataFileCard from './quality/QualityDataFile';
import { PageHeader } from './ui';

const STATUS_FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'flagged', label: 'Flagged' },
  { id: 'clean', label: 'Looks human' },
  { id: 'in_progress', label: 'In survey' },
];

function matches(row, filter, query) {
  if (query && !(row.respondent_id || '').toLowerCase().includes(query) && !row.session_id.toLowerCase().includes(query)) {
    return false;
  }
  if (filter === 'all') return true;
  if (filter === 'flagged') return row.flags.length > 0;
  if (filter === 'clean') return row.status === 'checked' && row.flags.length === 0;
  if (filter === 'in_progress') return row.status === 'in_progress';
  return row.flags.includes(filter);
}

function surveyName(item) {
  return item?.title && item.title !== item.survey_id ? item.title : item?.survey_id;
}

const LiveQuality = () => {
  const [params, setParams] = useSearchParams();
  const selected = params.get('survey') || '';
  const [surveys, setSurveys] = useState([]);
  const [listError, setListError] = useState('');
  const [scope, setScope] = useState('tracked');
  const [search, setSearch] = useState('');
  const [paused, setPaused] = useState(false);
  const [filter, setFilter] = useState('all');
  const [query, setQuery] = useState('');
  const now = useNow();
  const { results, error, loading, refresh } = useLiveResults(
    selected ? () => liveQualityService.getResults(selected) : null,
    selected,
    paused,
  );

  const select = (surveyId) => setParams(surveyId ? { survey: surveyId } : {}, { replace: !selected });

  useEffect(() => {
    liveQualityService
      .listSurveys()
      .then(({ surveys: list }) => {
        setSurveys(list);
        const anyTracked = list.some((item) => item.tracked);
        if (!anyTracked || (selected && !list.some((item) => item.survey_id === selected && item.tracked))) setScope('all');
        if (!selected) {
          const first = list.find((item) => item.tracked) || list[0];
          if (first) select(first.survey_id);
        }
      })
      .catch((err) => setListError(errorText(err, 'The survey list could not be loaded.')));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    setFilter('all');
    setQuery('');
  }, [selected]);

  const visibleSurveys = surveys.filter(
    (item) =>
      (scope === 'all' || item.tracked) &&
      `${item.survey_id} ${item.title || ''}`.toLowerCase().includes(search.toLowerCase()),
  );
  const current = surveys.find((item) => item.survey_id === selected);
  const rows = useMemo(
    () => (results ? results.respondents.filter((row) => matches(row, filter, query.trim().toLowerCase())) : []),
    [results, filter, query],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        description="Live bot and fraud results for each survey, judged under that survey's quality rules. Refreshes every 8 seconds while this tab is open."
        title="Live Quality"
      />

      <div className="flex min-h-0 gap-4">
        <nav aria-label="Surveys" className="hidden w-72 shrink-0 flex-col self-start rounded-xl border border-gray-200 bg-white shadow-sm md:flex">
          <div className="space-y-2 border-b border-gray-200 p-3">
            <label className="relative block">
              <span className="sr-only">Find a survey</span>
              <Search aria-hidden="true" className="pointer-events-none absolute left-2 top-2 h-4 w-4 text-gray-400" />
              <input
                className="h-8 w-full rounded-md border border-gray-300 bg-white pl-8 pr-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Find a survey"
                value={search}
              />
            </label>
            <div className="flex rounded-md border border-gray-200 p-0.5 text-xs" role="radiogroup" aria-label="Which surveys">
              {['tracked', 'all'].map((value) => (
                <button
                  aria-checked={scope === value}
                  className={clsx('flex-1 rounded px-2 py-1 font-medium', scope === value ? 'bg-gray-100 text-gray-900' : 'text-gray-500 hover:text-gray-900')}
                  key={value}
                  onClick={() => setScope(value)}
                  role="radio"
                  type="button"
                >
                  {value === 'tracked' ? 'Tracked XML' : 'All surveys'}
                </button>
              ))}
            </div>
          </div>
          <ul className="max-h-[70vh] min-h-0 flex-1 space-y-0.5 overflow-y-auto p-2">
            {listError && <li className="px-2 py-1 text-xs text-red-600">{listError}</li>}
            {visibleSurveys.map((item) => (
              <li key={item.survey_id}>
                <button
                  aria-current={item.survey_id === selected ? 'page' : undefined}
                  className={clsx('w-full rounded-md px-2 py-1.5 text-left transition-colors', item.survey_id === selected ? 'bg-blue-50' : 'hover:bg-gray-50')}
                  onClick={() => select(item.survey_id)}
                  type="button"
                >
                  <span className={clsx('block truncate text-sm', item.survey_id === selected ? 'font-medium text-blue-700' : 'text-gray-900')}>
                    {surveyName(item)}
                  </span>
                  <span className="block truncate text-[11px] text-gray-500">
                    {item.sessions.toLocaleString()} sessions
                    {item.last_session ? ` · ${ago(item.last_session, now)}` : ' · no responses yet'}
                    {item.custom_rules ? ' · own rules' : ''}
                  </span>
                </button>
              </li>
            ))}
            {!listError && visibleSurveys.length === 0 && (
              <li className="px-2 py-2 text-xs text-gray-500">
                {scope === 'tracked' ? (
                  <>No survey has had tracking added yet. <Link className="text-blue-600 hover:underline" to="/tracking">Add tracking</Link> to a Decipher XML.</>
                ) : (
                  'No surveys found.'
                )}
              </li>
            )}
          </ul>
        </nav>

        <main className="min-w-0 flex-1 space-y-4">
          <div className="md:hidden">
            <label className="text-xs font-medium text-gray-700" htmlFor="survey-picker">Survey</label>
            <select
              className="mt-1 h-9 w-full rounded-md border border-gray-300 bg-white px-2 text-sm"
              id="survey-picker"
              onChange={(event) => select(event.target.value)}
              value={selected}
            >
              {!selected && <option value="">Choose a survey</option>}
              {surveys.map((item) => (
                <option key={item.survey_id} value={item.survey_id}>{surveyName(item)}</option>
              ))}
            </select>
          </div>

          {!selected && <p className="text-sm text-gray-500">{surveys.length || listError ? 'Choose a survey.' : 'Loading surveys…'}</p>}

          {selected && (
            <>
              <div className="flex flex-wrap items-start gap-3">
                <div className="min-w-0 flex-1">
                  <h2 className="truncate text-lg font-semibold text-gray-900">{surveyName(current) || selected}</h2>
                  <p className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
                    <span>Survey id <code>{selected}</code></span>
                    {current?.tracked ? <Badge tone="accent">Tracked XML</Badge> : <Badge>Other integration</Badge>}
                    <LiveDot now={now} paused={paused} updated={results?.updated_at} />
                    <Link className="text-blue-600 hover:underline" to={`/surveys/${encodeURIComponent(selected)}`}>Survey details</Link>
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-1.5">
                  <button
                    className="inline-flex h-8 items-center gap-1.5 rounded-md px-2.5 text-xs font-medium text-gray-700 hover:bg-gray-100"
                    onClick={() => setPaused(!paused)}
                    type="button"
                  >
                    {paused ? <Play aria-hidden="true" className="h-3.5 w-3.5" /> : <Pause aria-hidden="true" className="h-3.5 w-3.5" />}
                    {paused ? 'Resume' : 'Pause'}
                  </button>
                  <button
                    className="inline-flex h-8 items-center gap-1.5 rounded-md px-2.5 text-xs font-medium text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                    disabled={loading}
                    onClick={() => refresh()}
                    type="button"
                  >
                    <RefreshCw aria-hidden="true" className={clsx('h-3.5 w-3.5', loading && 'animate-spin')} />
                    Refresh
                  </button>
                  <a
                    className="inline-flex h-8 items-center gap-1.5 rounded-md border border-gray-300 bg-white px-2.5 text-xs font-medium text-gray-800 hover:bg-gray-50"
                    download
                    href={liveQualityService.exportUrl(selected)}
                  >
                    <Download aria-hidden="true" className="h-3.5 w-3.5" />
                    Export CSV
                  </a>
                </div>
              </div>

              {error && <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</p>}
              {!results && !error && <p className="text-sm text-gray-500">Loading results… Large surveys can take up to a minute.</p>}

              {results && (
                <>
                  <KpiGrid results={results} />
                  <div className="grid gap-3 lg:grid-cols-3">
                    <div className="lg:col-span-2">
                      <StartsChart results={results} />
                    </div>
                    <QualityChart results={results} />
                  </div>
                  <FlagsChart onPick={(flag) => setFilter(flag)} results={results} />

                  <section className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-sm font-semibold text-gray-900">Respondents</h3>
                      <div className="flex flex-wrap gap-1" role="radiogroup" aria-label="Filter respondents">
                        {[
                          ...STATUS_FILTERS,
                          ...results.flag_counts.filter((item) => item.count > 0).map((item) => ({ id: item.flag, label: item.flag })),
                        ].map((item) => (
                          <button
                            aria-checked={filter === item.id}
                            className={clsx(
                              'rounded-full border px-2.5 py-0.5 text-xs',
                              filter === item.id ? 'border-blue-500 bg-blue-50 font-medium text-blue-700' : 'border-gray-300 text-gray-700 hover:border-blue-400',
                            )}
                            key={item.id}
                            onClick={() => setFilter(item.id)}
                            role="radio"
                            type="button"
                          >
                            {item.label}
                          </button>
                        ))}
                      </div>
                      <span className="flex-1" />
                      <input
                        aria-label="Find a respondent"
                        className="h-7 w-48 rounded-md border border-gray-300 bg-white px-2 text-xs placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        onChange={(event) => setQuery(event.target.value)}
                        placeholder="Respondent or session id"
                        value={query}
                      />
                    </div>
                    {results.respondents.length === 0 ? (
                      <p className="rounded-lg border border-dashed border-gray-300 bg-white p-6 text-center text-sm text-gray-500">
                        No one has started this survey yet. Respondents appear here as soon as they open the link.
                      </p>
                    ) : rows.length === 0 ? (
                      <p className="text-sm text-gray-500">No respondents match this filter.</p>
                    ) : (
                      <RespondentTable limit={500} now={now} rows={rows} />
                    )}
                  </section>
                </>
              )}

              <QualityRulesCard onSaved={() => refresh()} surveyId={selected} />
              <QualityDataFileCard surveyId={selected} />
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export default LiveQuality;
