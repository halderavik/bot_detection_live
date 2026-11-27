// Add tracking, before the upload: a checklist for preparing the XML, the result of the
// automatic check (every problem explained, with how to fix it), and "Fix with AI".

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { AlertTriangle, CheckCircle2, ChevronDown, Download, Sparkles, Upload, Wrench, XCircle } from 'lucide-react';

const CHECKLIST = [
  {
    title: 'It is the complete survey XML, exported from Decipher',
    text: 'Open the survey in Decipher and export or copy its whole XML. It must start with <survey ...> and end with </survey>. A copied block of questions without the <survey> tag cannot be tracked.',
  },
  {
    title: 'The <survey> tag has compat 143 or higher',
    text: 'Decipher has retired compat below 143. At compat 151 and above, the tag also needs delphi="1". Decipher\'s own export already has both.',
  },
  {
    title: 'Old question styles match the compat',
    text: 'Some styles only run up to a compat: atm1d.9 up to 149; autosum.5, ranksort.7, cardsort.8 and atmtable.6 up to 154. Lower the compat or update those questions.',
  },
  {
    title: 'The file opens as XML without errors',
    text: 'No bare & or < in text (write &amp; and &lt;, or use CDATA), every tag closed, nothing cut off at the end.',
  },
  {
    title: 'Every label is used once, and none start with QOS_',
    text: 'Questions, blocks, loops and page elements each need their own label. QOS_ labels are reserved for the results questions tracking adds.',
  },
  {
    title: 'You know where quota sheets and data files live',
    text: 'Quotas (sheet="...") and Database("....dat") files are stored in the Decipher survey, not in the XML. Upload the tracked file over the original survey to keep them, or add them to a new survey.',
  },
  {
    title: 'Saved as UTF-8, up to 5 MB',
    text: 'A .xml file, or .txt holding the XML. Files saved from Word or Excel are often not UTF-8.',
  },
  {
    title: 'You have a copy of the original',
    text: 'Tracking adds to the file; keep the original so you can go back. Test on a copy of the Decipher survey if it is already live.',
  },
];

export function XmlChecklist() {
  return (
    <details className="group rounded-xl border border-gray-200 bg-white shadow-sm" open>
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4">
        <span>
          <span className="block text-sm font-semibold text-gray-900">Before you upload: check your XML</span>
          <span className="block text-xs text-gray-500">The upload is checked against these automatically, and every problem is explained.</span>
        </span>
        <ChevronDown aria-hidden="true" className="h-4 w-4 shrink-0 text-gray-400 transition-transform group-open:rotate-180" />
      </summary>
      <ol className="grid gap-3 border-t border-gray-100 px-5 py-4 md:grid-cols-2">
        {CHECKLIST.map((item, index) => (
          <li className="flex gap-3" key={item.title}>
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-50 text-xs font-semibold text-blue-700">
              {index + 1}
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-medium text-gray-900">{item.title}</span>
              <span className="block text-xs text-gray-600">{item.text}</span>
            </span>
          </li>
        ))}
      </ol>
    </details>
  );
}

function IssueItem({ issue }) {
  const error = issue.severity === 'error';
  return (
    <li className={clsx('rounded-lg border p-3', error ? 'border-red-200 bg-red-50/60' : 'border-amber-200 bg-amber-50/60')}>
      <div className="flex flex-wrap items-start gap-2">
        {error ? (
          <XCircle aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
        ) : (
          <AlertTriangle aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
        )}
        <p className="min-w-0 flex-1 text-sm font-medium text-gray-900">{issue.title}</p>
        <span className="flex flex-wrap gap-1.5 text-xs">
          {issue.line && <span className="rounded bg-white px-1.5 py-0.5 font-mono text-gray-600 ring-1 ring-gray-200">line {issue.line}</span>}
          <span className={clsx('rounded px-1.5 py-0.5 ring-1', issue.ai_can_fix ? 'bg-white text-violet-700 ring-violet-200' : 'bg-white text-gray-600 ring-gray-200')}>
            {issue.ai_can_fix ? 'Fix with AI can repair this' : 'Needs your action'}
          </span>
        </span>
      </div>
      <p className="mt-1.5 break-words pl-6 text-sm text-gray-700">{issue.detail}</p>
      {issue.items?.length > 0 && (
        <p className="mt-1 break-words pl-6 font-mono text-xs text-gray-600">{issue.items.join(', ')}</p>
      )}
      <p className="mt-1.5 pl-6 text-sm text-gray-800"><span className="font-medium">How to fix: </span>{issue.fix}</p>
    </li>
  );
}

export function CheckReport({ report, filename }) {
  const errors = report.issues.filter((issue) => issue.severity === 'error');
  const warnings = report.issues.filter((issue) => issue.severity === 'warning');
  const facts = [
    report.questions ? `${report.questions} questions` : null,
    report.pages ? `${report.pages} pages` : null,
    report.lines ? `${report.lines} lines` : null,
    report.size_kb ? `${report.size_kb} KB` : null,
  ].filter(Boolean).join(' · ');

  return (
    <div aria-live="polite" className="space-y-3">
      {errors.length > 0 ? (
        <div className="flex items-start gap-2" role="alert">
          <XCircle aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
          <div>
            <p className="text-sm font-semibold text-red-800">
              {filename} has {errors.length} problem{errors.length === 1 ? '' : 's'} to fix before tracking can be added
            </p>
            <p className="text-xs text-gray-600">{facts}. Fix the file and upload it again, or use Fix with AI below.</p>
          </div>
        </div>
      ) : (
        <div className="flex items-start gap-2" role="status">
          <CheckCircle2 aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-green-600" />
          <div>
            <p className="text-sm font-semibold text-green-800">
              {filename} is ready for tracking{warnings.length ? `, with ${warnings.length} thing${warnings.length === 1 ? '' : 's'} to know` : ''}
            </p>
            <p className="text-xs text-gray-600">
              {facts}.{report.already_tracked ? ' It already has tracking; adding it again replaces it.' : ''}
            </p>
          </div>
        </div>
      )}
      {report.issues.length > 0 && (
        <ul className="space-y-2">
          {[...errors, ...warnings].map((issue) => <IssueItem issue={issue} key={`${issue.code}-${issue.line}`} />)}
        </ul>
      )}
    </div>
  );
}

