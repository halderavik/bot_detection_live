// Upload to Decipher, with Decipher's refusals explained.
// When the file came from Fix with AI, a refusal can be fixed with AI and uploaded again in one step;
// a file the user fixed by hand only gets Decipher's error, explained.

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, CheckCircle, ExternalLink, Sparkles, UploadCloud, XCircle } from 'lucide-react';
import { toast } from 'react-toastify';
import { trackingService } from '../../services/apiService';

const errorMessage = (err) => {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join('; ');
  if (detail && typeof detail.message === 'string') return detail.message;
  return err?.message || 'The upload failed.';
};

const toError = (err) => {
  const detail = err?.response?.data?.detail;
  const structured = detail && typeof detail === 'object' && !Array.isArray(detail);
  return {
    message: errorMessage(err),
    errors: structured && Array.isArray(detail.errors) ? detail.errors : [],
    explained: structured && Array.isArray(detail.explained) ? detail.explained : [],
    fileProblem: structured ? Boolean(detail.file_problem) : false,
    surveyPath: structured ? detail.survey_path || null : null,
  };
};

function ExplainedErrors({ items }) {
  return (
    <ul className="mt-2 space-y-2">
      {items.map((item) => (
        <li className="rounded-md border border-red-200 bg-white p-3" key={item.message}>
          <p className="break-words font-mono text-xs text-red-900">{item.message}</p>
          <p className="mt-1.5 text-sm text-gray-800">{item.explanation}</p>
          <p className="mt-1 text-sm text-gray-800"><span className="font-medium">How to fix: </span>{item.fix}</p>
          <p className="mt-1.5 flex flex-wrap gap-1.5 text-xs">
            {item.page && <span className="rounded bg-gray-100 px-1.5 py-0.5 text-gray-700">Decipher page {item.page}</span>}
            {item.needs_instruction && (
              <span className="rounded bg-amber-50 px-1.5 py-0.5 text-amber-800 ring-1 ring-amber-200">Fix with AI only acts on this if you tell it to</span>
            )}
          </p>
        </li>
      ))}
    </ul>
  );
}

// initial: the instructions used on the last retry, kept so a second refusal doesn't lose them.
function AiRetry({ error, onRetry, busy, step, initial = '' }) {
  const [instructions, setInstructions] = useState(initial);
  const needsInstruction = error.explained.some((item) => item.needs_instruction);
  return (
    <div className="mt-3 rounded-md border border-violet-200 bg-violet-50/50 p-3">
      <p className="flex items-center gap-2 text-sm font-semibold text-gray-900">
        <Sparkles aria-hidden="true" className="h-4 w-4 text-violet-600" /> Fix with AI and upload again
      </p>
      <p className="mt-1 text-sm text-gray-700">
        This file came from Fix with AI, so the AI can work on Decipher&apos;s errors too. It fixes the file, checks it, adds tracking again
        with the same settings, and uploads to the same Decipher survey.
      </p>
      {needsInstruction && (
        <p className="mt-1 text-sm text-amber-800">
          Some errors need your decision: the AI cannot create quota sheets or data files. Tell it what to do, for example
          &quot;remove the quotas and the data-file checks, this is a test survey&quot;, or upload those files in Decipher.
        </p>
      )}
      <label className="mt-2 block text-xs font-medium text-gray-700" htmlFor="decipher-ai-instructions">Instructions for the AI (optional)</label>
      <textarea
        className="mt-1 block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
        id="decipher-ai-instructions"
        maxLength={2000}
        onChange={(event) => setInstructions(event.target.value)}
        placeholder="Optional. With no instructions, the AI fixes what it can on its own."
        rows={3}
        value={instructions}
      />
      <button
        className="mt-2 inline-flex items-center gap-2 rounded-md bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
        disabled={busy}
        onClick={() => onRetry(instructions.trim())}
        type="button"
      >
        <Sparkles aria-hidden="true" className="h-4 w-4" />
        {busy ? step || 'Working…' : 'Fix with AI and upload again'}
      </button>
    </div>
  );
}

