// Quality rules editor: what counts as a bot, a speeder, a poor answer, or fraud for one survey.

import React, { useEffect, useState } from 'react';
import { RotateCcw, SlidersHorizontal } from 'lucide-react';
import { liveQualityService } from '../../services/apiService';
import { Badge, errorText } from './QualityParts';

/** What each decisive bot signal means, in plain words. Keys match the backend's BOT_SIGNALS. */
const SIGNAL_DETAIL = {
  automation: 'The browser reports that software is driving it (for example Selenium or a headless browser).',
  scripted_input: 'Clicks and key presses were produced by code, not by a real mouse, touch screen or keyboard.',
  no_input: 'Pages were answered with no mouse, touch or keyboard activity at all.',
  honeypot: "A field hidden from people was filled in. A person can't see it; a form-filling bot does.",
  untyped_answers: 'Text appeared in an open end without any typing, as when a script fills the box.',
  timeline_mismatch: 'The browser reported more time on the pages than had actually passed on our server. Real page times cannot add up to more than the real time, so these were made up.',
  robotic_timing: 'Keys were pressed at exactly the same interval in several answers, or the mouse moved in ruler-straight lines at a constant speed. People vary; scripts on a timer do not.',
};

/** What each open-end reason means. Keys match the backend's TEXT_REASONS. */
const REASON_DETAIL = {
  gibberish: 'Random letters or keyboard mashing, such as “asdfgh”.',
  generic: 'An answer that fits any question, such as “good”, “nothing” or “n/a”.',
  irrelevant: "Doesn't answer the question that was asked.",
  copy_paste: 'The same text repeated across questions or respondents.',
  low_quality: 'Too short or careless to be useful.',
};

const button = 'inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50';
const primary = `${button} bg-blue-600 text-white hover:bg-blue-700`;
const secondary = `${button} border border-gray-300 bg-white text-gray-800 hover:bg-gray-50`;
const ghost = `${button} text-gray-700 hover:bg-gray-100`;