const PLACEHOLDER = `Optional. For example:
- The survey title is "Amazon Fee Card Conjoint"
- Use compat 154
- Remove the quotas, this is only a test survey
- Rename the second Q5 to Q5b`;

export function FixWithAi({ report, busy, onFix, onReupload, aiAvailable }) {
  const [instructions, setInstructions] = useState('');
  const errors = report.issues.some((issue) => issue.severity === 'error');
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="rounded-lg border border-gray-200 p-4">
        <p className="flex items-center gap-2 text-sm font-semibold text-gray-900">
          <Wrench aria-hidden="true" className="h-4 w-4 text-gray-500" /> Option 1: fix it yourself
        </p>
        <p className="mt-1 text-sm text-gray-600">
          Correct the file in Decipher or a text editor using the steps above, then upload it again. The new file is checked the same way.
        </p>
        <button className="mt-3 inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-800 hover:bg-gray-50" onClick={onReupload} type="button">
          <Upload aria-hidden="true" className="h-4 w-4" /> Upload a corrected file
        </button>
      </div>
      <div className="rounded-lg border border-violet-200 bg-violet-50/40 p-4">
        <p className="flex items-center gap-2 text-sm font-semibold text-gray-900">
          <Sparkles aria-hidden="true" className="h-4 w-4 text-violet-600" /> Option 2: Fix with AI
        </p>
        <p className="mt-1 text-sm text-gray-600">
          An AI agent edits only what is needed, then the file is checked again. Tell it your preferences or anything missing; with no
          instructions it decides by itself and lists every choice it made.
          {!errors && ' There are no errors, so it only acts on your instructions (for example removing quotas).'}
        </p>
        <label className="mt-3 block text-xs font-medium text-gray-700" htmlFor="ai-instructions">Instructions for the AI (optional)</label>
        <textarea
          className="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
          id="ai-instructions"
          maxLength={2000}
          onChange={(event) => setInstructions(event.target.value)}
          placeholder={PLACEHOLDER}
          rows={5}
          value={instructions}
        />
        <div className="mt-1 flex justify-between text-xs text-gray-500">
          <span>It never changes question wording or logic unless you ask, and never touches the tracker.</span>
          <span>{instructions.length}/2000</span>
        </div>
        {aiAvailable === false ? (
          <p className="mt-3 text-sm text-amber-800">
            Fix with AI needs an OpenAI API key on the service. Add it on <Link className="font-medium underline" to="/settings">Settings</Link>.
          </p>
        ) : (
          <button
            className="mt-3 inline-flex items-center gap-2 rounded-md bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={busy || (!errors && !instructions.trim())}
            onClick={() => onFix(instructions.trim())}
            type="button"
          >
            <Sparkles aria-hidden="true" className="h-4 w-4" />
            {busy ? 'Fixing… (can take a minute or two)' : 'Fix with AI'}
          </button>
        )}
      </div>
    </div>
  );
}

function List({ title, items, tone = 'text-gray-700' }) {
  if (!items?.length) return null;
  return (
    <div>
      <p className="text-sm font-medium text-gray-900">{title}</p>
      <ul className={clsx('mt-1 list-disc space-y-0.5 pl-5 text-sm', tone)}>
        {items.map((item, index) => <li key={index}>{item}</li>)}
      </ul>
    </div>
  );
}

export function FixResult({ fix, onUse, onDownload }) {
  const ok = fix.report?.ok;
  return (
    <div className="space-y-3 rounded-lg border border-violet-200 bg-white p-4" role="status">
      <p className="flex items-center gap-2 text-sm font-semibold text-gray-900">
        <Sparkles aria-hidden="true" className="h-4 w-4 text-violet-600" />
        {fix.changed
          ? `Fix with AI made ${fix.applied} edit${fix.applied === 1 ? '' : 's'}${ok ? ' and the file now passes the check' : ', but some problems are left'}`
          : 'Fix with AI did not change the file'}
      </p>
      <List items={fix.changes} title="What changed" />
      <List items={fix.assumptions} title="Choices the AI made (check these)" tone="text-amber-800" />
      <List items={fix.cannot_fix} title="What it could not fix" tone="text-red-700" />
      <List items={fix.skipped} title="Edits that were not applied" tone="text-gray-500" />
      <div className="flex flex-wrap gap-2 pt-1">
        {fix.changed && (
          <button className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700" onClick={onUse} type="button">
            <CheckCircle2 aria-hidden="true" className="h-4 w-4" /> {ok ? 'Use the fixed file' : 'Use the fixed file and keep fixing'}
          </button>
        )}
        {fix.changed && (
          <button className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-800 hover:bg-gray-50" onClick={onDownload} type="button">
            <Download aria-hidden="true" className="h-4 w-4" /> Download {fix.filename}
          </button>
        )}
      </div>
      <p className="text-xs text-gray-500">
        Fixed by {fix.model}. Review the changes before you launch: test the fixed survey in Decipher like any edit.
      </p>
    </div>
  );
}