// result: the tracked file. aiFixed: the file came from Fix with AI.
// onAiRetry(errors, instructions) fixes, checks and re-tracks; it resolves with { result, fix }.
export default function DecipherUploadPanel({ result, aiFixed, onAiRetry }) {
  const info = result.decipher_upload || {};
  const lastPath = info.last_path || '';
  const [target, setTarget] = useState(lastPath ? 'last' : 'new');
  const [path, setPath] = useState('');
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState('');
  const [error, setError] = useState(null);
  const [uploaded, setUploaded] = useState(null);
  const [aiNote, setAiNote] = useState(null);
  const [lastInstructions, setLastInstructions] = useState('');

  if (!info.configured) {
    return (
      <p className="text-sm text-gray-500">
        To upload straight to Decipher, add the Decipher API key on <Link className="font-medium underline" to="/settings">Settings</Link>.
        Until then, download the file and import it in Decipher.
      </p>
    );
  }

  const send = async (xml, surveyId, previousError) => {
    // After a refusal that already created the Decipher survey, upload to that survey again.
    const surveyPath = previousError?.surveyPath || (target === 'path' ? path.trim() : null);
    const response = await trackingService.uploadToDecipher({
      xml,
      survey_id: surveyId,
      survey_path: surveyPath,
      create_new: !surveyPath && target === 'new',
    });
    setUploaded(response);
    setError(null);
    toast.success(response.message);
  };

  const upload = async () => {
    setBusy(true);
    setStep('Uploading to Decipher…');
    setError(null);
    setUploaded(null);
    setAiNote(null);
    try {
      await send(result.xml, result.survey_id, null);
    } catch (err) {
      setError(toError(err));
    } finally {
      setBusy(false);
      setStep('');
    }
  };

  const retryWithAi = async (instructions) => {
    const previous = error;
    setLastInstructions(instructions);
    setBusy(true);
    setAiNote(null);
    try {
      setStep('Fixing with AI…');
      const { result: tracked, fix } = await onAiRetry(previous.errors.length ? previous.errors : [previous.message], instructions, setStep);
      setAiNote(fix);
      setStep('Uploading to Decipher…');
      await send(tracked.xml, tracked.survey_id, previous);
    } catch (err) {
      if (err?.response) setError(toError(err));
      else setError({ ...previous, retryMessage: err?.message || 'Fix with AI could not finish.' });
    } finally {
      setBusy(false);
      setStep('');
    }
  };

  const radio = 'flex items-start gap-2 text-sm text-gray-800';
  return (
    <div className="rounded-md border border-gray-200 p-4 space-y-3" aria-label="Upload to Decipher">
      <h3 className="text-sm font-medium text-gray-900">Upload to Decipher</h3>
      <fieldset className="space-y-2">
        <legend className="sr-only">Where to upload</legend>
        {lastPath && (
          <label className={radio}>
            <input type="radio" name="decipher-target" checked={target === 'last'} onChange={() => setTarget('last')} className="mt-0.5" />
            <span>Update the survey uploaded last time (<span className="font-mono">{lastPath}</span>)</span>
          </label>
        )}
        <label className={radio}>
          <input type="radio" name="decipher-target" checked={target === 'new'} onChange={() => setTarget('new')} className="mt-0.5" />
          <span>Create a new Decipher survey named &quot;{result.survey_id}&quot;</span>
        </label>
        <label className={radio}>
          <input type="radio" name="decipher-target" checked={target === 'path'} onChange={() => setTarget('path')} className="mt-0.5" />
          <span>Replace the XML of an existing survey</span>
        </label>
        {target === 'path' && (
          <div className="ml-6">
            <label htmlFor="decipher-path" className="sr-only">Decipher survey path or link</label>
            <input
              id="decipher-path"
              type="text"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="selfserve/53b/240101, or the survey link"
              className="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">Decipher checks the file before saving it and never replaces the XML of a live survey.</p>
          </div>
        )}
      </fieldset>
      <button
        type="button"
        onClick={upload}
        disabled={busy || (target === 'path' && !path.trim())}
        className="inline-flex items-center gap-2 rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <UploadCloud className="h-4 w-4" aria-hidden="true" />
        {busy && !error ? step || 'Uploading to Decipher…' : 'Upload to Decipher'}
      </button>

      {aiNote && (
        <div className="rounded-md border border-violet-200 bg-white p-3 text-sm" role="status">
          <p className="font-medium text-gray-900">Fix with AI changed the file before this upload</p>
          {aiNote.changes?.length > 0 && <ul className="mt-1 list-disc pl-5 text-gray-700">{aiNote.changes.map((c, i) => <li key={i}>{c}</li>)}</ul>}
          {aiNote.assumptions?.length > 0 && (
            <>
              <p className="mt-2 font-medium text-gray-900">Choices the AI made (check these)</p>
              <ul className="mt-1 list-disc pl-5 text-amber-800">{aiNote.assumptions.map((c, i) => <li key={i}>{c}</li>)}</ul>
            </>
          )}
          {aiNote.cannot_fix?.length > 0 && (
            <>
              <p className="mt-2 font-medium text-gray-900">What it could not fix</p>
              <ul className="mt-1 list-disc pl-5 text-red-700">{aiNote.cannot_fix.map((c, i) => <li key={i}>{c}</li>)}</ul>
            </>
          )}
          {aiNote.skipped?.length > 0 && (
            <>
              <p className="mt-2 font-medium text-gray-900">Edits that were not applied</p>
              <ul className="mt-1 list-disc pl-5 text-gray-500">{aiNote.skipped.map((c, i) => <li key={i}>{c}</li>)}</ul>
            </>
          )}
        </div>
      )}

      {uploaded && (
        <div role="status" className="flex items-start gap-2 rounded-md bg-green-50 border border-green-200 p-3 text-sm text-green-800">
          <CheckCircle className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
          <span>
            {uploaded.message}{' '}
            <a href={uploaded.survey_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 font-medium underline">
              Open the survey <ExternalLink className="h-3 w-3" aria-hidden="true" />
            </a>
          </span>
        </div>
      )}
      {uploaded?.warnings?.length > 0 && (
        <div role="status" className="flex items-start gap-2 rounded-md bg-yellow-50 border border-yellow-200 p-3 text-sm text-yellow-800">
          <AlertTriangle className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
          <ul className="space-y-1">{uploaded.warnings.map((w) => <li key={w}>{w}</li>)}</ul>
        </div>
      )}

      {error && (
        <div role="alert" className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-800">
          <div className="flex items-start gap-2">
            <XCircle className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <p className="font-semibold">
                {error.fileProblem
                  ? `Decipher refused the file${error.explained.length > 1 ? ` (${error.explained.length} errors)` : ''}`
                  : error.message}
              </p>
              {error.fileProblem && error.explained.length === 0 && <p className="mt-0.5 text-red-700">{error.message}</p>}
              {error.explained.length > 0 && <ExplainedErrors items={error.explained} />}
              {error.surveyPath && (
                <p className="mt-2">
                  The survey&apos;s XML in Decipher was not replaced. The Decipher survey is <span className="font-mono">{error.surveyPath}</span>;
                  the next upload updates it instead of creating another one.
                </p>
              )}
              {error.retryMessage && <p className="mt-2 font-medium">{error.retryMessage}</p>}
              {error.fileProblem && !aiFixed && (
                <p className="mt-2 text-gray-800">
                  This file was not made with Fix with AI, so Decipher&apos;s errors are shown as reported. Correct the file, add tracking again,
                  and upload it.
                </p>
              )}
            </div>
          </div>
          {error.fileProblem && aiFixed && <AiRetry busy={busy} error={error} initial={lastInstructions} onRetry={retryWithAi} step={step} />}
        </div>
      )}
    </div>
  );
}
