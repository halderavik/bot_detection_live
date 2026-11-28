// How every check works: the rules, thresholds and formulas the service uses.
// Numbers here mirror the backend code (file names are shown per section); update both together.

import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, PageHeader } from './ui';

const SECTIONS = [
  ['flow', 'How a respondent is checked'],
  ['behaviour', 'Behaviour checks'],
  ['score', 'Combining the behaviour checks'],
  ['signals', 'Signals that always mean bot'],
  ['openends', 'Open-ended answers'],
  ['grids', 'Grids and speed'],
  ['fraud', 'Fraud and duplicates'],
  ['verdict', 'The final verdict'],
  ['livequality', 'Live Quality flags'],
  ['data', 'Values written into the survey data'],
];

function Formula({ children }) {
  return (
    <pre className="my-2 overflow-x-auto rounded-lg bg-gray-50 px-3 py-2 font-mono text-[13px] leading-relaxed text-gray-800">
      {children}
    </pre>
  );
}

function Source({ children }) {
  return <p className="mt-3 text-xs text-gray-500">Code: <span className="font-mono">{children}</span></p>;
}

function Table({ head, rows }) {
  return (
    <div className="my-2 overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-xs text-gray-500">
            {head.map((h) => <th key={h} className="py-2 pr-4 font-medium">{h}</th>)}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 text-gray-700">
          {rows.map((row, i) => (
            <tr key={i}>{row.map((cell, j) => <td key={j} className="py-2 pr-4 align-top">{cell}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Section({ id, title, description, children }) {
  return (
    <div id={id} className="scroll-mt-20">
      <Card title={title} description={description}>
        <div className="space-y-2 text-sm leading-relaxed text-gray-700">{children}</div>
      </Card>
    </div>
  );
}

const RELIABILITY = { keystroke: 0.5, mouse: 0.45, timing: 0.35, device: 0.4 };
const OLD_WEIGHTS = { keystroke: 0.3, mouse: 0.25, timing: 0.2, device: 0.15 };
const LABELS = { keystroke: 'Keyboard', mouse: 'Mouse', timing: 'Timing', device: 'Device' };

/** Try the behaviour score: the current combination next to the earlier weighted average. */
function ScoreCalculator() {
  const [scores, setScores] = useState({ keystroke: 1, mouse: 1, timing: 0, device: 0 });
  const result = useMemo(() => {
    const noisyOr = 1 - Object.entries(scores).reduce((left, [k, s]) => left * (1 - RELIABILITY[k] * s), 1);
    const weights = Object.values(OLD_WEIGHTS).reduce((a, b) => a + b, 0);
    const average = Object.entries(scores).reduce((sum, [k, s]) => sum + OLD_WEIGHTS[k] * s, 0) / weights;
    return { noisyOr, average };
  }, [scores]);
  return (
    <div className="mt-3 rounded-lg border border-gray-200 p-4">
      <div className="text-xs font-medium text-gray-500">Try it: set each check's score</div>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        {Object.keys(scores).map((k) => (
          <label key={k} className="block text-sm">
            <span className="flex justify-between"><span>{LABELS[k]}</span><span className="font-mono">{scores[k].toFixed(2)}</span></span>
            <input
              type="range" min="0" max="1" step="0.05" value={scores[k]}
              onChange={(e) => setScores({ ...scores, [k]: Number(e.target.value) })}
              className="mt-1 w-full accent-blue-600"
              aria-label={`${LABELS[k]} score`}
            />
          </label>
        ))}
      </div>
      <div className="mt-3 flex flex-wrap gap-6 text-sm">
        <div>Behaviour score now: <span className={`font-mono font-semibold ${result.noisyOr >= 0.7 ? 'text-red-600' : 'text-gray-900'}`}>{result.noisyOr.toFixed(3)}</span>{result.noisyOr >= 0.7 ? ' (bot at the default 0.7)' : ''}</div>
        <div className="text-gray-500">Earlier weighted average: <span className="font-mono">{result.average.toFixed(3)}</span></div>
      </div>
    </div>
  );
}

export default function HowChecksWork() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="How the checks work"
        description="Every test the service runs on a respondent, with the exact rules, thresholds and formulas. Default values are shown; a survey's own quality rules (Live Quality → Edit rules) can change the ones marked “rule”."
      />

      <Card title="On this page">
        <nav className="grid gap-1 text-sm sm:grid-cols-2">
          {SECTIONS.map(([id, label], i) => (
            <a key={id} href={`#${id}`} onClick={(e) => { e.preventDefault(); document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }); }}
              className="rounded px-2 py-1 text-blue-700 hover:bg-blue-50">
              {i + 1}. {label}
            </a>
          ))}
        </nav>
      </Card>

      <Section id="flow" title="1. How a respondent is checked" description="What happens from the first page to the result">
        <ol className="list-decimal space-y-1 pl-5">
          <li>The tracker in the survey opens a <b>session</b> when the first page loads and records mouse moves (at most every 100 ms), clicks, key presses, focus, scrolling, page times and grid answers. It sends them in batches.</li>
          <li>Each open-ended answer is sent when the respondent leaves the box or the page; it is scored by the open-end check (section 5) straight away.</li>
          <li>On the last page the tracker asks for the <b>final check</b>: behaviour, grids, timing, open ends and fraud are judged together, and the result is written into hidden questions in the survey (section 10). The tracker waits at most 3 seconds for it.</li>
          <li>Live Quality and Reports re-judge the stored results under each survey's current rules every time they are opened, without changing what was stored.</li>
        </ol>
        <p>The tracker also adds an invisible <b>honeypot</b> box (“Leave this empty”, off-screen, not reachable with the Tab key, no name so Decipher never receives it). People never fill it; form-filling bots do.</p>
      </Section>

      <Section id="behaviour" title="2. Behaviour checks" description="Four checks, each giving a bot score from 0 (human) to 1 (bot)">
        <Table
          head={['Check', 'Rules', 'Score']}
          rows={[
            [<b key="k">Keyboard</b>, <>Fewer than 5 key presses: 0.3 (too few to judge). Otherwise, using only gaps under 2 s between key presses (at least 4 of them), count how many apply: gaps vary by less than 10 ms (standard deviation); gaps average under 50 ms (faster than people type); more than 80% of gaps are whole multiples of 10 ms (timer-made).</>, 'patterns ÷ 3'],
            [<b key="m">Mouse</b>, <>Phones and tablets (touch): 0.3. No mouse moves: 0.4 with key presses (keyboard users), 0.8 if pages were clicked or submitted, else 0.4. With 10+ points: +1 if every step has the same length (standard deviation under 1 px), +1 if the path never turns.</>, 'points ÷ 2'],
            [<b key="t">Timing</b>, <>Fewer than 5 events: 0.4. Otherwise count: whole session under 10 s; more than 50 events a second; gaps between events vary by less than 0.1 s.</>, 'patterns ÷ 3'],
            [<b key="d">Device</b>, <>Automation flag or a headless/automation browser name: 1.0. Otherwise: +1 if the screen size changed during the session, +1 if a screen side is 0, +0.5 if no screen size at all (not on touch).</>, 'points ÷ 2'],
          ]}
        />
        <p>Events the tracker sent twice (same type, time, element, position and key) count once. A grid page counts as one page.</p>
        <Source>backend/app/services/bot_detection_engine.py</Source>
      </Section>

      <Section id="score" title="3. Combining the behaviour checks" description="Agreeing evidence adds up">
        <p>Each check's score is multiplied by how much that check alone can say, and the result is the chance that at least one of them means “bot” (a noisy-OR):</p>
        <Formula>{'behaviour score = 1 − (1 − 0.5·keyboard) × (1 − 0.45·mouse) × (1 − 0.35·timing) × (1 − 0.4·device)'}</Formula>
        <p>One strong check is a lead, not a verdict: a perfect keyboard score alone gives 0.5. Two agreeing checks reach the bot line: perfect keyboard and mouse give 1 − 0.5 × 0.55 = <b>0.725</b>. (The earlier weighted average, 0.3·keyboard + 0.25·mouse + 0.2·timing + 0.15·device divided by 0.9, could only reach 0.61 with those two.)</p>
        <p>Then the signals in section 4 lift it: <b>one signal → at least 0.85</b>, <b>two or more different signals → at least 0.95</b>. The score before the lift is kept as <span className="font-mono">base_score</span>.</p>
        <Table head={['Behaviour score', 'Risk shown']} rows={[['0.9 or more', 'critical'], ['0.7 or more, or judged a bot', 'high'], ['0.5 to 0.7', 'medium'], ['under 0.5', 'low']]} />
        <ScoreCalculator />
        <Source>backend/app/utils/helpers.py (calculate_confidence_score, determine_risk_level)</Source>
      </Section>

      <Section id="signals" title="4. Signals that always mean bot" description="Patterns real people cannot produce. Each can be switched off per survey (rule).">
        <Table
          head={['Signal', 'Exact rule', 'Data code']}
          rows={[
            ['Automated or headless browser', 'The browser reports navigator.webdriver, or its name contains bot, crawler, spider, scraper, headless, phantomjs, puppeteer, playwright or selenium.', '1'],
            ['Clicks and key presses generated by script', 'At least 3 clicks or key presses were not real (isTrusted false), and they are at least half of all clicks and key presses.', '2'],
            ['Pages answered with no mouse or keyboard use', 'Desktop, 2+ pages, and either no mouse moves, clicks or key presses at all, or 3+ clicks with no mouse moves and no key presses.', '3'],
            ['Hidden honeypot field filled in', 'The invisible honeypot box had text when a page was submitted.', '4'],
            ['Open ends that appeared without typing', 'An answer of 20+ characters appeared with no input events at all (set by a script).', '5'],
            ['Typing or mouse movement with machine-exact timing', <>Typing: at least 3 separate stretches of 8+ letter keys (a stretch ends at a new field or a 2 s pause), and in every such stretch the gaps vary by under 3 ms. Holding a key such as Backspace never counts. Mouse: 30+ points, at least 3 ruler-straight runs of 4+ points with equal steps (steps of 10 px or more, within 1.5 px), covering at least 40% of the points.</>, '7'],
            ['Page times longer than the time the server saw', <>The page times the browser reports add up to 60 s or more, and exceed the time our server actually observed (from session start to the last event received) by more than 30 s or 25% of the reported time, whichever is larger. Page times are measured in the browser and can be faked; the server's clock cannot.</>, '8'],
          ]}
        />
        <Source>backend/app/services/bot_detection_engine.py (_decisive_signals, _robotic_timing, _timeline_mismatch)</Source>
      </Section>

      <Section id="openends" title="5. Open-ended answers" description="One AI check per answer, plus how it was entered">
        <p>Each answer is sent to OpenAI once, with the question, and five things are judged together: gibberish, copied or pre-written text, relevance to the question, generic low effort, and an overall quality score from 0 to 100.</p>
        <Table
          head={['Flag', 'When']}
          rows={[
            ['Gibberish', 'The AI says gibberish with confidence above 0.7'],
            ['Copied text', 'The AI says copied or pre-written with confidence 0.7 or more'],
            ['Off-topic', 'The AI says not relevant (risk = max(0.7, 1 − confidence)); a relevant answer has risk 1 − confidence, flagged at 0.7 or more'],
            ['Generic', 'The AI says generic with confidence above 0.7'],
            ['Low quality', 'Quality score under 30'],
            ['Too short', 'Under 3 characters (quality 0, no AI call)'],
          ]}
        />
        <p>Gibberish hides Generic and Low quality for the same answer; Off-topic hides Generic.</p>
        <p><b>How it was entered</b> (from the tracker's counts, for answers of 20+ characters): <b>Pasted</b> when at least half of it, and at least 20 characters, was pasted or dropped in; <b>No typing</b> when there were no input events at all.</p>
        <p><b>Not checked:</b> the service allows 300 AI requests a minute per server. When that is reached an answer waits up to 20 s for a slot. If it still cannot be checked, or OpenAI is unavailable, it is stored as <i>not checked</i>: no score, no flag, and never counted as an acceptable answer. Live Quality and the CSV count these (<span className="font-mono">text_unchecked</span>).</p>
        <Source>backend/app/services/text_analysis_service.py, backend/app/controllers/text_analysis_controller.py</Source>
      </Section>

      <Section id="grids" title="6. Grids and speed">
        <p><b>Straight-lining</b> (rule): the same answer on every row of a grid with at least 3 rows. Five of six rows alike is not straight-lining.</p>
        <p><b>Speeder</b> (rule), from the tracker's page times:</p>
        <Formula>{'speeder = (total seconds ÷ pages) < 3.5\n       or (5+ checked respondents and total seconds < 0.5 × median total)'}</Formula>
        <p><b>Per-answer timing</b> (shown in session details, not used for the speeder flag): an answer is fast when quicker than max(0.5 s, min(mean − 2 × standard deviation, 2 s)) and slow (“flatliner”) when longer than min(10 min, max(mean + 2 × standard deviation, 5 min)). An answer more than 2.5 standard deviations from the respondent's mean is an anomaly.</p>
        <p><b>Grid patterns</b> such as diagonals and zig-zags, and a satisficing score, are shown in session details only.</p>
        <Source>backend/app/services/live_quality.py (_mark_speeders), grid_analysis_service.py, timing_analysis_service.py</Source>
      </Section>

      <Section id="fraud" title="7. Fraud and duplicates" description="Repeat respondents, shared devices, copied answers and server addresses, within the same survey">
        <Formula>{'fraud score = (0.25·IP + 0.25·device + 0.20·duplicate answers + 0.15·velocity [+ 0.15·location])\n              ÷ (sum of the weights used)'}</Formula>
        <p>The location check needs an IP-to-country lookup, which is not set up yet, so it is left out of the sum rather than counted as 0.</p>
        <Table
          head={['Part', 'Score']}
          rows={[
            ['IP address (sessions from this address in the survey)', '10+ sessions or 5+ today: 0.8 · 5+ or 3+ today: 0.6 · 3+: 0.4 · 2: 0.2 · else 0. Halved when this device is not seen on any other session (a shared office or home network).'],
            ['Device (sessions with the same device fingerprint)', '5+: 0.9 · 3–4: 0.7 · 2: 0.5 · else 0. Halved when the other sessions are only on other networks (IPv4 /24, IPv6 /48), because identical phone models look alike.'],
            ['Duplicate answers (most similar open end of 20+ characters)', 'similarity 0.95+: 1.0 · 0.85+: 0.8 · 0.70+: 0.6 · else 0. Exact copies are searched across the whole survey, near copies among its latest 2,000 answers.'],
            ['Velocity (sessions in the last hour by device, respondent id, or IP when the device repeats)', '20+: 1.0 · 10+: 0.8 · 5+: 0.6 · 3+: 0.4 · else 0'],
            ['Location', 'Same respondent from different countries within an hour: 0.9 (not active yet)'],
          ]}
        />
        <p><b>Duplicate</b> when the fraud score is 0.7 or more. A <b>data-centre address</b> (published ranges of AWS, Google Cloud, Oracle Cloud and DigitalOcean) raises the fraud score to at least 0.75. Fraud risk: 0.9+ critical, 0.7+ high, 0.4+ medium, else low.</p>
        <p>Reasons named in the data when a part is high: IP reuse (0.6+), device reuse (0.5+), duplicate answers (0.6+), high velocity (0.6+), data-centre address.</p>
        <Source>backend/app/services/fraud_detection_service.py, backend/app/utils/fraud_helpers.py, backend/app/utils/ip_intel.py</Source>
      </Section>

      <Section id="verdict" title="8. The final verdict" description="Bot or human, and the combined score">
        <Formula>{'bot = behaviour score before the lift ≥ bot threshold (rule, default 0.7)\n      or any enabled signal from section 4 fired'}</Formula>
        <p>Only behaviour decides bot or human. Open ends, grids, speed and fraud are reported as their own flags, so a careless person is not called a bot. A bot's risk is at least “high”.</p>
        <p>A <b>combined score</b> is also reported for reference:</p>
        <Formula>{'combined = 0.4 · behaviour score + 0.3 · (1 − average open-end quality ÷ 100) + 0.3 · fraud score'}</Formula>
        <p>(with no checked open ends the quality part uses 50). Combined risk: 0.8+ critical, 0.6+ high, 0.4+ medium, else low. Whether the combined score alone reaches the threshold is kept as <span className="font-mono">composite_is_bot</span>; it does not change the verdict.</p>
        <Source>backend/app/controllers/detection_controller.py (composite-analyze), backend/app/services/live_quality.py (bot_verdict)</Source>
      </Section>

      <Section id="livequality" title="9. Live Quality flags" description="What each flag on the dashboard means">
        <Table
          head={['Flag', 'When']}
          rows={[
            ['Bot-like behaviour', 'The verdict in section 8'],
            ['Low-quality open ends', 'Any answer flagged for a reason the survey counts (rule: gibberish, generic, off-topic, copied, low effort)'],
            ['Pasted answers', 'Any answer flagged Pasted or No typing (rule: can be switched off)'],
            ['Straight-lining', 'Section 6'],
            ['Speeder', 'Section 6'],
            ['Flatliner', 'Answers far slower than usual (per-answer timing)'],
            ['Duplicate', 'Fraud score 0.7 or more (rule: can be switched off)'],
            ['High fraud risk', 'Fraud score at or above the fraud threshold (rule, default 0.7)'],
            ['Data-centre IP', 'Connected from a cloud server range (rule: can be switched off)'],
          ]}
        />
        <p>A respondent who opened the survey more than once has several sessions; they count as one respondent, and when results are added to a data file the checked session is used first, then the latest. A session that was never checked shows as in survey for 20 minutes after its last activity, then as dropped.</p>
        <p>Change these on <Link to="/quality" className="text-blue-700 hover:underline">Live Quality</Link> → Edit rules.</p>
      </Section>

      <Section id="data" title="10. Values written into the survey data" description="Hidden QOS_ questions filled on the last page, following the survey's rules">
        <Table
          head={['Variable', 'Meaning']}
          rows={[
            ['QOS_STATUS', '3 Bot (verdict in section 8) · 2 Suspect (any reason code below, or combined risk medium or higher) · 1 Human'],
            ['QOS_BEHAV', 'Behaviour score × 100'],
            ['QOS_OES', 'Average open-end quality (0–100, higher is better; blank if none were checked)'],
            ['QOS_FRAUD', 'Fraud score × 100'],
            ['QOS_DUP / QOS_DUP_SCORE', 'Duplicate reasons present (1/0) / highest of IP, device and duplicate-answer risk × 100'],
            ['QOS_IP_RISK, QOS_DEVICE_RISK, QOS_GEO_RISK, QOS_VELOCITY', 'Each fraud part × 100'],
            ['QOS_DATACENTER', '1 when the address is in a data-centre range'],
            ['QOS_SPEEDER', 'Number of pages faster than the seconds-per-page rule'],
            ['QOS_STRAIGHTLINE', 'Number of straight-lined grids'],
            ['QOS_REASON / QOS_REASONS / QOS_FLAGCOUNT', 'Most severe reason code / all codes / how many'],
          ]}
        />
        <Table
          head={['Code', 'Reason']}
          rows={[
            ['1', 'Automated or headless browser'], ['2', 'Clicks and key presses generated by script'], ['3', 'Pages answered with no mouse or keyboard use'],
            ['4', 'Hidden honeypot field filled in'], ['5', 'Open ends that appeared without typing'], ['6', 'Bot-like behaviour score'],
            ['7', 'Typing or mouse movement with machine-exact timing'], ['8', 'Page times longer than the time the server saw'],
            ['10', 'Data centre, VPN or proxy IP address'], ['11', 'Same device seen on other sessions of this survey'], ['12', 'Same IP address used repeatedly'],
            ['13', 'Answers copied from another respondent'], ['14', 'Many surveys started in a short time'], ['15', 'Same respondent seen from different countries within an hour'],
            ['20', 'Low-quality open-ended answers'], ['21', 'Straight-lined grid questions'], ['22', 'Pages answered too fast'],
          ]}
        />
        <p>These are written once, when the respondent finishes, under the rules in force at that moment. Live Quality and the LQ_ columns added to a data file always use the current rules.</p>
        <Source>backend/app/services/quality_variables.py</Source>
      </Section>
    </div>
  );
}
