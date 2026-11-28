// Manual setup: step-by-step instructions for adding bot detection by hand to a Decipher
// survey, a Qualtrics survey, any other survey platform, your own web pages, or the API.
// The code blocks come from the running service (GET /tracking/decipher/snippet and
// GET /tracking/script.js), so they match what the automatic "Add tracking" upload adds.

import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import clsx from 'clsx';
import { Check, Code2, Copy, ExternalLink, FileCode2, Globe, LayoutTemplate, ListChecks } from 'lucide-react';
import { trackingService } from '../services/apiService';
import { config } from '../config/config';
import { Card, ErrorBanner, Loading, PageHeader, apiError, buttonClass, inputClass } from './ui';

// Same rule as the service (decipher_tracking.check_survey_id).
const SURVEY_ID = /^[\w .()&',+:-]{1,100}$/;
const validSurveyId = (id) => SURVEY_ID.test(id.trim()) && !id.includes('--');

const PLATFORMS = [
  { key: 'decipher', label: 'Decipher', note: 'Survey XML', icon: FileCode2 },
  { key: 'qualtrics', label: 'Qualtrics', note: 'Header + survey flow', icon: LayoutTemplate },
  { key: 'other', label: 'Other survey platforms', note: 'Any tool that allows JavaScript', icon: ListChecks },
  { key: 'web', label: 'Your own web pages', note: 'HTML you host', icon: Globe },
  { key: 'api', label: 'API', note: 'Your own tracker or server', icon: Code2 },
];

// Results the tracker writes. "Marker" is the data-field value for the span method.
const RESULT_FIELDS = [
  ['QOS_RESPONDENT', 'respondent', 'Text', 'Respondent id (Decipher: uuid; elsewhere your id or one the tracker makes)'],
  ['QOS_SESSION', 'session', 'Text', 'Session id in this service'],
  ['QOS_FLAG', 'flag', 'Text', 'human, bot or unknown'],
  ['QOS_SCORE', 'score', 'Text', 'Overall score 0–1 with decimals (higher is worse)'],
  ['QOS_RISK', 'risk', 'Text', 'Risk level'],
  ['QOS_STATUS', 'QOS_STATUS', 'Whole number', '1 human, 2 suspect, 3 bot'],
  ['QOS_BEHAV', 'QOS_BEHAV', 'Whole number', 'Behaviour bot score 0–100'],
  ['QOS_OES', 'QOS_OES', 'Whole number', 'Open-end quality 0–100 (higher is better)'],
  ['QOS_FRAUD', 'QOS_FRAUD', 'Whole number', 'Fraud score 0–100'],
  ['QOS_DUP', 'QOS_DUP', 'Whole number', 'Duplicate respondent: 1 yes, 0 no'],
  ['QOS_DUP_SCORE', 'QOS_DUP_SCORE', 'Whole number', 'Duplicate score 0–100'],
  ['QOS_IP_RISK', 'QOS_IP_RISK', 'Whole number', 'IP address risk 0–100'],
  ['QOS_DEVICE_RISK', 'QOS_DEVICE_RISK', 'Whole number', 'Device reuse risk 0–100'],
  ['QOS_GEO_RISK', 'QOS_GEO_RISK', 'Whole number', 'Location mismatch risk 0–100'],
  ['QOS_VELOCITY', 'QOS_VELOCITY', 'Whole number', 'Survey-taking velocity risk 0–100'],
  ['QOS_DATACENTER', 'QOS_DATACENTER', 'Whole number', 'Data centre, VPN or proxy IP: 1 yes, 0 no'],
  ['QOS_SPEEDER', 'QOS_SPEEDER', 'Whole number', 'Pages answered too fast'],
  ['QOS_STRAIGHTLINE', 'QOS_STRAIGHTLINE', 'Whole number', 'Straight-lined grid questions'],
  ['QOS_FLAGCOUNT', 'QOS_FLAGCOUNT', 'Whole number', 'Number of quality reasons'],
  ['QOS_REASON', 'QOS_REASON', 'Whole number', 'Main reason code (0 none)'],
  ['QOS_REASONS', 'QOS_REASONS', 'Text', 'All reason codes, comma separated'],
];

// ---------- small building blocks ----------

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  };
  return (
    <button className={buttonClass('secondary', 'sm')} disabled={!text} onClick={copy} type="button">
      {copied ? <Check aria-hidden="true" className="h-3.5 w-3.5 text-green-600" /> : <Copy aria-hidden="true" className="h-3.5 w-3.5" />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  );
}

