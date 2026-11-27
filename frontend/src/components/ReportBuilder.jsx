// Reports: build a survey quality report from the live results, under the survey's own
// quality rules, for a chosen period. Pick the sections, preview it, then download the
// respondent rows as CSV or print it (or save it as PDF from the print dialog).

import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import clsx from 'clsx';
import { BarChart3, ClipboardCopy, Download, ExternalLink, FileText, Printer } from 'lucide-react';
import { liveQualityService } from '../services/apiService';
import { Badge, FlagsChart, KpiGrid, QualityChart, StartsChart, errorText } from './quality/QualityParts';
import { Button, Card, EmptyState, ErrorBanner, Loading, PageHeader, formatDateTime, inputClass, toDate } from './ui';

const SECTIONS = [
  { id: 'summary', label: 'Summary', note: 'A few sentences on what the numbers say' },
  { id: 'headline', label: 'Headline numbers', note: 'Started, checked, flagged, bots and each check' },
  { id: 'flags', label: 'Why respondents were flagged', note: 'Respondents per flag' },
  { id: 'trend', label: 'Starts over time', note: 'Clean and flagged starts per hour or day' },
  { id: 'text', label: 'Open-end quality', note: 'How the open-ended answers scored' },
  { id: 'checks', label: 'Checks in detail', note: 'What each check looks at and what it found' },
  { id: 'respondents', label: 'Respondent list', note: 'One row per respondent, with reasons' },
  { id: 'method', label: 'Rules and method', note: 'The rules in force and how the survey is tracked' },
];

const PERIODS = [
  { id: 'all', label: 'All time' },
  { id: '24h', label: 'Last 24 hours', hours: 24 },
  { id: '7d', label: 'Last 7 days', hours: 24 * 7 },
  { id: '30d', label: 'Last 30 days', hours: 24 * 30 },
  { id: 'custom', label: 'Custom dates' },
];

const ROW_SETS = [
  { id: 'flagged', label: 'Flagged only' },
  { id: 'bots', label: 'Bot-like only' },
  { id: 'checked', label: 'Checked (finished)' },
  { id: 'all', label: 'Everyone who started' },
];

// CSV columns: id, header, value from a respondent row.
const COLUMNS = [
  { id: 'respondent_id', label: 'Respondent id', value: (row) => row.respondent_id },
  { id: 'session_id', label: 'Session id', value: (row) => row.session_id },
  { id: 'started', label: 'Started (UTC)', value: (row) => row.started },
  { id: 'status', label: 'Status', value: (row) => statusText(row) },
  { id: 'verdict', label: 'Behaviour verdict', value: (row) => row.verdict },
  { id: 'risk', label: 'Behaviour risk', value: (row) => row.risk },
  { id: 'confidence', label: 'Bot score (0-1)', value: (row) => row.confidence },
  { id: 'flags', label: 'Flags', value: (row) => row.flags.join('; ') },
  { id: 'reasons', label: 'Reasons', value: (row, labels) => reasons(row, labels).join(' | ') },
  { id: 'seconds', label: 'Time (seconds)', value: (row) => row.seconds },
  { id: 'pages', label: 'Pages timed', value: (row) => row.pages },
  { id: 'text_responses', label: 'Open ends', value: (row) => row.text_responses },
  { id: 'text_quality', label: 'Open-end quality (0-100)', value: (row) => row.text_quality },
  { id: 'text_flagged', label: 'Open ends flagged', value: (row) => row.text_flagged },
  { id: 'flagged_answers', label: 'Flagged answers', value: (row) => row.text_details.filter((d) => d.flagged).map((d) => d.answer).join(' | ') },
  { id: 'fraud_score', label: 'Fraud score (0-1)', value: (row) => row.fraud_score },
  { id: 'fraud_risk', label: 'Fraud risk', value: (row) => row.fraud_risk },
  { id: 'duplicate', label: 'Duplicate', value: (row) => (row.duplicate ? 'yes' : 'no') },
  { id: 'straight_lining', label: 'Straight-lining', value: (row) => (row.straight_lining ? 'yes' : 'no') },
  { id: 'speeder', label: 'Speeder', value: (row) => (row.speeder ? 'yes' : 'no') },
  { id: 'events', label: 'Tracked events', value: (row) => row.events },
];
const DEFAULT_COLUMNS = ['respondent_id', 'started', 'status', 'flags', 'reasons', 'seconds', 'text_quality', 'fraud_score'];
const TABLE_LIMIT = 500;

