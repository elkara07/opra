import { useEffect, useState } from 'react';
import { ldapApi } from '../api/client';
import { toast } from '../components/UI/Toast';
import {
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

export default function LDAPSettingsPage() {
  const [config, setConfig] = useState({
    server_url: '',
    bind_dn: '',
    bind_password: '',
    base_dn: '',
    user_search_filter: '(objectClass=user)',
    role_mapping: '{}',
    sync_enabled: false,
    sync_interval: 3600,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [lastSync, setLastSync] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const { data } = await ldapApi.getConfig();
        setConfig({
          server_url: data.server_url || '',
          bind_dn: data.bind_dn || '',
          bind_password: data.bind_password || '',
          base_dn: data.base_dn || '',
          user_search_filter: data.user_search_filter || '(objectClass=user)',
          role_mapping: typeof data.role_mapping === 'object'
            ? JSON.stringify(data.role_mapping, null, 2)
            : data.role_mapping || '{}',
          sync_enabled: data.sync_enabled || false,
          sync_interval: data.sync_interval || 3600,
        });
        if (data.last_sync_at) setLastSync(data.last_sync_at);
      } catch {
        // Config may not exist yet
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleSave(e) {
    e.preventDefault();
    setSaving(true);
    try {
      let roleMapping;
      try {
        roleMapping = JSON.parse(config.role_mapping);
      } catch {
        toast.error('Invalid JSON in role mapping');
        setSaving(false);
        return;
      }
      await ldapApi.updateConfig({
        ...config,
        sync_interval: Number(config.sync_interval),
        role_mapping: roleMapping,
      });
      toast.success('LDAP configuration saved');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save config');
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    setTesting(true);
    setTestResult(null);
    try {
      const { data } = await ldapApi.testConnection();
      setTestResult({ success: true, message: data.message || 'Connection successful' });
    } catch (err) {
      setTestResult({ success: false, message: err.response?.data?.detail || 'Connection failed' });
    } finally {
      setTesting(false);
    }
  }

  async function handleSync() {
    setSyncing(true);
    try {
      const { data } = await ldapApi.triggerSync();
      toast.success(data.message || 'Sync triggered');
      setLastSync(new Date().toISOString());
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Sync failed');
    } finally {
      setSyncing(false);
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 bg-slate-200 rounded" />
          <div className="h-64 bg-slate-200 rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">LDAP / Active Directory</h1>
        <p className="text-sm text-slate-500 mt-1">Configure user synchronization from LDAP/AD</p>
      </div>

      <form onSubmit={handleSave} className="bg-white rounded-xl border border-slate-200 p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Server URL</label>
            <input
              type="text"
              value={config.server_url}
              onChange={(e) => setConfig((p) => ({ ...p, server_url: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="ldaps://ldap.company.com:636"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Base DN</label>
            <input
              type="text"
              value={config.base_dn}
              onChange={(e) => setConfig((p) => ({ ...p, base_dn: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="DC=company,DC=com"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Bind DN</label>
            <input
              type="text"
              value={config.bind_dn}
              onChange={(e) => setConfig((p) => ({ ...p, bind_dn: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="CN=service,OU=Users,DC=company,DC=com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Bind Password</label>
            <input
              type="password"
              value={config.bind_password}
              onChange={(e) => setConfig((p) => ({ ...p, bind_password: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">User Search Filter</label>
          <input
            type="text"
            value={config.user_search_filter}
            onChange={(e) => setConfig((p) => ({ ...p, user_search_filter: e.target.value }))}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="(objectClass=user)"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Role Mapping (JSON)</label>
          <textarea
            value={config.role_mapping}
            onChange={(e) => setConfig((p) => ({ ...p, role_mapping: e.target.value }))}
            rows={4}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder='{"CN=Admins,OU=Groups,DC=co,DC=com": "admin", "CN=Agents,OU=Groups,DC=co,DC=com": "agent"}'
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
              <input
                type="checkbox"
                checked={config.sync_enabled}
                onChange={(e) => setConfig((p) => ({ ...p, sync_enabled: e.target.checked }))}
                className="rounded"
              />
              Enable auto sync
            </label>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Sync Interval (seconds)</label>
            <input
              type="number"
              value={config.sync_interval}
              onChange={(e) => setConfig((p) => ({ ...p, sync_interval: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              min={60}
            />
          </div>
        </div>

        {/* Last sync info */}
        {lastSync && (
          <div className="text-xs text-slate-500 bg-slate-50 rounded-lg px-3 py-2">
            Last sync: {new Date(lastSync).toLocaleString()}
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-wrap items-center gap-3 pt-2">
          <button
            type="button"
            onClick={handleTest}
            disabled={testing}
            className="flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50"
          >
            <ArrowPathIcon className={`w-4 h-4 ${testing ? 'animate-spin' : ''}`} />
            {testing ? 'Testing...' : 'Test Connection'}
          </button>
          <button
            type="button"
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50"
          >
            <ArrowPathIcon className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing...' : 'Trigger Sync'}
          </button>
          {testResult && (
            <div className={`flex items-center gap-1.5 text-sm ${testResult.success ? 'text-green-600' : 'text-red-600'}`}>
              {testResult.success ? <CheckCircleIcon className="w-4 h-4" /> : <XCircleIcon className="w-4 h-4" />}
              {testResult.message}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </form>
    </div>
  );
}
