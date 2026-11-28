// What the service collects and stores, what it never collects, and how to read the
// QOS_ variables in a Decipher SPSS export. Mirrors backend/app/assets/live_quality_tracker.js,
// backend/app/utils/privacy.py, backend/app/services/decipher_tracking.py and
// quality_variables.py; update both together. Example files: frontend/scripts/make_spss_example.py.

import React from 'react';
import { Check, Download, X } from 'lucide-react';
import { Card, PageHeader, buttonClass } from './ui';

const SECTIONS = [
  ['summary', 'In short'],
  ['collected', 'What we collect and store'],
  ['not-collected', 'What we never collect'],
  ['personal', 'How personal details are kept out'],
  ['where', 'Where the data goes'],
  ['spss', 'What the SPSS file contains'],
  ['codes', 'Reason codes'],
  ['read', 'How to read it'],
  ['example', 'Example files'],
];

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

const C = ({ children }) => <code className="rounded bg-gray-100 px-1 py-0.5 font-mono text-[12px] text-gray-800">{children}</code>;

function Note({ children }) {
  return <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">{children}</div>;
}

const COLLECTED = [
  ['Typed answers in text boxes', 'The full text typed into any text box (2 or more characters), with the question wording. That is mainly open ends, but also any other question the survey shows as a text box. Emails and phone numbers inside an answer are replaced by [email] and [phone] first.', 'The open-end quality check, duplicate answers'],
  ['Grid answers', 'For pages with 3 or more radio-button rows: the column position picked in each row (1, 2, 3 …), not the answer label.', 'Straight-lining'],
  ['Key presses', 'That a key was pressed and when. Letters, digits and symbols are all recorded as “char”; only keys like Backspace, Tab or Enter are kept by name. The characters themselves are not kept.', 'Typing rhythm, scripted input'],
  ['Mouse and touch', 'Click positions, mouse positions (at most every 100 ms), scrolling, and which box gained or lost focus.', 'Mouse checks, no-input and scripted-input signals'],
  ['Page timing', 'Time spent on each page as the browser reports it, and when our server received each event.', 'Speeders, timeline check'],
  ['How open ends were entered', 'Counts of characters typed, pasted and input events per answer (not the keys).', 'Pasted or untyped answers'],
  ['Device', 'Browser and operating system (user agent), screen and window size, time zone, browser languages, processor cores, memory, touch support, the browser’s “automated” flag, and two short codes describing how the device draws graphics.', 'Device checks, telling devices apart'],
  ['Network', 'The full IP address, the page that sent the respondent (referrer) and the survey page address, both without anything after ? or #.', 'IP reuse, data-centre IPs, velocity'],
  ['IDs', 'Decipher’s uuid (as the respondent id), the survey id, and a session id we create.', 'Linking results to your data'],
  ['Results', 'Every score, flag and reason the checks produce.', 'Dashboard, reports, SPSS variables'],
];

const NOT_COLLECTED = [
  'Answers to single-choice, multiple-choice and dropdown questions (apart from grid positions above).',
  'The characters a respondent types, except in the finished open-ended answer.',
  'Answers to text boxes that ask for contact or identity details: email address, phone number, name, street or home address, postcode or ZIP code, date of birth, social security or insurance number, passport or driver’s licence number.',
  'Password fields, and the hidden QOS_ boxes themselves.',
  'Anything after ? or # in page addresses (panel ids, respondent ids and tokens often travel there).',
  'Cookies. The session id is kept only in the browser tab while the survey is open.',
  'Anything outside the survey pages: other tabs, browsing history, files, location (GPS), camera or microphone.',
];

const TEXT_VARS = [
  ['QOS_RESPONDENT', 'Text', 'Respondent id. The same value as Decipher’s uuid.'],
  ['QOS_SESSION', 'Text', 'Our session id. Quote it when asking about a respondent.'],
  ['QOS_FLAG', 'Text', 'bot, human, or unknown (our check did not answer in time).'],
  ['QOS_SCORE', 'Text', 'Overall score from 0 to 1, higher is worse, for example 0.08. Stored as text: convert it before doing maths (the syntax file does this).'],
  ['QOS_RISK', 'Text', 'low, medium, high or critical.'],
  ['QOS_REASONS', 'Text', 'Every reason code that applied, comma-separated, for example 20,21,22. Empty when there are none.'],
];

