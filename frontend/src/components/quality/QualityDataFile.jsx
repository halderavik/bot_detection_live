// Add live quality flags to a survey data file (SPSS, CSV or Excel) as LQ_ variables.

import React, { useEffect, useRef, useState } from 'react';
import { Database, Download, FileUp } from 'lucide-react';
import { liveQualityService } from '../../services/apiService';

function save(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** The error text of a blob response (the merge endpoint answers errors as JSON). */
async function mergeError(err) {
  const data = err?.response?.data;
  if (data instanceof Blob) {
    try {
      const body = JSON.parse(await data.text());
      if (typeof body.detail === 'string') return body.detail;
    } catch (e) {
      // fall through
    }
  }
  return err?.message || 'The flags were not added to the file.';
}

function Fact({ label, value }) {
  return (
    <div>
      <dt className="text-xs text-gray-500">{label}</dt>
      <dd className="text-gray-900">{value}</dd>
    </div>
  );
}

export default function QualityDataFileCard({ surveyId }) {
  const input = useRef(null);
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [outcome, setOutcome] = useState(null);

  useEffect(() => {
    setFile(null);
    setError('');
    setOutcome(null);
    if (input.current) input.current.value = '';
  }, [surveyId]);

  async function merge() {
    if (!file) return;
    setBusy(true);
    setError('');
    setOutcome(null);
    try {
      const result = await liveQualityService.mergeDataFile(surveyId, file);
      setOutcome(result);
      save(result.blob, result.filename);
    } catch (err) {
      setError(await mergeError(err));
    } finally {
      setBusy(false);
    }
  }

  const report = outcome?.report;
  return (
    <section aria-labelledby="quality-data-title" className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
          <Database aria-hidden="true" className="h-5 w-5" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-gray-900" id="quality-data-title">Add flags to a data file</h3>
          <p className="mt-0.5 text-sm text-gray-600">
            Upload the Decipher export of this survey (SPSS .sav, CSV or Excel). Each record is matched on{' '}
            <code className="text-xs">QOS_SESSION</code>, then <code className="text-xs">QOS_RESPONDENT</code>, then
            Decipher&apos;s <code className="text-xs">uuid</code>, and you get the same file back with the scores and flags as{' '}
            <code className="text-xs">LQ_</code> variables, under this survey&apos;s rules.
          </p>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <label className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-800 hover:bg-gray-50 focus-within:ring-2 focus-within:ring-blue-500">
          <FileUp aria-hidden="true" className="h-4 w-4" />
          {file ? 'Choose another file' : 'Choose data file'}
          <input
            accept=".sav,.csv,.xlsx"
            className="sr-only"
            onChange={(event) => {
              setFile(event.target.files?.[0] || null);
              setOutcome(null);
              setError('');
            }}
            ref={input}
            type="file"
          />
        </label>
        {file && <span className="truncate text-sm text-gray-700">{file.name}</span>}
        <span className="flex-1" />
        <button
          className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={!file || busy}
          onClick={merge}
          type="button"
        >
          <Download aria-hidden="true" className="h-4 w-4" />
          {busy ? 'Adding flags…' : 'Add flags and download'}
        </button>
      </div>

      {error && <p className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">{error}</p>}

      {report && (
        <div className="mt-3 space-y-2" role="status">
          <p className="text-sm text-gray-800">{report.message}</p>
          <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm sm:grid-cols-4">
            <Fact label="Matched" value={`${report.matched} of ${report.tracked}`} />
            <Fact label="Flagged" value={String(report.flagged)} />
            <Fact label="Bots" value={String(report.bots)} />
            <Fact label="Matched on" value={(report.match_columns || []).join(', ') || '–'} />
          </dl>
          {report.unmatched > 0 && (
            <p className="text-xs text-gray-500">
              {report.unmatched} tracked records weren&apos;t found in the live quality results (for example a different survey id
              or sessions that were removed). Their LQ_MATCHED is 0.
            </p>
          )}
          <button
            className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:underline"
            onClick={() => save(outcome.blob, outcome.filename)}
            type="button"
          >
            <Download aria-hidden="true" className="h-4 w-4" /> Download {outcome.filename} again
          </button>
        </div>
      )}

      <details className="mt-3 text-sm">
        <summary className="cursor-pointer text-gray-700">What gets added</summary>
        <ul className="mt-2 list-disc space-y-0.5 pl-5 text-gray-700">
          <li><span className="text-gray-900">LQ_MATCHED, LQ_STATUS, LQ_VERDICT</span>: found in the results, session status, human or bot under this survey&apos;s rules.</li>
          <li><span className="text-gray-900">LQ_BOT_SCORE, LQ_BOT_RISK, LQ_BOT_SIGNALS</span>: behaviour score, its risk band, and the decisive signals that fired.</li>
          <li><span className="text-gray-900">LQ_SECONDS, LQ_PAGES, LQ_SEC_PER_PAGE, LQ_TEXT_QUALITY</span>: timing and open-end quality.</li>
          <li><span className="text-gray-900">LQ_FRAUD_SCORE, LQ_FRAUD_RISK</span>: fraud score and its band.</li>
          <li><span className="text-gray-900">LQ_F_BOT … LQ_F_DATACENTRE</span>: one 0/1 variable per flag, plus LQ_NFLAGS and LQ_FLAGS.</li>
        </ul>
        <p className="mt-2 text-xs text-gray-500">
          In SPSS files the LQ_ variables get labels and value labels, and the existing variables keep theirs. Uploading a file
          that already has LQ_ variables replaces them, so you can refresh after changing the rules.
        </p>
      </details>
    </section>
  );
}
