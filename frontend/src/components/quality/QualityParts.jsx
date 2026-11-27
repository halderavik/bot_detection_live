// Shared pieces of the live quality dashboard: polling, tiles, charts, and the respondent table.

import React, { Fragment, useEffect, useRef, useState } from 'react';
import clsx from 'clsx';
import { Link } from 'react-router-dom';
import { AlertTriangle, Check, ChevronDown, ChevronRight } from 'lucide-react';

export const POLL_MS = 8000;

const TONES = {
  neutral: 'bg-gray-100 text-gray-700',
  accent: 'bg-blue-50 text-blue-700',
  success: 'bg-green-50 text-green-700',
  warn: 'bg-amber-50 text-amber-800',
  danger: 'bg-red-50 text-red-700',
};

export function Badge({ tone = 'neutral', children }) {
  return (
    <span className={clsx('inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium', TONES[tone])}>
      {children}
    </span>
  );
}

export function errorText(err, fallback) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join('; ');
  return err?.message || fallback;
}

/** Poll a results loader every POLL_MS while the tab is visible and not paused. */
export function useLiveResults(load, key, paused) {
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const inFlight = useRef(false);
  const loader = useRef(load);
  loader.current = load;

  async function refresh() {
    if (!loader.current || inFlight.current) return;
    inFlight.current = true;
    setLoading(true);
    try {
      setResults(await loader.current());
      setError('');
    } catch (err) {
      setError(errorText(err, 'The live results could not be loaded.'));
    } finally {
      inFlight.current = false;
      setLoading(false);
    }
  }

  useEffect(() => {
    setResults(null);
    setError('');
    if (!key) return;
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  useEffect(() => {
    if (!key || paused) return undefined;
    const handle = window.setInterval(() => {
      if (document.visibilityState === 'visible') refresh();
    }, POLL_MS);
    return () => window.clearInterval(handle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, paused]);

  return { results, error, loading, refresh };
}

/** A clock that ticks every second, for "updated 5s ago" labels. */
export function useNow() {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const handle = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(handle);
  }, []);
  return now;
}

/** Parse an API time; times without a zone are UTC. */
function toTime(iso) {
  if (!iso) return NaN;
  const text = /[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`;
  return new Date(text).getTime();
}

export function ago(iso, now) {
  if (!iso) return '';
  const seconds = Math.max(0, Math.round((now - toTime(iso)) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.round(seconds / 60)} min ago`;
  if (seconds < 86400) return `${Math.round(seconds / 3600)} h ago`;
  return new Date(toTime(iso)).toLocaleDateString();
}

export function quality(value) {
  return value === null || value === undefined ? '–' : `${Math.round(value)}`;
}

export function LiveDot({ paused, updated, now }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-gray-700">
      <span className={clsx('h-2 w-2 rounded-full', paused ? 'bg-gray-300' : 'animate-pulse bg-green-500')} />
      {paused ? 'Paused' : 'Live'}
      {updated && <span className="font-normal text-gray-500">· updated {ago(updated, now)}</span>}
    </span>
  );
}

function Tile({ label, value, note, tone }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm">
      <p className="text-[11px] font-medium uppercase tracking-wide text-gray-500">{label}</p>
      <p className="mt-0.5 flex items-center gap-1.5 text-2xl font-semibold tabular-nums text-gray-900">
        {value}
        {tone && Number(value) > 0 && (
          <AlertTriangle aria-label="Needs review" className={clsx('h-4 w-4', tone === 'danger' ? 'text-red-600' : 'text-amber-500')} />
        )}
      </p>
      {note && <p className="text-xs text-gray-500">{note}</p>}
    </div>
  );
}

export function KpiGrid({ results }) {
  const totals = results.totals;
  const avg = results.text.avg_quality;
  const pageSeconds = results.rules?.speeder_page_seconds ?? 3.5;
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      <Tile label="Started" note={`${totals.in_progress} in survey now`} value={totals.sessions} />
      <Tile label="Checked" note={`${totals.dropped} did not finish`} value={totals.checked} />
      <Tile
        label="Flagged"
        note={totals.sessions ? `${Math.round((100 * totals.flagged) / totals.sessions)}% of starts` : 'At least one check'}
        tone="warn"
        value={totals.flagged}
      />
      <Tile label="Bot-like" note="Behaviour verdict" tone="danger" value={totals.bots} />
      <Tile
        label="Low-quality text"
        note={avg != null ? `Avg quality ${Math.round(avg)}/100` : 'Open ends'}
        tone="warn"
        value={totals.low_quality_text}
      />
      <Tile label="Straight-liners" note="Same answer across a grid" tone="warn" value={totals.straight_liners} />
      <Tile label="Speeders" note={`Under ${pageSeconds} s a page`} tone="warn" value={totals.speeders} />
      <Tile label="Duplicates" note={`${results.fraud.high_risk} high fraud risk`} tone="danger" value={totals.duplicates} />
    </div>
  );
}

