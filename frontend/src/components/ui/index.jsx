// Shared building blocks so every screen looks and behaves the same:
// page headers, cards, stat tiles, buttons, badges, and empty, loading and error states.

import React from 'react';
import clsx from 'clsx';
import { AlertTriangle, Loader2 } from 'lucide-react';

export function PageHeader({ title, description, actions, eyebrow }) {
  return (
    <header className="flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0">
        {eyebrow && <div className="mb-1 text-xs font-medium text-gray-500">{eyebrow}</div>}
        <h1 className="text-2xl font-semibold tracking-tight text-gray-900">{title}</h1>
        {description && <p className="mt-1 max-w-3xl text-sm text-gray-600">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}

export function Card({ title, description, actions, children, className, bodyClassName, as: Tag = 'section' }) {
  return (
    <Tag className={clsx('rounded-xl border border-gray-200 bg-white shadow-sm', className)}>
      {(title || actions) && (
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-gray-100 px-5 py-4">
          <div className="min-w-0">
            {title && <h2 className="text-sm font-semibold text-gray-900">{title}</h2>}
            {description && <p className="mt-0.5 text-xs text-gray-500">{description}</p>}
          </div>
          {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className={clsx('px-5 py-4', bodyClassName)}>{children}</div>
    </Tag>
  );
}

const STAT_TONES = {
  neutral: 'text-gray-900',
  danger: 'text-red-600',
  warn: 'text-amber-600',
  success: 'text-green-600',
};

export function StatCard({ label, value, note, tone = 'neutral', icon: Icon }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium text-gray-500">{label}</p>
        {Icon && <Icon aria-hidden="true" className="h-4 w-4 text-gray-400" />}
      </div>
      <p className={clsx('mt-1 text-2xl font-semibold tabular-nums', STAT_TONES[tone])}>{value}</p>
      {note && <p className="mt-0.5 text-xs text-gray-500">{note}</p>}
    </div>
  );
}

const BUTTON_VARIANTS = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm',
  secondary: 'border border-gray-300 bg-white text-gray-800 hover:bg-gray-50 shadow-sm',
  ghost: 'text-gray-700 hover:bg-gray-100',
  danger: 'border border-red-200 bg-white text-red-700 hover:bg-red-50',
};
const BUTTON_SIZES = {
  sm: 'h-8 px-2.5 text-xs gap-1.5',
  md: 'h-9 px-3.5 text-sm gap-2',
};

export function buttonClass(variant = 'secondary', size = 'md', extra) {
  return clsx(
    'inline-flex items-center justify-center rounded-lg font-medium transition-colors',
    'focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1',
    'disabled:cursor-not-allowed disabled:opacity-50',
    BUTTON_VARIANTS[variant],
    BUTTON_SIZES[size],
    extra,
  );
}

export function Button({ variant = 'secondary', size = 'md', icon: Icon, children, className, type = 'button', ...props }) {
  return (
    <button className={buttonClass(variant, size, className)} type={type} {...props}>
      {Icon && <Icon aria-hidden="true" className={size === 'sm' ? 'h-3.5 w-3.5' : 'h-4 w-4'} />}
      {children}
    </button>
  );
}

const BADGE_TONES = {
  neutral: 'bg-gray-100 text-gray-700',
  accent: 'bg-blue-50 text-blue-700',
  success: 'bg-green-50 text-green-700',
  warn: 'bg-amber-50 text-amber-800',
  danger: 'bg-red-50 text-red-700',
};

export function Badge({ tone = 'neutral', children, className }) {
  return (
    <span className={clsx('inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium', BADGE_TONES[tone], className)}>
      {children}
    </span>
  );
}

/** Verdict badge for a session or respondent: bot, human, or not checked yet. */
export function VerdictBadge({ isBot, analyzed = true }) {
  if (!analyzed || isBot === null || isBot === undefined) return <Badge>Not checked</Badge>;
  return isBot ? <Badge tone="danger">Bot</Badge> : <Badge tone="success">Human</Badge>;
}

const RISK_TONES = { low: 'success', medium: 'warn', high: 'danger', critical: 'danger' };

export function RiskBadge({ level }) {
  const key = String(level || 'unknown').toLowerCase();
  return <Badge tone={RISK_TONES[key] || 'neutral'}>{key === 'unknown' ? 'Unknown' : key.charAt(0).toUpperCase() + key.slice(1)}</Badge>;
}

export function EmptyState({ icon: Icon, title, children, action }) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-12 text-center">
      {Icon && (
        <span className="mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-gray-100 text-gray-500">
          <Icon aria-hidden="true" className="h-5 w-5" />
        </span>
      )}
      <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
      {children && <div className="mt-1 max-w-md text-sm text-gray-600">{children}</div>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function Loading({ label = 'Loading…', className }) {
  return (
    <div className={clsx('flex items-center justify-center gap-2 py-12 text-sm text-gray-500', className)} role="status">
      <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" />
      {label}
    </div>
  );
}

export function ErrorBanner({ children, onRetry }) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
      <AlertTriangle aria-hidden="true" className="h-4 w-4 shrink-0" />
      <span className="min-w-0 flex-1">{children}</span>
      {onRetry && <Button onClick={onRetry} size="sm" variant="danger">Try again</Button>}
    </div>
  );
}

export function apiError(err, fallback) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join('; ');
  if (detail && typeof detail.message === 'string') return detail.message;
  if (err?.code === 'ERR_NETWORK') return 'The service could not be reached. Check that it is running.';
  return err?.message || fallback;
}

/** Times from the API without a zone are UTC. */
export function toDate(iso) {
  if (!iso) return null;
  const text = /[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`;
  const date = new Date(text);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function timeAgo(iso, now = Date.now()) {
  const date = toDate(iso);
  if (!date) return '–';
  const seconds = Math.max(0, Math.round((now - date.getTime()) / 1000));
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.round(seconds / 60)} min ago`;
  if (seconds < 86400) return `${Math.round(seconds / 3600)} h ago`;
  if (seconds < 86400 * 7) return `${Math.round(seconds / 86400)} d ago`;
  return date.toLocaleDateString();
}

export function formatDateTime(iso) {
  const date = toDate(iso);
  return date ? date.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : '–';
}

export function percent(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '–';
  return `${Number(value).toFixed(digits)}%`;
}

/** A small horizontal bar for a 0-100 share, coloured by how bad it is. */
export function RateBar({ value, warnAt = 10, dangerAt = 20 }) {
  const share = Math.max(0, Math.min(100, Number(value) || 0));
  const colour = share >= dangerAt ? 'bg-red-500' : share >= warnAt ? 'bg-amber-500' : 'bg-green-500';
  return (
    <span className="inline-flex items-center gap-2">
      <span className="h-1.5 w-16 overflow-hidden rounded-full bg-gray-100">
        <span className={clsx('block h-full rounded-full', colour)} style={{ width: `${share}%` }} />
      </span>
      <span className="tabular-nums">{percent(share)}</span>
    </span>
  );
}

export const tableClasses = {
  wrap: 'relative overflow-x-auto',
  table: 'w-full text-sm',
  head: 'border-b border-gray-200 bg-gray-50 text-left text-xs font-medium text-gray-500',
  th: 'px-4 py-2.5 font-medium',
  row: 'border-b border-gray-100 last:border-0 hover:bg-gray-50',
  td: 'px-4 py-3 text-gray-700',
};

export const inputClass =
  'block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30 disabled:bg-gray-50 disabled:text-gray-500';
