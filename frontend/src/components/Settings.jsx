// Settings: the keys and options the service really uses. Saved values override the
// service's environment variables; secrets are never shown again once saved.

import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { KeyRound, Lock, LockOpen, RotateCcw, Save, ShieldCheck } from 'lucide-react';
import { toast } from 'react-toastify';
import { settingsService } from '../services/apiService';
import { Badge, Button, Card, ErrorBanner, Loading, PageHeader, apiError, inputClass } from './ui';

const TOKEN_KEY = 'bd_admin_token';

function readToken() {
  try {
    return window.sessionStorage.getItem(TOKEN_KEY) || '';
  } catch (e) {
    return '';
  }
}

function storeToken(token) {
  try {
    if (token) window.sessionStorage.setItem(TOKEN_KEY, token);
    else window.sessionStorage.removeItem(TOKEN_KEY);
  } catch (e) {
    // private window: the token simply isn't remembered
  }
}

function SourceBadge({ item }) {
  if (item.source === 'saved') return <Badge tone="accent">Saved here</Badge>;
  if (item.source === 'environment') return <Badge>From environment</Badge>;
  return <Badge tone="warn">Not set</Badge>;
}

function UnlockCard({ onUnlocked }) {
  const [token, setToken] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function unlock(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      await settingsService.checkToken(token.trim());
      storeToken(token.trim());
      onUnlocked(token.trim());
    } catch (err) {
      setError(apiError(err, 'The admin token was not accepted.'));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <form className="flex flex-wrap items-end gap-3" onSubmit={unlock}>
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gray-100 text-gray-600">
          <Lock aria-hidden="true" className="h-5 w-5" />
        </span>
        <div className="min-w-[14rem] flex-1">
          <label className="text-sm font-medium text-gray-900" htmlFor="admin-token">Admin token</label>
          <p className="text-xs text-gray-500">Settings are shown read-only. Enter the service&apos;s ADMIN_TOKEN to change them.</p>
          <input
            autoComplete="off"
            className={`${inputClass} mt-1.5 max-w-sm`}
            id="admin-token"
            onChange={(event) => setToken(event.target.value)}
            type="password"
            value={token}
          />
        </div>
        <Button disabled={!token.trim() || busy} icon={LockOpen} type="submit" variant="primary">
          {busy ? 'Checking…' : 'Unlock'}
        </Button>
        {error && <p className="w-full text-sm text-red-700" role="alert">{error}</p>}
      </form>
    </Card>
  );
}

function SettingRow({ item, draft, unlocked, onChange }) {
  const id = `setting-${item.key}`;
  const changed = Object.prototype.hasOwnProperty.call(draft, item.key);
  const value = changed ? draft[item.key] : item.value;
  const resetting = changed && draft[item.key] === null;
  return (
    <div className="grid gap-3 border-b border-gray-100 py-4 last:border-0 md:grid-cols-[minmax(0,1fr)_minmax(0,22rem)]">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-sm font-medium text-gray-900" htmlFor={id}>{item.label}</label>
          <SourceBadge item={item} />
          {changed && <Badge tone="warn">{resetting ? 'Will use environment' : 'Unsaved'}</Badge>}
        </div>
        <p className="mt-0.5 text-xs text-gray-500">{item.help}</p>
        <p className="mt-0.5 font-mono text-[11px] text-gray-400">{item.key}</p>
      </div>
      <div className="min-w-0 space-y-1.5">
        {item.kind === 'secret' ? (
          <>
            <input
              autoComplete="new-password"
              className={inputClass}
              disabled={!unlocked || resetting}
              id={id}
              onChange={(event) => onChange(item.key, event.target.value || undefined)}
              placeholder={item.is_set ? 'Set (hidden). Type to replace.' : 'Not set'}
              type="password"
              value={changed && !resetting ? value || '' : ''}
            />
          </>
        ) : (
          <input
            className={inputClass}
            disabled={!unlocked || resetting}
            id={id}
            inputMode={item.kind === 'number' ? 'decimal' : undefined}
            max={item.maximum ?? undefined}
            min={item.minimum ?? undefined}
            onChange={(event) => onChange(item.key, event.target.value)}
            placeholder={item.placeholder || ''}
            step={item.kind === 'number' ? 0.05 : undefined}
            type={item.kind === 'number' ? 'number' : 'text'}
            value={resetting ? item.environment_value ?? '' : value ?? ''}
          />
        )}
        {unlocked && item.source === 'saved' && !resetting && (
          <button className="text-xs font-medium text-blue-600 hover:underline" onClick={() => onChange(item.key, null)} type="button">
            Remove saved value and use the environment
          </button>
        )}
        {resetting && (
          <button className="text-xs font-medium text-blue-600 hover:underline" onClick={() => onChange(item.key, undefined)} type="button">
            Keep the saved value
          </button>
        )}
      </div>
    </div>
  );
}