export function statusBadge(row) {
  if (row.status === 'in_progress') return <Badge tone="accent">In survey</Badge>;
  if (row.status === 'dropped') return <Badge>Not finished</Badge>;
  if (row.verdict === 'bot') return <Badge tone="danger">Bot-like</Badge>;
  if (row.flags.length > 0) return <Badge tone="warn">Review</Badge>;
  return (
    <Badge tone="success">
      <Check aria-hidden="true" className="h-3 w-3" />
      Looks human
    </Badge>
  );
}

function RespondentDetail({ row }) {
  const label = 'font-medium text-gray-900';
  return (
    <div className="space-y-2 text-xs text-gray-700">
      <p>
        <span className={label}>Behaviour:</span>{' '}
        {row.verdict === 'pending'
          ? 'not scored yet (still in the survey or did not finish)'
          : `${row.verdict}, risk ${String(row.risk).toLowerCase()}`}
        {row.explanation ? ` · ${row.explanation}` : ''} · {row.events} events
      </p>
      {row.fraud_score != null && (
        <p>
          <span className={label}>Fraud:</span> score {Number(row.fraud_score).toFixed(2)}
          {row.fraud_risk ? `, ${String(row.fraud_risk).toLowerCase()} risk` : ''}
          {row.duplicate ? ', duplicate of another response' : ''}
          {row.fraud_reasons && Object.keys(row.fraud_reasons).length > 0
            ? ` · signals: ${Object.keys(row.fraud_reasons).join(', ').replace(/_/g, ' ')}`
            : ''}
        </p>
      )}
      {row.grid_explanation && <p><span className={label}>Grid:</span> {row.grid_explanation}</p>}
      {row.timing_explanation && <p><span className={label}>Timing:</span> {row.timing_explanation}</p>}
      {row.seconds ? <p><span className={label}>Time:</span> {Math.round(row.seconds)} seconds over {row.pages} pages</p> : null}
      {row.text_details.length > 0 && (
        <ul className="space-y-1">
          {row.text_details.map((detail, index) => (
            <li className="rounded-md border border-gray-200 bg-white px-2.5 py-1.5" key={index}>
              <p className="text-gray-500">{detail.question}</p>
              <p className="text-gray-900">“{detail.answer}”</p>
              <p>
                Quality {quality(detail.quality)}/100
                {detail.flagged && detail.reasons.length > 0 && (
                  <span className="text-amber-700"> · {detail.reasons.join(', ').replace(/_/g, ' ')}</span>
                )}
              </p>
            </li>
          ))}
        </ul>
      )}
      <p className="font-mono text-[11px] text-gray-500">
        Session {row.session_id} ·{' '}
        <Link className="text-blue-600 hover:underline" to={`/sessions/${encodeURIComponent(row.session_id)}`}>
          open session details
        </Link>
      </p>
    </div>
  );
}

