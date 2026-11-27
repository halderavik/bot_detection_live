// Integrations: the ways to connect a survey, and whether the platform keys are set.
// Step-by-step manual instructions live on the Manual setup page.

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ClipboardList, Code2, FileCode2, Globe, LayoutTemplate, ListChecks, Upload } from 'lucide-react';
import { integrationService } from '../services/apiService';
import { Badge, Card, PageHeader } from './ui';

const ROUTES = [
  {
    to: '/tracking',
    icon: Upload,
    title: 'Add tracking (automatic)',
    text: 'Upload a Decipher survey XML. Tracking, results questions and optional checks are added for you, and the file can go straight to Decipher.',
  },
  {
    to: '/manual-setup?platform=decipher',
    icon: FileCode2,
    title: 'Decipher by hand',
    text: 'Two XML blocks to paste into the survey, with step-by-step instructions.',
  },
  {
    to: '/manual-setup?platform=qualtrics',
    icon: LayoutTemplate,
    title: 'Qualtrics',
    text: 'One line in the survey header and two embedded data fields; flags are added to the export afterwards.',
  },
  {
    to: '/manual-setup?platform=other',
    icon: ListChecks,
    title: 'Other survey platforms',
    text: 'Any tool that lets you add a script to every page, with two ways to get the results into your data.',
  },
  {
    to: '/manual-setup?platform=web',
    icon: Globe,
    title: 'Your own web pages',
    text: 'A script tag on every page and hidden fields on the last page.',
  },
  {
    to: '/manual-setup?platform=api',
    icon: Code2,
    title: 'API',
    text: 'Send events from your own tracker or server and read the verdict.',
  },
];

export default function Integrations() {
  const [status, setStatus] = useState(null);

  useEffect(() => {
    integrationService.getIntegrationStatus().then((data) => setStatus(data?.data || data)).catch(() => setStatus(null));
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        actions={
          <Link className="inline-flex h-9 items-center gap-2 rounded-lg bg-blue-600 px-3.5 text-sm font-medium text-white shadow-sm hover:bg-blue-700" to="/manual-setup">
            <ClipboardList aria-hidden="true" className="h-4 w-4" /> Manual setup
          </Link>
        }
        description="Choose how bot and fraud checks get into a survey."
        title="Integrations"
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {ROUTES.map((route) => {
          const Icon = route.icon;
          return (
            <Link className="group rounded-xl border border-gray-200 bg-white p-5 shadow-sm hover:border-blue-300 hover:shadow" key={route.to} to={route.to}>
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
                <Icon aria-hidden="true" className="h-5 w-5" />
              </span>
              <h2 className="mt-3 text-sm font-semibold text-gray-900 group-hover:text-blue-700">{route.title}</h2>
              <p className="mt-1 text-sm text-gray-600">{route.text}</p>
            </Link>
          );
        })}
      </div>

      <Card description="Keys are set on the Settings page" title="Platform keys">
        <dl className="space-y-3 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <dt className="font-medium text-gray-900">Decipher API key</dt>
            <dd><Badge tone={status?.decipher?.configured ? 'success' : 'neutral'}>{status?.decipher?.configured ? 'Set' : 'Not set'}</Badge></dd>
            <dd className="basis-full text-gray-600">Needed only to upload a tracked survey to Decipher from Add tracking. Manual setup works without it.</dd>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <dt className="font-medium text-gray-900">Qualtrics API token</dt>
            <dd><Badge tone={status?.qualtrics?.configured ? 'success' : 'neutral'}>{status?.qualtrics?.configured ? 'Set' : 'Not set'}</Badge></dd>
            <dd className="basis-full text-gray-600">Not needed for the Qualtrics setup on Manual setup.</dd>
          </div>
        </dl>
        <Link className="mt-4 inline-block text-sm font-medium text-blue-700 underline" to="/settings">Open Settings</Link>
      </Card>
    </div>
  );
}