const NUMBER_VARS = [
  ['QOS_STATUS', '1, 2, 3', '1 human, 2 suspect (at least one quality reason but not a bot), 3 bot.'],
  ['QOS_BEHAV', '0–100', 'Behaviour bot score. Higher is worse.'],
  ['QOS_OES', '0–100', 'Average open-ended answer quality. Higher is better. Blank when there were no open ends or they could not be checked.'],
  ['QOS_FRAUD', '0–100', 'Overall fraud score. Higher is worse.'],
  ['QOS_DUP', '0, 1', '1 when the respondent looks like a duplicate (same device, repeated IP, or copied answers).'],
  ['QOS_DUP_SCORE', '0–100', 'How closely the answers match another respondent’s. Blank when nothing was compared.'],
  ['QOS_IP_RISK', '0–100', 'IP address risk (repeated use, data-centre address).'],
  ['QOS_DEVICE_RISK', '0–100', 'Same device seen on other sessions of this survey.'],
  ['QOS_GEO_RISK', '0–100', 'Location mismatch risk.'],
  ['QOS_VELOCITY', '0–100', 'Many surveys started in a short time.'],
  ['QOS_DATACENTER', '0, 1', '1 when the IP belongs to a data centre, VPN or proxy.'],
  ['QOS_SPEEDER', 'count', 'Number of pages answered too fast.'],
  ['QOS_STRAIGHTLINE', 'count', 'Number of straight-lined grid questions.'],
  ['QOS_FLAGCOUNT', 'count', 'Number of quality reasons.'],
  ['QOS_REASON', 'code', 'The most serious reason code (0 when none). See the table below.'],
];

const REASONS = [
  ['1', 'Automated or headless browser', 'Bot'], ['2', 'Clicks and key presses generated by script', 'Bot'],
  ['3', 'Pages answered with no mouse or keyboard use', 'Bot'], ['4', 'Hidden honeypot field filled in', 'Bot'],
  ['5', 'Open ends that appeared without typing', 'Bot'], ['6', 'Bot-like behaviour score', 'Bot'],
  ['7', 'Typing or mouse movement with machine-exact timing', 'Bot'], ['8', 'Page times longer than the time the server saw', 'Bot'],
  ['10', 'Data centre, VPN or proxy IP address', 'Fraud'], ['11', 'Same device seen on other sessions of this survey', 'Fraud'],
  ['12', 'Same IP address used repeatedly', 'Fraud'], ['13', 'Answers copied from another respondent', 'Fraud'],
  ['14', 'Many surveys started in a short time', 'Fraud'], ['15', 'Same respondent seen from different countries within an hour', 'Fraud'],
  ['20', 'Low-quality open-ended answers', 'Quality'], ['21', 'Straight-lined grid questions', 'Quality'],
  ['22', 'Pages answered too fast', 'Quality'],
];

const EXAMPLE_ROWS = [
  ['k3f9x2m7q1', 'human', '0.08', '1', '0', '', 'Clean. Keep.'],
  ['b7n4c1v9z3', 'human', '0.34', '2', '20', '20,21,22', 'Not a bot, but a weak open end (“ok”), a straight-lined grid and 3 fast pages. Review.'],
  ['h2j6l8s0a5', 'bot', '0.95', '3', '1', '1,7', 'Automated browser with machine-exact typing. Remove.'],
  ['e5r7y9u1i3', 'human', '0.48', '2', '11', '11,13', 'Same device as an earlier respondent and the same open end word for word. Review. Note that the earlier respondent (p8d2w5r4t6) shows as clean: it finished before the copy arrived.'],
  ['m1q3e5t7u9', 'bot', '0.85', '3', '4', '4,10', 'Filled the hidden honeypot box, from a data-centre IP. Remove.'],
  ['g4h6j8k0l2', 'human', '0.11', '1', '0', '', 'Clean. QOS_OES is blank because the open end could not be checked in time.'],
  ['w9e1r3t5y7', 'unknown', '', '', '', '', 'Our check did not answer within 3 seconds. Look the uuid up on Live Quality.'],
];

const FILES = [
  ['examples/qos_example.sav', 'qos_example.sav', 'SPSS data file', 'Eight made-up respondents laid out like a Decipher export of a tracked survey.'],
  ['examples/qos_example.csv', 'qos_example.csv', 'CSV', 'The same rows, for Excel or R.'],
  ['examples/qos_labels.sps', 'qos_labels.sps', 'SPSS syntax', 'Adds value labels, a numeric score, one 0/1 variable per reason and a suggested Keep / Review / Remove variable. Works on your real export too.'],
];