/** Rules card for one survey. ``onSaved`` is called after a save or reset so results reload. */
export default function QualityRulesCard({ surveyId, onSaved }) {
  const [state, setState] = useState(null);
  const [draft, setDraft] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setState(null);
    setDraft(null);
    setError('');
    if (!surveyId) return;
    liveQualityService.getRules(surveyId).then(setState).catch((err) => setError(errorText(err, 'The rules could not be loaded.')));
  }, [surveyId]);

  if (error && !state) return <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</p>;
  if (!state) return null;
  const rules = state.rules;
  const editing = draft !== null;

  async function run(action) {
    setBusy(true);
    setError('');
    try {
      setState(await action());
      setDraft(null);
      if (onSaved) onSaved();
    } catch (err) {
      setError(errorText(err, 'The rules were not saved.'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-labelledby="quality-rules-title" className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
          <SlidersHorizontal aria-hidden="true" className="h-5 w-5" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="flex flex-wrap items-center gap-2 text-sm font-semibold text-gray-900" id="quality-rules-title">
            Quality rules
            {state.changed.length === 0 ? <Badge>Defaults</Badge> : <Badge tone="accent">{state.changed.length} changed</Badge>}
          </h3>
          <p className="mt-0.5 text-sm text-gray-600">
            What counts as a bot, a speeder, a poor answer, or fraud for this survey. The dashboard, the CSV export and the
            LQ_ variables follow these rules as soon as you save.
          </p>
        </div>
        {!editing && (
          <button className={secondary} onClick={() => setDraft({ ...rules })} type="button">
            Edit rules
          </button>
        )}
      </div>

      {error && <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</p>}

      {!editing && <RulesSummary rules={rules} state={state} />}

      {editing && (
        <form
          className="mt-4 space-y-5"
          onSubmit={(event) => {
            event.preventDefault();
            run(() => liveQualityService.saveRules(surveyId, draft));
          }}
        >
          <RulesGuide state={state} />

          <Group title="Bot detection">
            <NumberField
              defaultValue={state.defaults.bot_threshold}
              help="Behaviour score (0 looks human, 1 almost certainly a bot) at which a respondent is flagged. Lower is stricter and flags more real people; higher only catches clear cases."
              label="Bot score threshold"
              max={0.99}
              min={0.3}
              onChange={(value) => setDraft({ ...draft, bot_threshold: value })}
              step={0.05}
              value={draft.bot_threshold}
            />
            <Checklist
              details={SIGNAL_DETAIL}
              help="Any of these marks a respondent as a bot, whatever the score."
              label="Signals that always mean bot"
              labels={state.bot_signals}
              onChange={(value) => setDraft({ ...draft, bot_signals: value })}
              value={draft.bot_signals}
            />
          </Group>

          <Group title="Speed and attention">
            <NumberField
              defaultValue={state.defaults.speeder_page_seconds}
              help="Average seconds per page below which a respondent is a speeder."
              label="Speeder: seconds per page"
              max={60}
              min={0.5}
              onChange={(value) => setDraft({ ...draft, speeder_page_seconds: value })}
              step={0.5}
              value={draft.speeder_page_seconds}
            />
            <NumberField
              defaultValue={state.defaults.speeder_median_share}
              help="Also a speeder when total time is under this share of the median (0 turns it off; needs 5 checked respondents)."
              label="Speeder: share of median time"
              max={0.9}
              min={0}
              onChange={(value) => setDraft({ ...draft, speeder_median_share: value })}
              step={0.05}
              value={draft.speeder_median_share}
            />
            <NumberField
              defaultValue={state.defaults.straightline_min_rows}
              help="Same answer on every row of a grid with at least this many rows."
              label="Straight-lining: minimum grid rows"
              max={30}
              min={2}
              onChange={(value) => setDraft({ ...draft, straightline_min_rows: value })}
              step={1}
              value={draft.straightline_min_rows}
            />
          </Group>

          <Group title="Open-ended answers">
            <Checklist
              details={REASON_DETAIL}
              help="Answers the text check flags for these reasons count as low quality."
              label="Low-quality reasons"
              labels={state.text_reasons}
              onChange={(value) => setDraft({ ...draft, text_reasons: value })}
              value={draft.text_reasons}
            />
            <Toggle
              checked={draft.flag_pasted}
              label="Flag mostly pasted answers, or text that appeared without typing"
              onChange={(value) => setDraft({ ...draft, flag_pasted: value })}
            />
          </Group>

          <Group title="Fraud">
            <NumberField
              defaultValue={state.defaults.fraud_threshold}
              help="Fraud score (0 to 1, from repeat devices and networks, matching answers, and disguised locations) at which a respondent is flagged as high risk."
              label="High fraud risk threshold"
              max={0.99}
              min={0.3}
              onChange={(value) => setDraft({ ...draft, fraud_threshold: value })}
              step={0.05}
              value={draft.fraud_threshold}
            />
            <Toggle
              checked={draft.flag_duplicates}
              label="Flag duplicate respondents (the same person or device taking the survey again)"
              onChange={(value) => setDraft({ ...draft, flag_duplicates: value })}
            />
            <Toggle
              checked={draft.flag_datacenter}
              label="Flag connections from cloud data centres (bot farms, many VPNs)"
              onChange={(value) => setDraft({ ...draft, flag_datacenter: value })}
            />
          </Group>

          <p className="text-xs text-gray-500">
            Ending the survey on a clear bot signal and the privacy notice are chosen when you add tracking to the Decipher
            XML (Add Tracking). The QOS_ variables written into the Decipher data use the service&apos;s standard scoring; these
            rules apply here and to the LQ_ variables.
          </p>

          <div className="flex flex-wrap items-center gap-2">
            <button className={primary} disabled={busy} type="submit">{busy ? 'Saving…' : 'Save rules'}</button>
            <button className={ghost} disabled={busy} onClick={() => setDraft(null)} type="button">Cancel</button>
            <span className="flex-1" />
            <button className={ghost} disabled={busy} onClick={() => setDraft({ ...state.defaults })} type="button">
              <RotateCcw aria-hidden="true" className="h-3.5 w-3.5" />
              Fill in defaults
            </button>
            {state.changed.length > 0 && (
              <button className={ghost} disabled={busy} onClick={() => run(() => liveQualityService.resetRules(surveyId))} type="button">
                Reset to defaults
              </button>
            )}
          </div>
        </form>
      )}
    </section>
  );
}

function RulesSummary({ rules, state }) {
  const signalTotal = Object.keys(state.bot_signals).length;
  const reasonTotal = Object.keys(state.text_reasons).length;
  const median = rules.speeder_median_share ? Math.round(rules.speeder_median_share * 100) : 0;
  const items = [
    {
      term: 'Bot',
      setting: `score ≥ ${rules.bot_threshold}, or any of ${rules.bot_signals.length} decisive signals${rules.bot_signals.length < signalTotal ? ` (of ${signalTotal})` : ''}`,
      meaning: 'Flagged when how they type, click and move looks automated, or a signal only a bot gives fires.',
    },
    {
      term: 'Speeder',
      setting: `under ${rules.speeder_page_seconds} s a page${median ? `, or under ${median}% of the median time` : ''}`,
      meaning: median
        ? `Too fast to have read the questions. With a median of 10 minutes, anyone under ${(10 * median) / 100} minutes is flagged.`
        : 'Too fast to have read the questions.',
    },
    {
      term: 'Straight-lining',
      setting: `same answer on every row of a grid with ${rules.straightline_min_rows}+ rows`,
      meaning: 'Picking one column all the way down usually means they stopped reading.',
    },
    {
      term: 'Open ends',
      setting: `${rules.text_reasons.length} of ${reasonTotal} low-quality reasons count${rules.flag_pasted ? '; pasted answers flagged' : ''}`,
      meaning: 'Each typed answer is checked for gibberish, generic or off-topic text.',
    },
    {
      term: 'Fraud',
      setting: `score ≥ ${rules.fraud_threshold}${rules.flag_duplicates ? '; duplicates flagged' : ''}${rules.flag_datacenter ? '; data-centre IPs flagged' : ''}`,
      meaning: 'Catches the same person or device taking the survey more than once, or hiding where they connect from.',
    },
  ];
  return (
    <>
      <dl className="mt-3 grid gap-x-6 gap-y-2.5 text-sm lg:grid-cols-2">
        {items.map(({ term, setting, meaning }) => (
          <div className="flex gap-2" key={term}>
            <dt className="w-28 shrink-0 text-gray-500">{term}</dt>
            <dd className="min-w-0">
              <span className="text-gray-900">{setting}</span>
              <span className="mt-0.5 block text-xs text-gray-500">{meaning}</span>
            </dd>
          </div>
        ))}
      </dl>
      <RulesGuide state={state} />
    </>
  );
}

/** Collapsible explanation of every check and how to pick a setting. */
function RulesGuide({ state }) {
  const d = state.defaults;
  const strong = 'font-medium text-gray-900';
  return (
    <details className="mt-3 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm">
      <summary className="cursor-pointer font-medium text-gray-900">How the checks work, and how to choose</summary>
      <div className="mt-2 space-y-3 text-gray-700">
        <p>
          While people take the survey, the tracker records how they answer: typing, mouse and touch movement, scrolling,
          time on each page, grid answers and open-end text. Each respondent gets the checks below. A flag marks them on the
          dashboard and in the exports; it doesn&apos;t remove anyone from your data.
        </p>
        <GuideSection title="Scores run from 0 to 1">
          <p>
            0 means the respondent looks entirely human or genuine, 1 means almost certainly a bot or fraud. A respondent is
            flagged when their score reaches the threshold. Under 0.5 counts as low risk, 0.5 to 0.7 medium, 0.7 and over high.
          </p>
          <p>
            <strong className={strong}>Lower threshold</strong> (for example 0.5): stricter, catches more bots, but flags more
            real people. <strong className={strong}>Higher threshold</strong> (for example 0.85): only the clearest cases, so
            fewer false alarms but more bots get through. The default, {d.bot_threshold}, suits most studies. Go lower for a
            panel known to have bot problems or a high incentive; go higher for a small or hard-to-reach sample where losing a
            real respondent is costly.
          </p>
        </GuideSection>
        <GuideSection title="Bot behaviour">
          <p>
            The bot score comes from how the respondent behaves: whether typing rhythm, mouse paths and timings look like a
            person&apos;s. Some signals are decisive: any one you tick flags the respondent as a bot, whatever their score.
          </p>
          <ul className="list-disc space-y-0.5 pl-5">
            {Object.entries(state.bot_signals).map(([code, label]) => (
              <li key={code}><span className="text-gray-900">{label}.</span> {SIGNAL_DETAIL[code] || ''}</li>
            ))}
          </ul>
        </GuideSection>
        <GuideSection title="Speeders and straight-lining">
          <p>
            <strong className={strong}>Speeder</strong>: average time per page is under the limit (default {d.speeder_page_seconds} s),
            or total time is under a share of the median respondent&apos;s time (default {Math.round(d.speeder_median_share * 100)}%).
            The median check starts once 5 respondents have been checked. Raise the seconds for long or text-heavy pages; set the
            share to 0 to turn the median check off.
          </p>
          <p>
            <strong className={strong}>Straight-lining</strong>: the same answer on every row of a grid with at least the set
            number of rows (default {d.straightline_min_rows}). Raise it if short grids where everyone could honestly agree are
            being flagged.
          </p>
          <p>
            <strong className={strong}>Flatliner</strong> (always shown): the time between answers is unnaturally even, as when a
            script answers at a fixed pace.
          </p>
        </GuideSection>
        <GuideSection title="Open-ended answers">
          <p>Each typed answer is checked, and flagged for any reason you tick:</p>
          <ul className="list-disc space-y-0.5 pl-5">
            {Object.entries(state.text_reasons).map(([code, label]) => (
              <li key={code}><span className="text-gray-900">{label}.</span> {REASON_DETAIL[code] || ''}</li>
            ))}
          </ul>
          <p>
            <strong className={strong}>Pasted answers</strong>: most of the answer was pasted in or appeared without typing.
            Untick it if respondents are asked to paste something, such as a link.
          </p>
        </GuideSection>
        <GuideSection title="Fraud">
          <p>
            The fraud score (0 to 1, default threshold {d.fraud_threshold}) looks at the device and connection: the same device or
            network seen many times, matching answers from different sessions, and disguised locations.
          </p>
          <ul className="list-disc space-y-0.5 pl-5">
            <li><span className="text-gray-900">Duplicate respondents.</span> The same person or device has already taken this survey.</li>
            <li>
              <span className="text-gray-900">Data-centre connections.</span> The connection comes from a cloud server rather than a
              home or mobile network. Bot farms use them, and so do many VPNs, so some real people are caught too.
            </li>
          </ul>
        </GuideSection>
      </div>
    </details>
  );
}

function GuideSection({ title, children }) {
  return (
    <section className="space-y-1.5">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">{title}</h4>
      {children}
    </section>
  );
}

function Group({ title, children }) {
  return (
    <fieldset className="space-y-3 rounded-lg border border-gray-200 p-3">
      <legend className="px-1 text-xs font-semibold uppercase tracking-wide text-gray-500">{title}</legend>
      {children}
    </fieldset>
  );
}

function NumberField({ label, help, value, defaultValue, min, max, step, onChange }) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-gray-900">{label}</span>
      {value !== defaultValue && <span className="ml-2 text-xs text-gray-500">default {defaultValue}</span>}
      <span className="mt-0.5 block text-xs text-gray-500">{help}</span>
      <input
        className="mt-1 h-8 w-28 rounded-md border border-gray-300 bg-white px-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        max={max}
        min={min}
        onChange={(event) => {
          const next = Number(event.target.value);
          if (!Number.isNaN(next)) onChange(next);
        }}
        step={step}
        type="number"
        value={value}
      />
    </label>
  );
}

function Toggle({ label, checked, onChange }) {
  return (
    <label className="flex items-center gap-2 text-sm text-gray-800">
      <input checked={checked} className="h-4 w-4 accent-blue-600" onChange={(event) => onChange(event.target.checked)} type="checkbox" />
      {label}
    </label>
  );
}

function Checklist({ label, help, labels, details, value, onChange }) {
  return (
    <fieldset className="text-sm">
      <legend className="font-medium text-gray-900">{label}</legend>
      <p className="text-xs text-gray-500">{help}</p>
      <div className="mt-1 grid gap-1 sm:grid-cols-2">
        {Object.entries(labels).map(([code, text]) => (
          <label className="flex items-start gap-2 text-gray-800" key={code}>
            <input
              checked={value.includes(code)}
              className="mt-0.5 h-4 w-4 shrink-0 accent-blue-600"
              onChange={(event) => onChange(event.target.checked ? [...value, code] : value.filter((item) => item !== code))}
              type="checkbox"
            />
            <span>
              {text}
              {details && details[code] && <span className="block text-xs text-gray-500">{details[code]}</span>}
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