export function RespondentTable({ rows, now, limit }) {
  const [open, setOpen] = useState(null);
  const shown = limit ? rows.slice(0, limit) : rows;
  const th = 'px-2 py-2 font-medium';
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
      <table className="w-full min-w-[680px] text-sm">
        <thead className="bg-gray-50 text-left text-[11px] uppercase tracking-wide text-gray-500">
          <tr>
            <th className="w-6 px-2 py-2" />
            <th className={th}>Started</th>
            <th className={th}>Respondent</th>
            <th className={th}>Status</th>
            <th className={clsx(th, 'text-right')}>Text quality</th>
            <th className={clsx(th, 'text-right')}>Time</th>
            <th className={th}>Flags</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {shown.map((row) => {
            const expanded = open === row.session_id;
            const toggle = () => setOpen(expanded ? null : row.session_id);
            return (
              <Fragment key={row.session_id}>
                <tr
                  aria-expanded={expanded}
                  className="cursor-pointer hover:bg-gray-50"
                  onClick={toggle}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      toggle();
                    }
                  }}
                  tabIndex={0}
                >
                  <td className="px-2 py-2 text-gray-400">
                    {expanded ? <ChevronDown aria-hidden="true" className="h-4 w-4" /> : <ChevronRight aria-hidden="true" className="h-4 w-4" />}
                  </td>
                  <td className="whitespace-nowrap px-2 py-2 text-gray-700" title={row.started || ''}>{ago(row.started, now)}</td>
                  <td className="px-2 py-2 font-mono text-xs">{row.respondent_id || '–'}</td>
                  <td className="px-2 py-2">{statusBadge(row)}</td>
                  <td className="px-2 py-2 text-right tabular-nums">
                    {quality(row.text_quality)}
                    {row.text_flagged > 0 && <span className="ml-1 text-xs text-amber-700">({row.text_flagged} flagged)</span>}
                  </td>
                  <td className="px-2 py-2 text-right tabular-nums text-gray-700">{row.seconds ? `${Math.round(row.seconds)} s` : '–'}</td>
                  <td className="px-2 py-2">
                    <div className="flex flex-wrap gap-1">
                      {row.flags.map((flag) => (
                        <Badge key={flag} tone={flag === 'Bot-like behaviour' || flag === 'Duplicate' ? 'danger' : 'warn'}>{flag}</Badge>
                      ))}
                    </div>
                  </td>
                </tr>
                {expanded && (
                  <tr className="bg-gray-50">
                    <td />
                    <td className="px-2 py-3" colSpan={6}>
                      <RespondentDetail row={row} />
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
      {limit && rows.length > limit && (
        <p className="border-t border-gray-200 px-3 py-2 text-xs text-gray-500">Showing the newest {limit} of {rows.length}.</p>
      )}
    </div>
  );
}

function Tip({ tip }) {
  if (!tip) return null;
  return (
    <div
      className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full whitespace-nowrap rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-900 shadow-md"
      role="status"
      style={{ left: tip.x, top: tip.y - 6 }}
    >
      {tip.text}
    </div>
  );
}

function ChartCard({ title, note, children }) {
  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <h4 className="text-sm font-semibold text-gray-900">{title}</h4>
      {note && <p className="text-xs text-gray-500">{note}</p>}
      <div className="relative mt-2">{children}</div>
    </section>
  );
}

const CLEAN = '#2563eb';
const FLAGGED = '#f59e0b';

/** Starts over time as stacked bars: clean starts and flagged starts. */
export function StartsChart({ results }) {
  const [tip, setTip] = useState(null);
  const buckets = results.trend.buckets;
  const width = 560;
  const height = 150;
  const pad = { left: 28, right: 6, top: 8, bottom: 20 };
  const max = Math.max(1, ...buckets.map((bucket) => bucket.started));
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;
  const slot = buckets.length ? plotW / buckets.length : plotW;
  const barW = Math.max(2, Math.min(28, slot - 2));
  const label = (iso) => {
    const date = new Date(toTime(iso));
    return results.trend.unit === 'hour'
      ? date.toLocaleTimeString([], { hour: 'numeric' })
      : date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };
  const ticks = [...new Set([0, Math.ceil(max / 2), max])];
  const every = Math.max(1, Math.ceil(buckets.length / 6));
  return (
    <ChartCard note={`Respondents who started, per ${results.trend.unit}`} title="Starts over time">
      <div className="mb-1 flex gap-3 text-xs text-gray-700">
        <span className="inline-flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-sm" style={{ background: CLEAN }} />Clean</span>
        <span className="inline-flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-sm" style={{ background: FLAGGED }} />Flagged</span>
      </div>
      {buckets.length === 0 ? (
        <p className="py-8 text-center text-sm text-gray-500">No starts yet.</p>
      ) : (
        <svg aria-label="Starts over time" className="w-full" onMouseLeave={() => setTip(null)} role="img" viewBox={`0 0 ${width} ${height}`}>
          {ticks.map((tick) => {
            const y = pad.top + plotH - (tick / max) * plotH;
            return (
              <g key={tick}>
                <line stroke="#e5e7eb" x1={pad.left} x2={width - pad.right} y1={y} y2={y} />
                <text fill="#6b7280" fontSize="10" textAnchor="end" x={pad.left - 4} y={y + 3}>{tick}</text>
              </g>
            );
          })}
          {buckets.map((bucket, index) => {
            const x = pad.left + index * slot + (slot - barW) / 2;
            const clean = bucket.started - bucket.flagged;
            const cleanH = (clean / max) * plotH;
            const flaggedH = (bucket.flagged / max) * plotH;
            const base = pad.top + plotH;
            const text = `${label(bucket.start)}: ${bucket.started} started, ${bucket.flagged} flagged`;
            return (
              <g key={bucket.start}>
                <rect
                  fill="transparent"
                  height={plotH}
                  onMouseEnter={(event) => {
                    const box = event.currentTarget.ownerSVGElement.getBoundingClientRect();
                    setTip({ x: ((x + barW / 2) / width) * box.width, y: ((base - cleanH - flaggedH) / height) * box.height, text });
                  }}
                  width={slot}
                  x={pad.left + index * slot}
                  y={pad.top}
                />
                {clean > 0 && (
                  <rect fill={CLEAN} height={Math.max(0, cleanH - (bucket.flagged ? 1 : 0))} pointerEvents="none" rx={2} width={barW} x={x} y={base - cleanH} />
                )}
                {bucket.flagged > 0 && (
                  <rect fill={FLAGGED} height={Math.max(1, flaggedH - 1)} pointerEvents="none" rx={2} width={barW} x={x} y={base - cleanH - flaggedH} />
                )}
                {index % every === 0 && (
                  <text fill="#6b7280" fontSize="10" textAnchor="middle" x={x + barW / 2} y={height - 6}>{label(bucket.start)}</text>
                )}
              </g>
            );
          })}
          <line stroke="#d1d5db" x1={pad.left} x2={width - pad.right} y1={pad.top + plotH} y2={pad.top + plotH} />
        </svg>
      )}
      <Tip tip={tip} />
    </ChartCard>
  );
}

/** Respondents per flag, one horizontal bar each, labelled with the count. */
export function FlagsChart({ results, onPick, note }) {
  const counts = results.flag_counts;
  const max = Math.max(1, ...counts.map((item) => item.count));
  const total = Math.max(1, results.totals.sessions);
  return (
    <ChartCard note={note || "Respondents with each flag (one person can have several). Click a bar to filter the table."} title="Why respondents were flagged">
      <ul className="space-y-1.5">
        {counts.map((item) => (
          <li key={item.flag}>
            <button
              className="grid w-full grid-cols-[9.5rem_1fr_4.5rem] items-center gap-2 rounded px-1 py-0.5 text-left text-xs hover:bg-gray-50 disabled:cursor-default disabled:hover:bg-transparent"
              disabled={!onPick || item.count === 0}
              onClick={() => onPick && onPick(item.flag)}
              title={`${item.flag}: ${item.count} of ${results.totals.sessions} respondents`}
              type="button"
            >
              <span className="truncate text-gray-700">{item.flag}</span>
              <span className="h-3 rounded-sm bg-gray-100">
                <span className="block h-3 rounded-sm" style={{ width: `${(item.count / max) * 100}%`, background: FLAGGED }} />
              </span>
              <span className="text-right tabular-nums text-gray-900">
                {item.count} <span className="text-gray-500">({Math.round((100 * item.count) / total)}%)</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
    </ChartCard>
  );
}

const QUALITY_BUCKETS = ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90-100'];

/** Open-end quality scores as a histogram, low scores to the left. */
export function QualityChart({ results }) {
  const [tip, setTip] = useState(null);
  const values = QUALITY_BUCKETS.map((bucket) => Number(results.quality_distribution[bucket] || 0));
  const total = values.reduce((sum, value) => sum + value, 0);
  const max = Math.max(1, ...values);
  return (
    <ChartCard note={`${results.text.responses} answers scored 0 to 100 · below 40 is usually flagged`} title="Open-end quality">
      {total === 0 ? (
        <p className="py-8 text-center text-sm text-gray-500">No open-end answers yet.</p>
      ) : (
        <div className="flex h-[120px] items-end gap-[2px]" onMouseLeave={() => setTip(null)}>
          {values.map((value, index) => (
            <div className="flex h-full flex-1 flex-col justify-end" key={QUALITY_BUCKETS[index]}>
              <div
                className="rounded-t"
                onMouseEnter={(event) => {
                  const box = event.currentTarget.parentElement.parentElement.getBoundingClientRect();
                  const own = event.currentTarget.getBoundingClientRect();
                  setTip({ x: own.left - box.left + own.width / 2, y: own.top - box.top, text: `Score ${QUALITY_BUCKETS[index]}: ${value} answers` });
                }}
                style={{ height: `${Math.max(value ? 3 : 0, (value / max) * 100)}%`, background: index < 4 ? FLAGGED : CLEAN }}
              />
            </div>
          ))}
        </div>
      )}
      <div className="mt-1 flex justify-between text-[10px] text-gray-500"><span>0</span><span>50</span><span>100</span></div>
      <Tip tip={tip} />
    </ChartCard>
  );
}