function statusText(row) {
  if (row.status === 'in_progress') return 'In survey';
  if (row.status === 'dropped') return 'Not finished';
  if (row.verdict === 'bot') return 'Bot-like';
  return row.flags.length ? 'Review' : 'Looks human';
}

function statusTone(row) {
  if (row.status !== 'checked') return row.status === 'in_progress' ? 'accent' : 'neutral';
  if (row.verdict === 'bot') return 'danger';
  return row.flags.length ? 'warn' : 'success';
}

/** The bot engine's own "Bot detected: …" sentence, without its method-by-method details. */
function botSentence(explanation) {
  const found = /Bot detected:\s*([^\n]+)/i.exec(explanation || '');
  return found ? found[1].trim().replace(/\.?$/, '.') : '';
}

/** Plain-language reasons behind a respondent's flags. labels: code → label maps from the rules. */
function reasons(row, labels = {}) {
  const out = [];
  if (row.verdict === 'bot') {
    const signals = (row.bot_signals || []).map((code) => labels.signals?.[code] || code.replace(/_/g, ' '));
    if (signals.length) out.push(`Behaviour: ${signals.join('; ')}.`);
    else {
      const sentence = botSentence(row.explanation);
      const score = row.confidence != null ? ` (bot score ${Number(row.confidence).toFixed(2)})` : '';
      out.push(`Behaviour: ${sentence || 'movement, typing and timing looked automated.'}${score}`);
    }
  }
  if (row.timing_explanation) out.push(`Timing: ${row.timing_explanation}`);
  if (row.grid_explanation) out.push(`Grid: ${row.grid_explanation}`);
  const poor = row.text_details.filter((detail) => detail.flagged);
  if (poor.length) {
    const kinds = [...new Set(poor.flatMap((detail) => detail.reasons))]
      .map((code) => labels.texts?.[code] || code.replace(/_/g, ' '))
      .join(', ');
    out.push(`Open ends: ${poor.length} flagged${kinds ? ` (${kinds})` : ''}.`);
  }
  if (row.duplicate) out.push('Duplicate of another response.');
  if (row.fraud_reasons && Object.keys(row.fraud_reasons).length) {
    out.push(`Fraud signals: ${Object.keys(row.fraud_reasons).join(', ').replace(/_/g, ' ')}`);
  }
  return out;
}

function pickRows(rows, set) {
  if (set === 'flagged') return rows.filter((row) => row.flags.length > 0);
  if (set === 'bots') return rows.filter((row) => row.verdict === 'bot');
  if (set === 'checked') return rows.filter((row) => row.status === 'checked');
  return rows;
}

function share(part, whole) {
  return whole ? `${Math.round((100 * part) / whole)}%` : '0%';
}

function surveyName(item) {
  return item?.title && item.title !== item.survey_id ? item.title : item?.survey_id;
}

/** The period as ISO bounds for the API (custom dates cover whole local days). */
function bounds(period, from, to) {
  const preset = PERIODS.find((item) => item.id === period);
  if (preset?.hours) return { dateFrom: new Date(Date.now() - preset.hours * 3600 * 1000).toISOString(), dateTo: '' };
  if (period !== 'custom') return { dateFrom: '', dateTo: '' };
  return {
    dateFrom: from ? new Date(`${from}T00:00:00`).toISOString() : '',
    dateTo: to ? new Date(`${to}T23:59:59.999`).toISOString() : '',
  };
}

function periodText(report) {
  const { from, to } = report.period || {};
  if (!from && !to) return 'All time';
  if (from && to) return `${formatDateTime(from)} to ${formatDateTime(to)}`;
  return from ? `From ${formatDateTime(from)}` : `Up to ${formatDateTime(to)}`;
}