export default function DataAndSpss() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Data collected & SPSS file"
        description="What this service records about respondents, what it never records, and what the quality variables in a Decipher SPSS export mean, with example files."
      />

      <Card title="On this page">
        <nav className="grid gap-1 text-sm sm:grid-cols-3">
          {SECTIONS.map(([id, label], i) => (
            <a key={id} href={`#${id}`} onClick={(e) => { e.preventDefault(); document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }); }}
              className="rounded px-2 py-1 text-blue-700 hover:bg-blue-50">
              {i + 1}. {label}
            </a>
          ))}
        </nav>
      </Card>

      <Section id="summary" title="1. In short">
        <ul className="space-y-1">
          <li className="flex gap-2"><Check aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-green-600" />We record <b>how</b> people answer: typing rhythm, mouse and touch, page times, and their device and network.</li>
          <li className="flex gap-2"><Check aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-green-600" />The only answers we keep are <b>typed open-ended answers</b> and <b>grid positions</b>, because the open-end and straight-lining checks need them.</li>
          <li className="flex gap-2"><X aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />We do <b>not</b> keep choice answers, the keys people type, contact or identity details, or anything outside the survey.</li>
          <li className="flex gap-2"><Check aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-green-600" />Decipher remains the place where the survey data lives. We add 21 <C>QOS_</C> variables to it on the last page.</li>
        </ul>
      </Section>

      <Section id="collected" title="2. What we collect and store" description="Kept in our database in Canada (Google Cloud, Toronto). Nothing is deleted automatically.">
        <Table head={['What', 'Exactly', 'Used for']} rows={COLLECTED.map(([a, b, c]) => [<b key="a" className="text-gray-900">{a}</b>, b, c])} />
      </Section>

      <Section id="not-collected" title="3. What we never collect">
        <ul className="space-y-1">
          {NOT_COLLECTED.map((item) => (
            <li key={item} className="flex gap-2"><X aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />{item}</li>
          ))}
        </ul>
      </Section>

      <Section id="personal" title="4. How personal details are kept out" description="Two layers: in the respondent's browser, and again on our server">
        <ol className="list-decimal space-y-1 pl-5">
          <li><b>In the browser</b>: the tracker skips any text box whose question asks for contact or identity details. It recognises them by the question wording, or by the box’s id, name or autofill setting (for example “email”). It never sends their answers, and it sends page addresses without anything after <C>?</C> or <C>#</C>. This applies to surveys tracked from 28 November 2026 on.</li>
          <li><b>On our server</b>, for every survey including ones tracked earlier: the same wording check marks such questions as personal, and their answers are not stored, not sent to the AI check, not compared for duplicates and not flagged for pasting. Email addresses and phone numbers (9–15 digits) inside other answers become <C>[email]</C> and <C>[phone]</C> before the AI check and before saving. Page addresses and referrers lose anything after <C>?</C> or <C>#</C>.</li>
        </ol>
        <Note>
          The wording list is deliberately narrow so real open ends are still checked: “What do you like about your phone?” is checked as usual.
          A contact question worded unusually, such as “How can we reach you?”, is not recognised. Its answer is stored, with any email or phone number masked.
          Word contact questions plainly, or put them on a page after the survey ends. Data stored before 28 November 2026 still has full page addresses and any personal details typed into text boxes.
        </Note>
      </Section>

      <Section id="where" title="5. Where the data goes">
        <Table
          head={['Who', 'What they receive']}
          rows={[
            [<b key="a" className="text-gray-900">Our database</b>, 'Everything in section 2. Google Cloud SQL in Toronto, Canada, encrypted at rest. Respondents’ browsers send it over HTTPS.'],
            [<b key="b" className="text-gray-900">OpenAI</b>, 'Each open-ended answer (with emails and phone numbers masked) and its question wording, to judge answer quality. Nothing else: no ids, IP addresses or device details.'],
            [<b key="c" className="text-gray-900">Decipher</b>, 'The 21 QOS_ results on the last page (section 6), and QOS_EARLY when the in-survey check is on.'],
            [<b key="d" className="text-gray-900">Anyone else</b>, 'No one. Data-centre IP checks use published address lists stored on our server; IP addresses are not sent to any lookup service.'],
          ]}
        />
      </Section>

      <Section id="spss" title="6. What the SPSS file contains" description="21 QOS_ variables, written once on a hidden last page when the respondent finishes">
        <p>In most surveys the variables appear near the end of the file, after your own questions. Their labels are the hidden question titles, so each ends with “(leave blank)”. That is an instruction meant for the page, not for you.</p>
        <h3 className="pt-2 font-semibold text-gray-900">Text (string) variables</h3>
        <Table head={['Variable', 'Type', 'Meaning']} rows={TEXT_VARS.map(([a, b, c]) => [<C key="a">{a}</C>, b, c])} />
        <h3 className="pt-2 font-semibold text-gray-900">Numeric variables</h3>
        <Table head={['Variable', 'Values', 'Meaning']} rows={NUMBER_VARS.map(([a, b, c]) => [<C key="a">{a}</C>, b, c])} />
        <p>If the in-survey bot check is switched on, there is also <C>QOS_EARLY</C> (“bot” or “human”). Respondents with “bot” were ended early, so they are terminates in Decipher, not completes.</p>
      </Section>

      <Section id="codes" title="7. Reason codes" description="QOS_REASON holds the most serious one; QOS_REASONS lists them all">
        <Table head={['Code', 'Reason', 'Group']} rows={REASONS} />
        <p>1–8: bot signals and behaviour. 10–15: fraud and duplicates. 20–22: answer quality. A survey’s quality rules can switch some of these off.</p>
      </Section>

      <Section id="read" title="8. How to read it">
        <h3 className="font-semibold text-gray-900">A simple cleaning routine</h3>
        <ol className="list-decimal space-y-1 pl-5">
          <li>Run <C>qos_labels.sps</C> on your export (section 9). It adds value labels and a <C>QOS_ACTION</C> variable.</li>
          <li><C>QOS_STATUS</C> = 3 (bot): remove.</li>
          <li><C>QOS_STATUS</C> = 2 (suspect): review. Look at <C>QOS_REASONS</C>: copied answers (13) and device reuse (11) usually mean remove; one fast page (22) on its own usually means keep.</li>
          <li><C>QOS_STATUS</C> = 1 (human): keep.</li>
          <li><C>QOS_STATUS</C> blank: look the uuid up on Live Quality (below).</li>
        </ol>

        <h3 className="pt-3 font-semibold text-gray-900">Why some values are blank</h3>
        <ul className="list-disc space-y-1 pl-5">
          <li><b>No QOS values at all</b>: the respondent never reached the last page (screened out, terminated or dropped out).</li>
          <li><b>QOS_FLAG = unknown and the rest blank</b>: our check did not answer within 3 seconds, or could not be reached. The survey carries on regardless.</li>
          <li><b>One score blank</b>: that check did not apply, for example <C>QOS_OES</C> with no open ends, or <C>QOS_DUP_SCORE</C> when there was nothing to compare.</li>
        </ul>

        <h3 className="pt-3 font-semibold text-gray-900">The SPSS values are a snapshot</h3>
        <p>They are worked out when each respondent finishes, and never change afterwards. Our dashboard keeps learning. For example, when someone copies an earlier respondent’s answers, only the later one is flagged in SPSS, and open ends checked after the respondent finished are not included.</p>
        <Note>
          For final cleaning, use <b>Live Quality → Add flags to a data file</b>. Upload your Decipher export and get it back with up-to-date <C>LQ_</C> variables matched on uuid, under the survey’s current rules. It also covers respondents with blank QOS values.
        </Note>

        <h3 className="pt-3 font-semibold text-gray-900">Reading the example file</h3>
        <Table head={['uuid', 'QOS_FLAG', 'QOS_SCORE', 'QOS_STATUS', 'QOS_REASON', 'QOS_REASONS', 'What it means']} rows={EXAMPLE_ROWS} />
        <p className="text-xs text-gray-500">QOS_FLAG says bot or not; QOS_STATUS also counts quality and fraud reasons, which is why a “human” can be a suspect (2).</p>
      </Section>

      <Section id="example" title="9. Example files" description="Made-up respondents; no real data">
        <div className="grid gap-3 sm:grid-cols-3">
          {FILES.map(([href, name, kind, text]) => (
            <div key={href} className="flex flex-col rounded-lg border border-gray-200 p-4">
              <div className="text-xs font-medium text-gray-500">{kind}</div>
              <div className="mt-1 font-mono text-sm text-gray-900">{name}</div>
              <p className="mt-2 flex-1 text-sm text-gray-600">{text}</p>
              <a href={href} download={name} className={buttonClass('secondary', 'sm', 'mt-3 gap-1.5 self-start')}>
                <Download aria-hidden="true" className="h-3.5 w-3.5" /> Download
              </a>
            </div>
          ))}
        </div>
        <p>To use the syntax on a real export: open your Decipher SPSS file, then File → Open → Syntax, choose <C>qos_labels.sps</C>, and Run → All.</p>
      </Section>
    </div>
  );
}