function CodeBlock({ title, code, tall = false }) {
  return (
    <div className="mt-3 overflow-hidden rounded-lg border border-gray-200">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-200 bg-gray-50 px-3 py-2">
        <span className="text-xs font-medium text-gray-700">{title}</span>
        <CopyButton text={code} />
      </div>
      <pre className={clsx('overflow-auto bg-gray-900 p-3 text-xs leading-relaxed text-gray-100', tall ? 'max-h-72' : 'max-h-96')}>
        <code className="whitespace-pre">{code}</code>
      </pre>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className="space-y-3">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-500">{title}</h3>
      {children}
    </section>
  );
}

function Steps({ children }) {
  return <ol className="list-decimal space-y-5 pl-5 text-sm text-gray-700 marker:font-semibold marker:text-gray-500">{children}</ol>;
}

function Checklist({ items }) {
  return (
    <ul className="space-y-1.5 text-sm text-gray-700">
      {items.map((item, index) => (
        <li className="flex gap-2" key={index}>
          <Check aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-green-600" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

function Note({ tone = 'info', children }) {
  const tones = {
    info: 'border-blue-200 bg-blue-50 text-blue-900',
    warn: 'border-amber-200 bg-amber-50 text-amber-900',
  };
  return <div className={clsx('rounded-lg border px-4 py-3 text-sm', tones[tone])}>{children}</div>;
}

const C = ({ children }) => <code className="rounded bg-gray-100 px-1 py-0.5 text-xs text-gray-800">{children}</code>;
const A = ({ to, children }) => <Link className="font-medium text-blue-700 underline" to={to}>{children}</Link>;

function NeedId() {
  return <Note tone="warn">Enter a survey id at the top of the page to get the code for this survey.</Note>;
}

// Checking in the browser works the same on every platform.
function BrowserCheck() {
  return (
    <li>
      <strong>Check it in the browser.</strong> Open the survey with a test link, press <C>F12</C> (or right-click → Inspect) and open the{' '}
      <em>Console</em> tab. Type <C>QOSTracker.sessionId()</C> and press Enter: it shows a session id once the tracker is running. Nothing
      there, or red errors mentioning <C>/detection/sessions</C>, means the script did not load or could not reach the service.
    </li>
  );
}

// ---------- platform guides ----------

function DecipherGuide({ surveyId, valid }) {
  const [snippet, setSnippet] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!valid) {
      setSnippet(null);
      return undefined;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    // Reason: wait until typing pauses so each key press doesn't fetch the script.
    const timer = setTimeout(async () => {
      try {
        const data = await trackingService.getDecipherSnippet(surveyId.trim(), config.trackerApiBase);
        if (!cancelled) setSnippet(data);
      } catch (err) {
        if (!cancelled) setError(apiError(err, 'Could not build the Decipher code.'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 400);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [surveyId, valid]);

  return (
    <div className="space-y-8">
      <Note>
        <strong>Prefer not to edit XML?</strong> Upload the survey file on <A to="/tracking">Add tracking</A>. It adds the same two blocks,
        checks the file against Decipher&apos;s rules first, can add a privacy notice and an in-survey bot check, and can send the file
        straight to Decipher.
      </Note>

      <Section title="Before you start">
        <Checklist
          items={[
            'Edit access to the survey in Decipher, and its XML (the XML editor, or the survey.xml file).',
            <>A copy of the current XML, so you can go back. Make the change on a test copy of the survey if it is already live.</>,
            <>The opening <C>&lt;survey&gt;</C> tag uses <C>compat</C> 143 or higher (Decipher refuses lower), and <C>delphi=&quot;1&quot;</C> when <C>compat</C> is 151 or higher.</>,
            <>No questions of your own whose label starts with <C>QOS_</C>; those labels are used by the results questions.</>,
          ]}
        />
      </Section>

      <Section title="Steps">
        <Steps>
          <li>
            <strong>Find where block 1 goes.</strong> Search the XML for <C>&lt;/samplesources&gt;</C>. Block 1 goes on the line right after it.
            If the survey has no <C>&lt;samplesources&gt;</C> section, put block 1 right after the opening <C>&lt;survey ...&gt;</C> tag
            (after its closing <C>&gt;</C>).
          </li>
          <li>
            <strong>Paste block 1, the tracker.</strong> It is a <C>respview.client.js</C> style with <C>mode=&quot;after&quot;</C>, so it adds to any
            scripts the survey already has instead of replacing them, and it runs on every page. It uses Decipher&apos;s <C>uuid</C> as the
            respondent id, the same value as the <C>uuid</C> column in Decipher&apos;s data. Paste it unchanged: Decipher reads dollar signs in
            styles, and the block has exactly one on purpose (<C>{'${uuid}'}</C>).
            {!valid && <div className="mt-3"><NeedId /></div>}
            {error && <div className="mt-3"><ErrorBanner>{error}</ErrorBanner></div>}
            {loading && !snippet && <Loading label="Building the code…" />}
            {snippet && <CodeBlock code={snippet.style} tall title="Block 1 — tracker (after </samplesources>)" />}
          </li>
          <li>
            <strong>Paste block 2, the results questions,</strong> on the line right before the closing <C>&lt;/survey&gt;</C>. It is a short thank-you
            line and 21 optional <C>QOS_</C> questions. They sit on the survey&apos;s last page; the tracker hides them, runs the final check when
            that page opens and fills them in, so the results reach Decipher&apos;s data. Because they are optional, they never stop a respondent.
            {snippet && <CodeBlock code={snippet.results_page} tall title="Block 2 — results questions (before </survey>)" />}
          </li>
          <li>
            <strong>Save.</strong> If Decipher refuses the file, read its message: it is almost always the <C>compat</C>/<C>delphi</C> rule above, or
            a paste in the wrong place (inside another element).
          </li>
          <BrowserCheck />
          <li>
            <strong>Run a test response</strong> to the end. Within a few seconds it shows on <A to="/quality">Live Quality</A> under{' '}
            <C>{valid ? surveyId.trim() : 'your survey id'}</C>, and the test record in Decipher&apos;s data has <C>QOS_FLAG</C>, <C>QOS_SESSION</C>{' '}
            and the other values.
          </li>
        </Steps>
      </Section>

      <Section title="Later">
        <ul className="list-disc space-y-1.5 pl-5 text-sm text-gray-700">
          <li>Keep the same survey id for the whole fieldwork; a new id starts a separate survey on Live Quality.</li>
          <li>To remove tracking, delete the two blocks. Your own questions are untouched.</li>
          <li>Respondents whose values are empty (the service was slow): use <em>Add flags to a data file</em> on Live Quality with Decipher&apos;s export; it matches on <C>uuid</C>.</li>
        </ul>
        {snippet && (
          <p className="text-xs text-gray-500">
            The tracker calls <C>{snippet.api_base}</C>.{' '}
            {snippet.signed ? 'The code carries a signed token for this survey id.' : 'Survey tokens are not configured, so the code is unsigned.'}
          </p>
        )}
      </Section>
    </div>
  );
}

function QualtricsGuide({ surveyId, valid, scriptUrl }) {
  const header = `<script src="${scriptUrl('qualtrics')}"></script>`;
  return (
    <div className="space-y-8">
      <Note tone="warn">
        Not yet tried in a live Qualtrics survey: the tracker was tested on plain web pages. Send one test response and check that{' '}
        <C>QOS_SESSION</C> is filled in your data before you launch.
      </Note>

      <Section title="Before you start">
        <Checklist
          items={[
            'Edit access to the survey (Survey flow and Look and feel).',
            <>A layout other than <strong>Simple</strong>. Qualtrics does not run custom JavaScript in the Simple layout; Flat, Modern and Classic run it.</>,
            'The survey id you will use on Live Quality.',
          ]}
        />
      </Section>

      <Section title="Steps">
        <Steps>
          <li>
            <strong>Declare two embedded data fields.</strong> Open <em>Survey flow</em>, add an <em>Embedded Data</em> element, move it to the very top,
            and add the fields <C>QOS_SESSION</C> and <C>QOS_RESPONDENT</C> with no value. Save the flow. Qualtrics only keeps embedded data that
            the survey flow declares, so without this step the ids never reach your data.
          </li>
          <li>
            <strong>Add the script to the header.</strong> Go to <em>Look and feel → General → Header</em>, click <em>edit</em>, switch the editor to its
            HTML/source view, paste the line below and save. The header is on every page, so the tracker runs on every page; it writes the
            session id and its respondent id into the two embedded data fields.
            {valid ? <CodeBlock code={header} title="Survey header" /> : <div className="mt-3"><NeedId /></div>}
          </li>
          <BrowserCheck />
          <li>
            <strong>Run a test response</strong> to the end. It shows on <A to="/quality">Live Quality</A> under <C>{valid ? surveyId.trim() : 'your survey id'}</C>,
            and in <em>Data &amp; Analysis</em> the response has <C>QOS_SESSION</C> filled.
          </li>
        </Steps>
      </Section>

      <Section title="Getting the results into your data">
        <p className="text-sm text-gray-700">
          Qualtrics stores the two ids; the verdicts are added afterwards. Export the responses (SPSS .sav, CSV or Excel), open the survey on{' '}
          <A to="/quality">Live Quality</A> and use <em>Add flags to a data file</em>. Each record is matched on <C>QOS_SESSION</C> and you get the same
          file back with <C>LQ_</C> flag variables. A Qualtrics CSV has two extra header rows; they just get empty flag columns.
        </p>
        <p className="text-xs text-gray-500">A Qualtrics API token in Settings is not needed for this.</p>
      </Section>
    </div>
  );
}

function OtherPlatformGuide({ surveyId, valid, scriptUrl }) {
  const tag = `<script src="${scriptUrl('web')}"></script>`;
  const withId = `<script>
  // Your platform's respondent id, written in by its piping or variable syntax.
  // Letters, digits, - and _ only, 4 to 64 characters; anything else is ignored.
  window.QOS_RESPONDENT_ID = "REPLACE_WITH_YOUR_PLATFORM_RESPONDENT_ID";
</script>
${tag}`;
  const marker = `<span class="qos-bot-field" data-field="flag"></span>Quality check result (leave blank)`;
  return (
    <div className="space-y-8">
      <p className="text-sm text-gray-700">
        Any survey tool works if it lets you add a script that runs in the respondent&apos;s browser on every page. The setup always has the same
        three parts: <strong>the tracker on every page</strong>, <strong>a survey id</strong> (in the script address), and <strong>a way to get the
        results back</strong> into your data.
      </p>

      <Section title="Before you start">
        <Checklist
          items={[
            <>Find where your tool accepts custom HTML or JavaScript. It is often called a header or footer, custom theme or template, page HTML, or JavaScript on a question. You need one place that is on every page, or the same code on a question on every page.</>,
            <>Check that it allows a <C>&lt;script src=&quot;…&quot;&gt;</C> tag that loads a file from another site. Some hosted tools do not allow custom JavaScript at all; those cannot run the tracker (use the API from your own system instead).</>,
            'The survey id you will use on Live Quality.',
          ]}
        />
      </Section>

      <Section title="Steps">
        <Steps>
          <li>
            <strong>Add the tracker to every page.</strong> Paste this line into the place you found. If the tool only runs code per question, add it
            to one question on each page; loading it again on later pages is fine, as the tracker keeps one session while the respondent stays in
            the same browser tab.
            {valid ? <CodeBlock code={tag} title="Every page" /> : <div className="mt-3"><NeedId /></div>}
          </li>
          <li>
            <strong>Optional: use your tool&apos;s respondent id.</strong> If the tool can write its respondent id into the page (piping, merge
            fields, variables), set it before the script. Then results here use the same id as your data. Without it the tracker makes its own id.
            {valid && <CodeBlock code={withId} title="Every page, with your respondent id" />}
          </li>
          <li>
            <strong>Choose how results get back into your data</strong> (one of these):
            <div className="mt-3 space-y-3">
              <div className="rounded-lg border border-gray-200 p-3">
                <p className="font-medium text-gray-900">A. Results questions on the last page (results land in your data)</p>
                <p className="mt-1">
                  Add open text questions on the last page for the values you want (at least <C>QOS_FLAG</C> and <C>QOS_SESSION</C>; the full
                  list is below). The tracker finds them in either of two ways, and fills them when the page opens:
                </p>
                <ul className="mt-2 list-disc space-y-1 pl-5">
                  <li>the input&apos;s HTML name is the variable name, e.g. <C>QOS_FLAG</C> (works when your tool uses your variable name in the page); or</li>
                  <li>the question text contains a marker span (works when your tool keeps HTML in question text):</li>
                </ul>
                <CodeBlock code={marker} title="Question text for QOS_FLAG" />
                <p className="mt-2 text-xs text-gray-500">
                  Use the <em>Marker</em> value from the table below in <C>data-field</C>. Questions found by the marker are hidden from respondents;
                  a question found only by its name stays visible (with a &quot;leave blank&quot; title), so use the marker where your tool keeps HTML.
                  A question your tool hides by not drawing it at all can&apos;t be filled. Make all of them optional, and use text questions for <C>QOS_SCORE</C> and <C>QOS_REASONS</C> (they are not whole numbers).
                </p>
              </div>
              <div className="rounded-lg border border-gray-200 p-3">
                <p className="font-medium text-gray-900">B. No extra questions (add results afterwards)</p>
                <p className="mt-1">
                  Keep step 2 so the tracker uses your tool&apos;s respondent id. After fieldwork, export your data, rename the respondent id column
                  to <C>QOS_RESPONDENT</C>, and use <em>Add flags to a data file</em> on <A to="/quality">Live Quality</A>. You get the file back with{' '}
                  <C>LQ_</C> flag variables.
                </p>
              </div>
            </div>
          </li>
          <BrowserCheck />
          <li>
            <strong>Run a test response</strong> to the end. It shows on <A to="/quality">Live Quality</A> under{' '}
            <C>{valid ? surveyId.trim() : 'your survey id'}</C>; with option A, the test record in your data has the <C>QOS_</C> values.
          </li>
        </Steps>
      </Section>
    </div>
  );
}

function WebGuide({ valid, scriptUrl }) {
  const everyPage = `<!-- In the <head> of every page -->
<script>
  // Optional: your own respondent id (letters, digits, - and _, 4 to 64 characters).
  window.QOS_RESPONDENT_ID = "panel-12345";
</script>
<script src="${scriptUrl('web')}" async></script>`;
  const lastForm = `<!-- Last page: hidden fields inside your form. The tracker runs the final check when
     the page opens, fills them, and holds the submit (at most 3 seconds) until they are filled. -->
<form action="/submit" method="post">
  ...your last questions...
  <input type="hidden" name="QOS_RESPONDENT">
  <input type="hidden" name="QOS_SESSION">
  <input type="hidden" name="QOS_FLAG">
  <input type="hidden" name="QOS_SCORE">
  <input type="hidden" name="QOS_STATUS">
  <input type="hidden" name="QOS_REASONS">
  <button type="submit">Finish</button>
</form>`;
  const inScript = `// Without a form: run the final check yourself and use the result
QOSTracker.finish().then(function (result) {
  // result.flag: "human", "bot" or "unknown"; result.score: 0-1; result.risk
  // result.session_id, result.respondent_id, result.variables (QOS_STATUS, QOS_FRAUD, ...)
});

// Or listen for it anywhere on the page
document.addEventListener("qos:result", function (event) { console.log(event.detail); });`;
  return (
    <div className="space-y-8">
      <p className="text-sm text-gray-700">
        For surveys or forms you build and host yourself. The tracker records typing, mouse, scrolling and time per page, finds open-ended
        answers and grids, adds an invisible honeypot field, and keeps one session while the respondent moves between pages in the same tab. It
        never stops a page from submitting.
      </p>
      {!valid && <NeedId />}
      {valid && (
        <Section title="Steps">
          <Steps>
            <li>
              <strong>Add the tracker to every page</strong> of the survey.
              <CodeBlock code={everyPage} title="Every page" />
            </li>
            <li>
              <strong>On the last page, collect the results with your form.</strong> Add hidden inputs named after the variables you want; they
              are submitted with the rest of the answers.
              <CodeBlock code={lastForm} title="Last page" />
            </li>
            <li>
              <strong>Or read the result in your own script</strong> instead of hidden inputs.
              <CodeBlock code={inScript} title="Reading the result" />
            </li>
            <BrowserCheck />
          </Steps>
        </Section>
      )}
    </div>
  );
}

function ApiGuide({ surveyId, valid }) {
  const id = encodeURIComponent(valid ? surveyId.trim() : 'my-survey');
  const base = config.trackerApiBase;
  const curl = `# 1. Start a session (one per respondent)
curl -X POST "${base}/detection/sessions?survey_id=${id}&respondent_id=resp-001&platform_id=web"
# -> {"session_id": "…", "status": "active", ...}

# 2. Send events in batches (at most 500 per request)
curl -X POST "${base}/detection/sessions/SESSION_ID/events" \\
  -H "Content-Type: application/json" \\
  -d '[{"event_type": "page_load",   "timestamp": "2026-11-26T10:00:00.000Z"},
       {"event_type": "mouse_move",  "timestamp": "2026-11-26T10:00:01.200Z", "x": 120, "y": 340},
       {"event_type": "keystroke",   "timestamp": "2026-11-26T10:00:02.050Z", "key": "char"},
       {"event_type": "mouse_click", "timestamp": "2026-11-26T10:00:03.400Z", "x": 125, "y": 350}]'

# 3. Run the full check (behaviour, grids, timing, text and fraud)
curl -X POST "${base}/detection/sessions/SESSION_ID/composite-analyze"
# -> {"is_bot": false, "composite_score": 0.24, "risk_level": "LOW", "survey_variables": {...}, ...}

# Latest verdict at any time
curl "${base}/detection/sessions/SESSION_ID/status"`;
  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-700">
        For your own tracker or a server-side integration. Event types the service keeps: <C>keystroke</C>, <C>mouse_move</C>, <C>mouse_click</C>,{' '}
        <C>mouse_drag</C>, <C>scroll</C>, <C>focus</C>, <C>blur</C>, <C>page_load</C>, <C>form_submit</C>. Each event needs <C>event_type</C> and an ISO{' '}
        <C>timestamp</C> from the last 7 days; other events are skipped.
      </p>
      <CodeBlock code={curl} title="Shell (curl)" />
      <p className="text-sm text-gray-700">
        Use the real times of the events. Open-ended answers go to <C>POST /text-analysis/questions</C> and <C>POST /text-analysis/responses</C>.
        Try any endpoint on the <A to="/api-playground">API Playground</A> or in the{' '}
        <a className="inline-flex items-center gap-1 font-medium text-blue-700 underline" href={config.trackerApiDocsUrl} rel="noopener noreferrer" target="_blank">
          interactive API docs <ExternalLink aria-hidden="true" className="h-3 w-3" />
        </a>
        .
      </p>
    </div>
  );
}

// ---------- page ----------

export default function ManualSetup() {
  const [params, setParams] = useSearchParams();
  const platform = PLATFORMS.some((item) => item.key === params.get('platform')) ? params.get('platform') : 'decipher';
  const [surveyId, setSurveyId] = useState('');
  const valid = validSurveyId(surveyId);

  const scriptUrl = useMemo(
    () => (kind) => `${config.trackerApiBase}/tracking/script.js?survey_id=${encodeURIComponent(surveyId.trim())}&platform=${kind}`,
    [surveyId],
  );

  const choose = (key) => setParams({ platform: key }, { replace: true });
  const current = PLATFORMS.find((item) => item.key === platform);

  return (
    <div className="space-y-6">
      <PageHeader
        description="Step-by-step instructions for adding bot and fraud checks to a survey by hand. Pick where the survey runs, enter its survey id, and copy the code built for it."
        title="Manual setup"
      />

      <Card>
        <label className="text-sm font-medium text-gray-900" htmlFor="manual-survey-id">1. Survey id</label>
        <p className="mb-2 mt-0.5 text-xs text-gray-500">
          The name responses are grouped under on Live Quality. Up to 100 letters, digits, spaces and . ( ) &amp; &apos; , + : _ -
        </p>
        <input
          aria-invalid={surveyId !== '' && !valid}
          className={clsx(inputClass, 'max-w-md')}
          id="manual-survey-id"
          onChange={(event) => setSurveyId(event.target.value)}
          placeholder="e.g. Coffee study W1"
          value={surveyId}
        />
        {surveyId !== '' && !valid && <p className="mt-1 text-xs text-red-600">This id has characters the tracker can&apos;t use.</p>}
        <p className="mt-2 text-xs text-gray-500">
          All code on this page sends respondents&apos; data to <C>{config.trackerApiBase}</C>.
        </p>

        <p className="mt-5 text-sm font-medium text-gray-900">2. Where does the survey run?</p>
        <div className="mt-2 grid gap-2 sm:grid-cols-2 lg:grid-cols-5" role="tablist">
          {PLATFORMS.map((item) => {
            const Icon = item.icon;
            const active = item.key === platform;
            return (
              <button
                aria-selected={active}
                className={clsx(
                  'flex items-start gap-2 rounded-lg border px-3 py-2.5 text-left',
                  active ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500' : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50',
                )}
                key={item.key}
                onClick={() => choose(item.key)}
                role="tab"
                type="button"
              >
                <Icon aria-hidden="true" className={clsx('mt-0.5 h-4 w-4 shrink-0', active ? 'text-blue-600' : 'text-gray-400')} />
                <span className="min-w-0">
                  <span className="block text-sm font-medium text-gray-900">{item.label}</span>
                  <span className="block text-xs text-gray-500">{item.note}</span>
                </span>
              </button>
            );
          })}
        </div>
      </Card>

      <Card title={`3. ${current.label}`} description={current.note}>
        <div role="tabpanel">
          {platform === 'decipher' && <DecipherGuide surveyId={surveyId} valid={valid} />}
          {platform === 'qualtrics' && <QualtricsGuide scriptUrl={scriptUrl} surveyId={surveyId} valid={valid} />}
          {platform === 'other' && <OtherPlatformGuide scriptUrl={scriptUrl} surveyId={surveyId} valid={valid} />}
          {platform === 'web' && <WebGuide scriptUrl={scriptUrl} valid={valid} />}
          {platform === 'api' && <ApiGuide surveyId={surveyId} valid={valid} />}
        </div>
      </Card>

      <Card description="Names for results questions or hidden inputs, and the marker value for the span method" title="Result variables">
        <div className="relative overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-gray-200 bg-gray-50 text-left text-xs font-medium text-gray-500">
              <tr>
                <th className="px-3 py-2 font-medium">Variable</th>
                <th className="px-3 py-2 font-medium">Marker</th>
                <th className="px-3 py-2 font-medium">Type</th>
                <th className="px-3 py-2 font-medium">Meaning</th>
              </tr>
            </thead>
            <tbody>
              {RESULT_FIELDS.map(([name, markerValue, type, meaning]) => (
                <tr className="border-b border-gray-100 last:border-0" key={name}>
                  <td className="px-3 py-2 font-mono text-xs text-gray-800">{name}</td>
                  <td className="px-3 py-2 font-mono text-xs text-gray-600">{markerValue}</td>
                  <td className="whitespace-nowrap px-3 py-2 text-gray-600">{type}</td>
                  <td className="px-3 py-2 text-gray-600">{meaning}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-gray-500">
          On Live Quality, <em>Add flags to a data file</em> adds the results as <C>LQ_</C> variables under the survey&apos;s own rules, matching on{' '}
          <C>QOS_SESSION</C>, then <C>QOS_RESPONDENT</C>, then Decipher&apos;s <C>uuid</C>.
        </p>
      </Card>

      <Card title="If something doesn't work">
        <dl className="grid gap-4 text-sm md:grid-cols-2">
          <div>
            <dt className="font-medium text-gray-900">Nothing appears on Live Quality</dt>
            <dd className="text-gray-600">
              Use the browser check above. Usual causes: the script is not on the page, an ad blocker or the platform&apos;s
              Content-Security-Policy blocks the service, or the survey id is typed differently.
            </dd>
          </div>
          <div>
            <dt className="font-medium text-gray-900">Decipher won&apos;t save the XML</dt>
            <dd className="text-gray-600">
              Usually <C>compat</C> below 143, or 151 and higher without <C>delphi=&quot;1&quot;</C>. <A to="/tracking">Add tracking</A> reports these
              before anything is sent.
            </dd>
          </div>
          <div>
            <dt className="font-medium text-gray-900">QOS_ values are empty for some respondents</dt>
            <dd className="text-gray-600">
              The last page waits at most 3 seconds for the check; if the service was slow or unreachable, the respondent goes on. Their result is
              still on Live Quality, and <em>Add flags to a data file</em> fills it in.
            </dd>
          </div>
          <div>
            <dt className="font-medium text-gray-900">Results split across two surveys</dt>
            <dd className="text-gray-600">The survey id changed during fieldwork. Use one id from the first test to the last complete.</dd>
          </div>
        </dl>
      </Card>
    </div>
  );
}