/** A few sentences that sum the report up; also what "Copy summary" copies. */
function summaryLines(report) {
  const t = report.totals;
  if (!t.sessions) return ['Nobody started this survey in the chosen period.'];
  const lines = [
    `${t.sessions} respondents started; ${t.checked} finished and were checked, ${t.in_progress} are still in the survey and ${t.dropped} did not finish.`,
    `${t.flagged} (${share(t.flagged, t.sessions)}) were flagged by at least one check, and ${t.bots} of those checked (${share(t.bots, t.checked)}) behaved like bots.`,
  ];
  const top = [...report.flag_counts].filter((item) => item.count > 0).sort((a, b) => b.count - a.count).slice(0, 3);
  if (top.length) lines.push(`Most common reasons: ${top.map((item) => `${item.flag.toLowerCase()} (${item.count})`).join(', ')}.`);
  if (report.text.responses) {
    lines.push(
      `${report.text.responses} open-ended answers were scored${report.text.avg_quality != null ? `, averaging ${Math.round(report.text.avg_quality)}/100` : ''}; ${report.text.flagged} (${share(report.text.flagged, report.text.responses)}) were flagged.`,
    );
  }
  if (!t.flagged) lines.push('No respondent was flagged.');
  return lines;
}

function csvCell(value) {
  if (value === null || value === undefined) return '';
  const text = String(value);
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function downloadCsv(name, rows, columns, labels) {
  const picked = COLUMNS.filter((column) => columns.includes(column.id));
  const lines = [picked.map((column) => csvCell(column.label)).join(',')];
  rows.forEach((row) => lines.push(picked.map((column) => csvCell(column.value(row, labels))).join(',')));
  // Reason: the byte-order mark makes Excel read accented and non-Latin text correctly.
  const blob = new Blob(['﻿' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function Section({ title, note, children }) {
  return (
    <section className="break-inside-avoid-page space-y-3">
      <div>
        <h3 className="text-base font-semibold text-gray-900">{title}</h3>
        {note && <p className="text-sm text-gray-500">{note}</p>}
      </div>
      {children}
    </section>
  );
}

function ChecksTable({ report }) {
  const t = report.totals;
  const r = report.rules;
  const datacentre = report.flag_counts.find((item) => item.flag === 'Data-centre IP')?.count || 0;
  const flatliners = report.flag_counts.find((item) => item.flag === 'Flatliner')?.count || 0;
  const pasted = report.flag_counts.find((item) => item.flag === 'Pasted answers')?.count || 0;
  const rows = [
    ['Bot-like behaviour', `Behaviour score of ${r.bot_threshold} or more, or one of ${r.bot_signals.length} enabled bot signals.`, `${t.bots} of ${t.checked} checked (${share(t.bots, t.checked)})`],
    ['Speeders', `Pages averaging under ${r.speeder_page_seconds} s${r.speeder_median_share ? `, or a total under ${Math.round(r.speeder_median_share * 100)}% of the median time` : ''}.`, `${t.speeders} (${share(t.speeders, t.sessions)})`],
    ['Flatliners', 'Answer timing too even to be a person reading.', `${flatliners} (${share(flatliners, t.sessions)})`],
    ['Straight-lining', `The same answer on every row of a grid with ${r.straightline_min_rows} or more rows.`, `${t.straight_liners} (${share(t.straight_liners, t.sessions)})`],
    ['Low-quality open ends', `Answers judged ${r.text_reasons.length ? r.text_reasons.map((code) => report.rules_state.text_reasons[code] || code).join(', ').toLowerCase() : 'poor'}.`, `${t.low_quality_text} respondents · ${report.text.flagged} of ${report.text.responses} answers`],
    ['Pasted answers', r.flag_pasted ? 'Open ends pasted in, or entered with no typing.' : 'Not counted (switched off in the rules).', `${pasted}`],
    ['Duplicates', r.flag_duplicates ? 'The same person or device answering more than once.' : 'Not counted (switched off in the rules).', `${t.duplicates}`],
    ['High fraud risk', `Fraud score of ${r.fraud_threshold} or more.`, `${report.fraud.high_risk}${report.fraud.avg_score != null ? ` · average score ${Number(report.fraud.avg_score).toFixed(2)}` : ''}`],
    ['Data-centre IP', r.flag_datacenter ? 'Connections from cloud or hosting networks rather than homes or phones.' : 'Not counted (switched off in the rules).', `${datacentre}`],
  ];
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="w-full min-w-[560px] text-sm">
        <thead className="bg-gray-50 text-left text-[11px] uppercase tracking-wide text-gray-500">
          <tr>
            <th className="px-3 py-2 font-medium">Check</th>
            <th className="px-3 py-2 font-medium">What counts</th>
            <th className="px-3 py-2 text-right font-medium">Found</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {rows.map(([name, rule, found]) => (
            <tr key={name}>
              <td className="whitespace-nowrap px-3 py-2 font-medium text-gray-900">{name}</td>
              <td className="px-3 py-2 text-gray-700">{rule}</td>
              <td className="whitespace-nowrap px-3 py-2 text-right tabular-nums text-gray-900">{found}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RespondentRows({ rows, labels }) {
  const shown = rows.slice(0, TABLE_LIMIT);
  if (!rows.length) return <p className="rounded-lg border border-dashed border-gray-300 px-4 py-6 text-center text-sm text-gray-500">No respondents match.</p>;
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="w-full min-w-[720px] text-sm">
        <thead className="bg-gray-50 text-left text-[11px] uppercase tracking-wide text-gray-500">
          <tr>
            <th className="px-3 py-2 font-medium">Respondent</th>
            <th className="px-3 py-2 font-medium">Started</th>
            <th className="px-3 py-2 font-medium">Status</th>
            <th className="px-3 py-2 text-right font-medium">Time</th>
            <th className="px-3 py-2 text-right font-medium">Text</th>
            <th className="px-3 py-2 font-medium">Flags and reasons</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 align-top">
          {shown.map((row) => (
            <tr className="break-inside-avoid" key={row.session_id}>
              <td className="px-3 py-2">
                <Link className="font-mono text-xs text-blue-700 hover:underline print:text-gray-900" to={`/sessions/${encodeURIComponent(row.session_id)}`}>
                  {row.respondent_id || row.session_id.slice(0, 8)}
                </Link>
              </td>
              <td className="whitespace-nowrap px-3 py-2 text-gray-700">{formatDateTime(row.started)}</td>
              <td className="px-3 py-2"><Badge tone={statusTone(row)}>{statusText(row)}</Badge></td>
              <td className="whitespace-nowrap px-3 py-2 text-right tabular-nums text-gray-700">{row.seconds ? `${Math.round(row.seconds)} s` : '–'}</td>
              <td className="whitespace-nowrap px-3 py-2 text-right tabular-nums text-gray-700">{row.text_quality != null ? Math.round(row.text_quality) : '–'}</td>
              <td className="px-3 py-2">
                {row.flags.length > 0 && (
                  <div className="mb-1 flex flex-wrap gap-1">
                    {row.flags.map((flag) => (
                      <Badge key={flag} tone={flag === 'Bot-like behaviour' || flag === 'Duplicate' ? 'danger' : 'warn'}>{flag}</Badge>
                    ))}
                  </div>
                )}
                <ul className="space-y-0.5 text-xs text-gray-600">
                  {reasons(row, labels).map((reason) => <li key={reason}>{reason}</li>)}
                </ul>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > TABLE_LIMIT && (
        <p className="border-t border-gray-200 px-3 py-2 text-xs text-gray-500">
          Showing the newest {TABLE_LIMIT} of {rows.length}. The CSV download has all of them.
        </p>
      )}
    </div>
  );
}

function Method({ report }) {
  const state = report.rules_state;
  const r = state.rules;
  const changed = new Set(state.changed);
  const survey = report.survey;
  const def = state.defaults;
  const item = (key, label, value, defaultValue) => (
    <li className="flex flex-wrap items-baseline justify-between gap-x-3 py-1.5" key={key}>
      <span className="text-gray-700">{label}</span>
      <span className="text-right text-gray-900">
        {value}
        {changed.has(key) && <span className="ml-2 text-xs text-amber-700">changed from {defaultValue}</span>}
      </span>
    </li>
  );
  const signals = r.bot_signals.map((code) => state.bot_signals[code] || code);
  const texts = r.text_reasons.map((code) => state.text_reasons[code] || code);
  const onOff = (value) => (value ? 'counted' : 'not counted');
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="rounded-lg border border-gray-200 p-4">
        <p className="text-sm font-semibold text-gray-900">
          Quality rules {changed.size ? <Badge tone="warn">Custom for this survey</Badge> : <Badge>Defaults</Badge>}
        </p>
        <ul className="mt-2 divide-y divide-gray-100 text-sm">
          {item('bot_threshold', 'Bot score threshold', r.bot_threshold, def.bot_threshold)}
          {item('bot_signals', 'Bot signals that count', signals.length ? signals.join(', ') : 'none', `${def.bot_signals.length} signals`)}
          {item('speeder_page_seconds', 'Speeder: seconds per page under', `${r.speeder_page_seconds} s`, `${def.speeder_page_seconds} s`)}
          {item('speeder_median_share', 'Speeder: share of median time under', r.speeder_median_share ? `${Math.round(r.speeder_median_share * 100)}%` : 'off', `${Math.round(def.speeder_median_share * 100)}%`)}
          {item('straightline_min_rows', 'Straight-lining: grid rows at least', r.straightline_min_rows, def.straightline_min_rows)}
          {item('text_reasons', 'Open-end problems that count', texts.length ? texts.join(', ') : 'none', 'all')}
          {item('flag_pasted', 'Pasted answers', onOff(r.flag_pasted), onOff(def.flag_pasted))}
          {item('fraud_threshold', 'Fraud score threshold', r.fraud_threshold, def.fraud_threshold)}
          {item('flag_duplicates', 'Duplicates', onOff(r.flag_duplicates), onOff(def.flag_duplicates))}
          {item('flag_datacenter', 'Data-centre IPs', onOff(r.flag_datacenter), onOff(def.flag_datacenter))}
        </ul>
      </div>
      <div className="space-y-3 rounded-lg border border-gray-200 p-4 text-sm text-gray-700">
        <p className="font-semibold text-gray-900">How this survey is tracked</p>
        {survey.tracked ? (
          <ul className="space-y-1">
            <li>Tracking added on this platform{survey.tracked_since ? ` on ${formatDateTime(survey.tracked_since)}` : ''}{survey.platform ? ` for ${survey.platform}` : ''}.</li>
            {survey.decipher_path && <li>Decipher survey: <span className="font-mono">{survey.decipher_path}</span></li>}
            <li>{survey.terminates_bots ? 'Clear bots are ended inside the survey.' : 'Bots are flagged, not ended, inside the survey.'}</li>
            <li>{survey.privacy_notice ? 'Respondents see a short privacy notice.' : 'No privacy notice is shown by the tracker.'}</li>
          </ul>
        ) : (
          <p>This survey was tracked with code added by hand or through the API, so its tracking settings are not stored here.</p>
        )}
        <p className="font-semibold text-gray-900">How to read this</p>
        <p>
          The tracker records how each respondent moves, types and pauses, and their answers are checked when they finish. Each check above
          can flag someone; a flag means &quot;worth a look&quot;, not proof. Respondents still in the survey or who did not finish are counted as
          started but not checked. Numbers are live and can change while fieldwork runs.
        </p>
      </div>
    </div>
  );
}

const ReportBuilder = () => {
  const [params, setParams] = useSearchParams();
  const [surveys, setSurveys] = useState([]);
  const [listError, setListError] = useState('');
  const [surveyId, setSurveyId] = useState(params.get('survey') || '');
  const [period, setPeriod] = useState('all');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [sections, setSections] = useState(SECTIONS.map((item) => item.id));
  const [rowSet, setRowSet] = useState('flagged');
  const [columns, setColumns] = useState(DEFAULT_COLUMNS);
  const [report, setReport] = useState(null);
  const [builtAt, setBuiltAt] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    liveQualityService
      .listSurveys()
      .then((data) => setSurveys(data.surveys || []))
      .catch((err) => setListError(errorText(err, 'The survey list could not be loaded.')));
  }, []);

  const customInvalid = period === 'custom' && from && to && from > to;

  const build = async () => {
    if (!surveyId || customInvalid) return;
    setLoading(true);
    setError('');
    try {
      const data = await liveQualityService.getReport(surveyId, bounds(period, from, to));
      setReport(data);
      setBuiltAt(new Date().toISOString());
      setParams({ survey: surveyId }, { replace: true });
    } catch (err) {
      setError(errorText(err, 'The report could not be built.'));
    } finally {
      setLoading(false);
    }
  };

  const rows = useMemo(() => (report ? pickRows(report.respondents, rowSet) : []), [report, rowSet]);
  const labels = useMemo(
    () => ({ signals: report?.rules_state.bot_signals || {}, texts: report?.rules_state.text_reasons || {} }),
    [report],
  );
  const has = (id) => sections.includes(id);
  const toggle = (list, setList, id) => setList(list.includes(id) ? list.filter((item) => item !== id) : [...list, id]);
  const title = report ? surveyName(report.survey) : '';
  const fileStem = (report?.survey.survey_id || 'survey').replace(/[^\w-]+/g, '_').slice(0, 60);

  const copySummary = async () => {
    const text = [`${title} – quality report (${periodText(report)})`, ...summaryLines(report)].join('\n');
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError('Copying is blocked in this browser. Select the summary text and copy it instead.');
    }
  };

  const chip = (active) =>
    clsx(
      'rounded-full border px-3 py-1 text-sm transition-colors',
      active ? 'border-blue-600 bg-blue-50 font-medium text-blue-700' : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50',
    );

  return (
    <div className="space-y-6">
      <div className="print:hidden">
        <PageHeader
          description="Build a quality report for one survey: the same live results and quality rules as Live Quality, for the period you choose. Print it, save it as PDF, or download the respondents as CSV."
          title="Reports"
        />
      </div>

      <Card className="print:hidden" title="Build a report">
        {listError && <ErrorBanner>{listError}</ErrorBanner>}
        <div className="grid gap-5 lg:grid-cols-2">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-900" htmlFor="report-survey">Survey</label>
              <select className={clsx(inputClass, 'mt-1')} id="report-survey" onChange={(event) => setSurveyId(event.target.value)} value={surveyId}>
                <option value="">Choose a survey…</option>
                {surveys.map((item) => (
                  <option key={item.survey_id} value={item.survey_id}>
                    {surveyName(item)} · {item.sessions} started{item.tracked ? '' : ' · not tracked here'}
                  </option>
                ))}
              </select>
            </div>
            <fieldset>
              <legend className="text-sm font-medium text-gray-900">Period (by when respondents started)</legend>
              <div className="mt-2 flex flex-wrap gap-2">
                {PERIODS.map((item) => (
                  <button aria-pressed={period === item.id} className={chip(period === item.id)} key={item.id} onClick={() => setPeriod(item.id)} type="button">
                    {item.label}
                  </button>
                ))}
              </div>
              {period === 'custom' && (
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <label className="text-xs font-medium text-gray-700">
                    From
                    <input className={clsx(inputClass, 'mt-1')} onChange={(event) => setFrom(event.target.value)} type="date" value={from} />
                  </label>
                  <label className="text-xs font-medium text-gray-700">
                    To
                    <input className={clsx(inputClass, 'mt-1')} onChange={(event) => setTo(event.target.value)} type="date" value={to} />
                  </label>
                  {customInvalid && <p className="col-span-2 text-xs text-red-700">The start date is after the end date.</p>}
                </div>
              )}
            </fieldset>
            <fieldset>
              <legend className="text-sm font-medium text-gray-900">Respondents to list and download</legend>
              <div className="mt-2 flex flex-wrap gap-2">
                {ROW_SETS.map((item) => (
                  <button aria-pressed={rowSet === item.id} className={chip(rowSet === item.id)} key={item.id} onClick={() => setRowSet(item.id)} type="button">
                    {item.label}
                  </button>
                ))}
              </div>
            </fieldset>
          </div>
          <fieldset>
            <legend className="text-sm font-medium text-gray-900">Sections</legend>
            <div className="mt-2 grid gap-1.5 sm:grid-cols-2">
              {SECTIONS.map((item) => (
                <label className="flex cursor-pointer items-start gap-2 rounded-md border border-gray-200 px-3 py-2 hover:bg-gray-50" key={item.id}>
                  <input checked={has(item.id)} className="mt-0.5" onChange={() => toggle(sections, setSections, item.id)} type="checkbox" />
                  <span>
                    <span className="block text-sm text-gray-900">{item.label}</span>
                    <span className="block text-xs text-gray-500">{item.note}</span>
                  </span>
                </label>
              ))}
            </div>
            <details className="mt-3 rounded-md border border-gray-200 px-3 py-2">
              <summary className="cursor-pointer text-sm text-gray-900">CSV columns ({columns.length} of {COLUMNS.length})</summary>
              <div className="mt-2 grid gap-1 sm:grid-cols-2">
                {COLUMNS.map((column) => (
                  <label className="flex items-center gap-2 text-sm text-gray-700" key={column.id}>
                    <input checked={columns.includes(column.id)} onChange={() => toggle(columns, setColumns, column.id)} type="checkbox" />
                    {column.label}
                  </label>
                ))}
              </div>
            </details>
          </fieldset>
        </div>
        <div className="mt-5 flex flex-wrap items-center gap-2 border-t border-gray-100 pt-4">
          <Button disabled={!surveyId || loading || customInvalid} icon={BarChart3} onClick={build} variant="primary">
            {loading ? 'Building…' : report ? 'Rebuild report' : 'Build report'}
          </Button>
          {report && (
            <>
              <Button disabled={!rows.length || !columns.length} icon={Download} onClick={() => downloadCsv(`report-${fileStem}.csv`, rows, columns, labels)}>
                Download CSV ({rows.length})
              </Button>
              <Button icon={Printer} onClick={() => window.print()}>Print or save as PDF</Button>
              <Button icon={ClipboardCopy} onClick={copySummary}>{copied ? 'Copied' : 'Copy summary'}</Button>
              <Link className="ml-auto inline-flex items-center gap-1 text-sm text-blue-700 hover:underline" to={`/quality?survey=${encodeURIComponent(report.survey.survey_id)}`}>
                Open in Live Quality <ExternalLink aria-hidden="true" className="h-3.5 w-3.5" />
              </Link>
            </>
          )}
        </div>
      </Card>

      {error && <div className="print:hidden"><ErrorBanner onRetry={surveyId ? build : undefined}>{error}</ErrorBanner></div>}
      {loading && !report && <Loading label="Building the report…" />}

      {!report && !loading && (
        <div className="print:hidden">
          <EmptyState icon={FileText} title="No report yet">
            Choose a survey and a period, pick the sections you want, and select Build report.
          </EmptyState>
        </div>
      )}

      {report && (
        <article className="space-y-8 rounded-xl border border-gray-200 bg-white p-6 shadow-sm print:border-0 print:p-0 print:shadow-none" aria-label="Report">
          <header className="border-b border-gray-200 pb-4">
            <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Survey quality report</p>
            <h2 className="mt-1 text-2xl font-semibold text-gray-900">{title}</h2>
            <p className="mt-1 text-sm text-gray-600">
              {title !== report.survey.survey_id && <>Survey id <span className="font-mono">{report.survey.survey_id}</span> · </>}
              {periodText(report)} · built {formatDateTime(builtAt)} ·{' '}
              {report.rules_state.changed.length ? 'custom quality rules' : 'default quality rules'}
            </p>
          </header>

          {has('summary') && (
            <Section title="Summary">
              <div className="space-y-1.5 text-sm leading-relaxed text-gray-800">
                {summaryLines(report).map((line) => <p key={line}>{line}</p>)}
              </div>
            </Section>
          )}

          {has('headline') && (
            <Section title="Headline numbers">
              <KpiGrid results={report} />
            </Section>
          )}

          {(has('flags') || has('trend') || has('text')) && report.totals.sessions > 0 && (
            <div className="grid gap-4 lg:grid-cols-2 print:grid-cols-2">
              {has('flags') && <FlagsChart note="Respondents with each flag; one person can have several." results={report} />}
              {has('trend') && <StartsChart results={report} />}
              {has('text') && <QualityChart results={report} />}
            </div>
          )}

          {has('checks') && (
            <Section note="Each respondent can be flagged by several checks." title="Checks in detail">
              <ChecksTable report={report} />
            </Section>
          )}

          {has('respondents') && (
            <Section note={`${ROW_SETS.find((item) => item.id === rowSet).label}: ${rows.length} of ${report.totals.sessions} respondents, newest first.`} title="Respondents">
              <RespondentRows labels={labels} rows={rows} />
            </Section>
          )}

          {has('method') && (
            <Section title="Rules and method">
              <Method report={report} />
            </Section>
          )}

          <footer className="border-t border-gray-200 pt-3 text-xs text-gray-500">
            Built from live results{report.updated_at && toDate(report.updated_at) ? ` as of ${formatDateTime(report.updated_at)}` : ''}. Flags mark respondents worth a
            look; they are not proof of fraud on their own.
          </footer>
        </article>
      )}
    </div>
  );
};

export default ReportBuilder;