const Settings = () => {
  const [state, setState] = useState(null);
  const [error, setError] = useState('');
  const [token, setToken] = useState(readToken());
  const [draft, setDraft] = useState({});
  const [saving, setSaving] = useState(false);

  const load = () => {
    setError('');
    settingsService.get().then(setState).catch((err) => setError(apiError(err, 'Settings could not be loaded.')));
  };
  useEffect(load, []);

  const groups = useMemo(() => {
    const map = new Map();
    (state?.settings || []).forEach((item) => {
      if (!map.has(item.group)) map.set(item.group, []);
      map.get(item.group).push(item);
    });
    return [...map.entries()];
  }, [state]);

  const unlocked = Boolean(state?.editable && token);
  const pending = Object.keys(draft).length;

  function change(key, value) {
    setDraft((current) => {
      const next = { ...current };
      const item = state.settings.find((entry) => entry.key === key);
      if (value === undefined || (value !== null && item.kind !== 'secret' && String(value) === String(item.value ?? ''))) {
        delete next[key];
      } else {
        next[key] = value;
      }
      return next;
    });
  }

  async function save() {
    setSaving(true);
    try {
      const changes = {};
      Object.entries(draft).forEach(([key, value]) => {
        changes[key] = value === '' ? null : value;
      });
      setState(await settingsService.save(token, changes));
      setDraft({});
      toast.success('Settings saved. Other instances pick them up within 30 seconds.');
    } catch (err) {
      if (err?.response?.status === 401) {
        storeToken('');
        setToken('');
        toast.error('The admin token is no longer accepted. Unlock again.');
      } else {
        toast.error(apiError(err, 'Settings were not saved.'));
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        actions={
          unlocked ? (
            <Button
              icon={Lock}
              onClick={() => {
                storeToken('');
                setToken('');
                setDraft({});
              }}
              variant="ghost"
            >
              Lock
            </Button>
          ) : null
        }
        description="Keys and options this service uses. A value saved here overrides the service's environment variable of the same name and applies at once (other instances within 30 seconds). Saved keys are stored encrypted and never shown again."
        title="Settings"
      />

      {error && <ErrorBanner onRetry={load}>{error}</ErrorBanner>}
      {!state && !error && <Loading label="Loading settings…" />}

      {state && !state.editable && (
        <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <KeyRound aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0" />
          <p>
            Read-only. To change settings here, set <code className="font-mono">ADMIN_TOKEN</code> on the service and restart it.
            Until then, values come from the service&apos;s environment variables.
          </p>
        </div>
      )}
      {state && state.editable && !token && <UnlockCard onUnlocked={setToken} />}

      {state &&
        groups.map(([group, items]) => (
          <Card key={group} title={group} bodyClassName="py-0">
            {items.map((item) => (
              <SettingRow draft={draft} item={item} key={item.key} onChange={change} unlocked={unlocked} />
            ))}
          </Card>
        ))}

      {state && (
        <Card>
          <div className="flex items-start gap-3 text-sm text-gray-600">
            <ShieldCheck aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-gray-400" />
            <p>
              What counts as a bot, a speeder or a poor answer for one survey is set per survey on{' '}
              <Link className="font-medium text-blue-600 hover:underline" to="/quality">Live Quality</Link>. The bot threshold above
              is the service-wide verdict stored with each new analysis.
            </p>
          </div>
        </Card>
      )}

      {unlocked && pending > 0 && (
        <div className="sticky bottom-4 z-10 flex flex-wrap items-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-lg">
          <span className="text-sm text-gray-700">{pending} unsaved {pending === 1 ? 'change' : 'changes'}</span>
          <span className="flex-1" />
          <Button disabled={saving} icon={RotateCcw} onClick={() => setDraft({})} variant="ghost">Discard</Button>
          <Button disabled={saving} icon={Save} onClick={save} variant="primary">{saving ? 'Saving…' : 'Save changes'}</Button>
        </div>
      )}
    </div>
  );
};

export default Settings;
