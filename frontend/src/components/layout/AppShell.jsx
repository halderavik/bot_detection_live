// App frame: a grouped left sidebar on wide screens, a top bar with a slide-out menu on phones.

import React, { useEffect, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import clsx from 'clsx';
import {
  Activity,
  BookOpen,
  ClipboardList,
  FileText,
  LayoutDashboard,
  Menu,
  MessageSquare,
  Plug,
  Settings as SettingsIcon,
  ShieldCheck,
  TerminalSquare,
  Upload,
  Users,
  X,
} from 'lucide-react';
import { healthService } from '../../services/apiService';

export const NAV_GROUPS = [
  {
    label: 'Monitor',
    items: [
      { name: 'Overview', to: '/', icon: LayoutDashboard, end: true, match: ['/', '/dashboard', '/surveys'] },
      { name: 'Live Quality', to: '/quality', icon: ShieldCheck },
      { name: 'Sessions', to: '/sessions', icon: Users },
    ],
  },
  {
    label: 'Analyse',
    items: [
      { name: 'Open-end quality', to: '/text-analysis', icon: MessageSquare },
      { name: 'Reports', to: '/reports', icon: FileText },
    ],
  },
  {
    label: 'Set up',
    items: [
      { name: 'Add tracking', to: '/tracking', icon: Upload },
      { name: 'Manual setup', to: '/manual-setup', icon: ClipboardList },
      { name: 'Integrations', to: '/integrations', icon: Plug },
      { name: 'Settings', to: '/settings', icon: SettingsIcon },
    ],
  },
  {
    label: 'Developers',
    items: [
      { name: 'Quick start', to: '/quick-start', icon: BookOpen },
      { name: 'API playground', to: '/api-playground', icon: TerminalSquare },
    ],
  },
];

function isActive(item, pathname) {
  if (item.match) {
    return item.match.some((path) => (path === '/' ? pathname === '/' : pathname === path || pathname.startsWith(`${path}/`)));
  }
  return pathname === item.to || pathname.startsWith(`${item.to}/`);
}

function ServiceStatus() {
  const [status, setStatus] = useState('checking');
  useEffect(() => {
    let alive = true;
    const check = () =>
      healthService
        .checkHealth()
        .then((data) => alive && setStatus(data?.status === 'healthy' ? 'up' : 'degraded'))
        .catch(() => alive && setStatus('down'));
    check();
    const handle = window.setInterval(check, 60000);
    return () => {
      alive = false;
      window.clearInterval(handle);
    };
  }, []);
  const dot = { up: 'bg-green-500', degraded: 'bg-amber-500', down: 'bg-red-500', checking: 'bg-gray-300' }[status];
  const text = { up: 'Service running', degraded: 'Service degraded', down: 'Service unreachable', checking: 'Checking service…' }[status];
  return (
    <div className="flex items-center gap-2 px-3 text-xs text-gray-500" role="status">
      <span className={clsx('h-2 w-2 rounded-full', dot)} />
      {text}
    </div>
  );
}

function NavList({ onNavigate }) {
  const { pathname } = useLocation();
  return (
    <nav aria-label="Main" className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
      {NAV_GROUPS.map((group) => (
        <div key={group.label}>
          <p className="px-3 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-gray-400">{group.label}</p>
          <ul className="space-y-0.5">
            {group.items.map((item) => {
              const active = isActive(item, pathname);
              const Icon = item.icon;
              return (
                <li key={item.to}>
                  <NavLink
                    aria-current={active ? 'page' : undefined}
                    className={clsx(
                      'flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                      'focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500',
                      active ? 'bg-blue-50 text-blue-700' : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900',
                    )}
                    onClick={onNavigate}
                    to={item.to}
                  >
                    <Icon aria-hidden="true" className={clsx('h-4 w-4 shrink-0', active ? 'text-blue-600' : 'text-gray-400')} />
                    {item.name}
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}

function Brand() {
  return (
    <div className="flex items-center gap-2.5">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white">
        <Activity aria-hidden="true" className="h-4 w-4" />
      </span>
      <span className="text-[15px] font-semibold tracking-tight text-gray-900">Bot Detection</span>
    </div>
  );
}

export default function AppShell({ children }) {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();

  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (event) => event.key === 'Escape' && setOpen(false);
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  return (
    <div className="min-h-screen bg-gray-50">
      <a className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:rounded-md focus:bg-white focus:px-3 focus:py-2 focus:shadow" href="#main">
        Skip to content
      </a>

      {/* Wide screens: fixed sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-gray-200 bg-white lg:flex">
        <div className="flex h-16 items-center border-b border-gray-100 px-5">
          <Brand />
        </div>
        <NavList />
        <div className="border-t border-gray-100 py-3">
          <ServiceStatus />
        </div>
      </aside>

      {/* Phones and tablets: top bar and slide-out menu */}
      <div className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-gray-200 bg-white px-4 lg:hidden">
        <Brand />
        <button
          aria-expanded={open}
          aria-label="Open menu"
          className="rounded-lg p-2 text-gray-600 hover:bg-gray-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          onClick={() => setOpen(true)}
          type="button"
        >
          <Menu aria-hidden="true" className="h-5 w-5" />
        </button>
      </div>
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true" aria-label="Menu">
          <button aria-label="Close menu" className="absolute inset-0 bg-gray-900/40" onClick={() => setOpen(false)} type="button" />
          <div className="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col bg-white shadow-xl">
            <div className="flex h-14 items-center justify-between border-b border-gray-100 px-4">
              <Brand />
              <button
                aria-label="Close menu"
                className="rounded-lg p-2 text-gray-600 hover:bg-gray-100"
                onClick={() => setOpen(false)}
                type="button"
              >
                <X aria-hidden="true" className="h-5 w-5" />
              </button>
            </div>
            <NavList onNavigate={() => setOpen(false)} />
            <div className="border-t border-gray-100 py-3">
              <ServiceStatus />
            </div>
          </div>
        </div>
      )}

      <main className="lg:pl-60" id="main">
        <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">{children}</div>
      </main>
    </div>
  );
}
