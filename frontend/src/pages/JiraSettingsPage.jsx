import { useEffect, useState } from 'react';
import { jiraApi } from '../api/client';
import { toast } from '../components/UI/Toast';
import {
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

export default function JiraSettingsPage() {
  const [config, setConfig] = useState({
    site_url: '',
    api_email: '',
    api_token: '',
    status_mapping: '{}',
    priority_mapping: '{}',
    sync_enabled: false,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const { data } = await jiraApi.getConfig();
        setConfig({
          site_url: data.site_url || '',
          api_email: data.api_email || '',
          api_token: data.api_token || '',
          status_mapping: typeof data.status_mapping === 'object'
            ? JSON.stringify(data.status_mapping, null, 2)
            : data.status_mapping || '{}',
          priority_mapping: typeof data.priority_mapping === 'object'
            ? JSON.stringify(data.priority_mapping, null, 2)
            : data.priority_mapping || '{}',
          sync_enabled: data.sync_enabled || false,
        });
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
      let statusMapping, priorityMapping;
      try {
        statusMapping = JSON.parse(config.status_mapping);
        priorityMapping = JSON.parse(config.priority_mapping);
      } catch {
        toast.error('Invalid JSON in mappings');
        setSaving(false);
        return;
      }
      await jiraApi.updateConfig({
        site_url: config.site_url,
        api_email: config.api_email,
        api_token: config.api_token,
        status_mapping: statusMapping,
        priority_mapping: priorityMapping,
        sync_enabled: config.sync_enabled,
      });
      toast.success('Jira configuration saved');
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
      const { data } = await jiraApi.testConnection();
      setTestResult({ success: true, message: data.message || 'Connection successful' });
    } catch (err) {
      setTestResult({ success: false, message: err.response?.data?.detail || 'Connection failed' });
    } finally {
      setTesting(false);
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
        <h1 className="text-2xl font-bold text-slate-800">Jira Integration</h1>
        <p className="text-sm text-slate-500 mt-1">Configure bidirectional sync with Jira</p>
      </div>

      <form onSubmit={handleSave} className="bg-white rounded-xl border border-slate-200 p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Site URL</label>
            <input
              type="url"
              value={config.site_url}
              onChange={(e) => setConfig((p) => ({ ...p, site_url: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="https://your-org.atlassian.net"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">API Email</label>
            <input
              type="email"
              value={config.api_email}
              onChange={(e) => setConfig((p) => ({ ...p, api_email: e.target.value }))}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="jira-service@company.com"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">API Token</label>
          <input
            type="password"
            value={config.api_token}
            onChange={(e) => setConfig((p) => ({ ...p, api_token: e.target.value }))}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Jira API token"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Status Mapping (JSON)</label>
          <textarea
            value={config.status_mapping}
            onChange={(e) => setConfig((p) => ({ ...p, status_mapping: e.target.value }))}
            rows={4}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder='{"new": "To Do", "in_progress": "In Progress", "resolved": "Done"}'
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Priority Mapping (JSON)</label>
          <textarea
            value={config.priority_mapping}
            onChange={(e) => setConfig((p) => ({ ...p, priority_mapping: e.target.value }))}
            rows={3}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder='{"P1": "Highest", "P2": "High", "P3": "Medium", "P4": "Low"}'
          />
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
            <input
              type="checkbox"
              checked={config.sync_enabled}
              onChange={(e) => setConfig((p) => ({ ...p, sync_enabled: e.target.checked }))}
              className="rounded"
            />
            Enable bidirectional sync
          </label>
        </div>

        {/* Test connection */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="button"
            onClick={handleTest}
            disabled={testing}
            className="flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50"
          >
            <ArrowPathIcon className={`w-4 h-4 ${testing ? 'animate-spin' : ''}`} />
            {testing ? 'Testing...' : 'Test Connection'}
          </button>
          {testResult && (
            <div className={`flex items-center gap-1.5 text-sm ${testResult.success ? 'text-green-600' : 'text-red-600'}`}>
              {testResult.success ? (
                <CheckCircleIcon className="w-4 h-4" />
              ) : (
                <XCircleIcon className="w-4 h-4" />
              )}
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
