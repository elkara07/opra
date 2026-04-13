import { useEffect, useState } from 'react';
import { escalationApi } from '../api/client';
import { toast } from '../components/UI/Toast';
import { PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';

export default function EscalationPage() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    level: 'L1',
    threshold_minutes: 30,
    notify_team: '',
    notify_user: '',
    channels: 'email',
  });

  async function loadRules() {
    setLoading(true);
    try {
      const { data } = await escalationApi.list();
      setRules(data.items || data || []);
    } catch {
      toast.error('Failed to load escalation rules');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadRules();
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await escalationApi.create({
        ...form,
        threshold_minutes: Number(form.threshold_minutes),
        channels: form.channels.split(',').map((c) => c.trim()).filter(Boolean),
      });
      toast.success('Escalation rule created');
      setShowForm(false);
      setForm({ level: 'L1', threshold_minutes: 30, notify_team: '', notify_user: '', channels: 'email' });
      loadRules();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create rule');
    } finally {
      setSaving(false);
    }
  }

  const LEVEL_COLORS = {
    L1: 'bg-blue-100 text-blue-700',
    L2: 'bg-amber-100 text-amber-700',
    L3: 'bg-orange-100 text-orange-700',
    L4: 'bg-red-100 text-red-700',
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Escalation Rules</h1>
          <p className="text-sm text-slate-500 mt-1">Configure automatic escalation based on time thresholds</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          <PlusIcon className="w-4 h-4" />
          Add Rule
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-800">New Escalation Rule</h2>
            <button onClick={() => setShowForm(false)} className="text-slate-400 hover:text-slate-600">
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Level</label>
              <select
                value={form.level}
                onChange={(e) => setForm((p) => ({ ...p, level: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="L1">L1</option>
                <option value="L2">L2</option>
                <option value="L3">L3</option>
                <option value="L4">L4</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Threshold (minutes)</label>
              <input
                type="number"
                value={form.threshold_minutes}
                onChange={(e) => setForm((p) => ({ ...p, threshold_minutes: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                min={1}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Notify Team</label>
              <input
                type="text"
                value={form.notify_team}
                onChange={(e) => setForm((p) => ({ ...p, notify_team: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Team name or ID"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Notify User</label>
              <input
                type="text"
                value={form.notify_user}
                onChange={(e) => setForm((p) => ({ ...p, notify_user: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="User name or ID"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Channels (comma-separated)</label>
              <input
                type="text"
                value={form.channels}
                onChange={(e) => setForm((p) => ({ ...p, channels: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="email, sms, slack"
              />
            </div>
            <div className="flex items-end">
              <div className="flex gap-2">
                <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 text-sm text-slate-600">
                  Cancel
                </button>
                <button type="submit" disabled={saving} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
                  {saving ? 'Creating...' : 'Create'}
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              {['Level', 'Threshold', 'Notify Team', 'Notify User', 'Channels'].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-400">Loading...</td></tr>
            )}
            {!loading && rules.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-400">No escalation rules defined</td></tr>
            )}
            {!loading && rules.map((r, i) => (
              <tr key={r.id || i} className="border-b border-slate-100">
                <td className="px-4 py-3">
                  <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${LEVEL_COLORS[r.level] || 'bg-gray-100 text-gray-600'}`}>
                    {r.level}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-600">{r.threshold_minutes} min</td>
                <td className="px-4 py-3 text-slate-600">{r.notify_team || '-'}</td>
                <td className="px-4 py-3 text-slate-600">{r.notify_user || '-'}</td>
                <td className="px-4 py-3 text-slate-600">
                  {Array.isArray(r.channels) ? r.channels.join(', ') : r.channels || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
