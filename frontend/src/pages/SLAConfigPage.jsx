import { useEffect, useState } from 'react';
import { slaApi } from '../api/client';
import { toast } from '../components/UI/Toast';
import { PlusIcon, XMarkIcon } from '@heroicons/react/24/outline';

export default function SLAConfigPage() {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name: '',
    priority: 'P3',
    response_minutes: 60,
    update_minutes: 240,
    resolution_minutes: 480,
    escalation_thresholds: '{"warning": 50, "critical": 80}',
  });

  async function loadConfigs() {
    setLoading(true);
    try {
      const { data } = await slaApi.list();
      setConfigs(data.items || data || []);
    } catch {
      toast.error('Failed to load SLA configurations');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadConfigs();
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    setSaving(true);
    try {
      let thresholds;
      try {
        thresholds = JSON.parse(form.escalation_thresholds);
      } catch {
        toast.error('Invalid JSON for escalation thresholds');
        setSaving(false);
        return;
      }
      await slaApi.create({
        ...form,
        response_minutes: Number(form.response_minutes),
        update_minutes: Number(form.update_minutes),
        resolution_minutes: Number(form.resolution_minutes),
        escalation_thresholds: thresholds,
      });
      toast.success('SLA config created');
      setShowForm(false);
      loadConfigs();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create SLA config');
    } finally {
      setSaving(false);
    }
  }

  function formatMinutes(mins) {
    if (!mins) return '-';
    if (mins < 60) return `${mins}m`;
    return `${Math.floor(mins / 60)}h ${mins % 60 > 0 ? `${mins % 60}m` : ''}`.trim();
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">SLA Configuration</h1>
          <p className="text-sm text-slate-500 mt-1">Define response and resolution time targets by priority</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          <PlusIcon className="w-4 h-4" />
          Add SLA Config
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-800">New SLA Configuration</h2>
            <button onClick={() => setShowForm(false)} className="text-slate-400 hover:text-slate-600">
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., Critical SLA"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Priority</label>
              <select
                value={form.priority}
                onChange={(e) => setForm((p) => ({ ...p, priority: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="P1">P1 - Critical</option>
                <option value="P2">P2 - High</option>
                <option value="P3">P3 - Medium</option>
                <option value="P4">P4 - Low</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Response (minutes)</label>
              <input
                type="number"
                value={form.response_minutes}
                onChange={(e) => setForm((p) => ({ ...p, response_minutes: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                min={1}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Update (minutes)</label>
              <input
                type="number"
                value={form.update_minutes}
                onChange={(e) => setForm((p) => ({ ...p, update_minutes: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                min={1}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Resolution (minutes)</label>
              <input
                type="number"
                value={form.resolution_minutes}
                onChange={(e) => setForm((p) => ({ ...p, resolution_minutes: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                min={1}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Escalation Thresholds (JSON)</label>
              <input
                type="text"
                value={form.escalation_thresholds}
                onChange={(e) => setForm((p) => ({ ...p, escalation_thresholds: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="lg:col-span-3 flex justify-end gap-2">
              <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 text-sm text-slate-600">
                Cancel
              </button>
              <button type="submit" disabled={saving} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
                {saving ? 'Creating...' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              {['Name', 'Priority', 'Response', 'Update', 'Resolution', 'Thresholds'].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">Loading...</td>
              </tr>
            )}
            {!loading && configs.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">No SLA configs defined</td>
              </tr>
            )}
            {!loading &&
              configs.map((c, i) => (
                <tr key={c.id || i} className="border-b border-slate-100">
                  <td className="px-4 py-3 font-medium text-slate-800">{c.name}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${
                      c.priority === 'P1' ? 'bg-red-100 text-red-700' :
                      c.priority === 'P2' ? 'bg-orange-100 text-orange-700' :
                      c.priority === 'P3' ? 'bg-blue-100 text-blue-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {c.priority}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{formatMinutes(c.response_minutes)}</td>
                  <td className="px-4 py-3 text-slate-600">{formatMinutes(c.update_minutes)}</td>
                  <td className="px-4 py-3 text-slate-600">{formatMinutes(c.resolution_minutes)}</td>
                  <td className="px-4 py-3 text-xs font-mono text-slate-500">
                    {c.escalation_thresholds ? JSON.stringify(c.escalation_thresholds) : '-'}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Visual SLA timeline bars */}
      {configs.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-4">SLA Timeline Visualization</h2>
          <div className="space-y-3">
            {configs.map((c, i) => {
              const maxMins = c.resolution_minutes || 480;
              const responsePct = ((c.response_minutes || 0) / maxMins) * 100;
              const updatePct = ((c.update_minutes || 0) / maxMins) * 100;
              return (
                <div key={c.id || i}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium text-slate-600 w-24">{c.name}</span>
                    <span className="text-[10px] text-slate-400">{c.priority}</span>
                  </div>
                  <div className="relative h-4 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="absolute inset-y-0 left-0 bg-blue-300 rounded-full"
                      style={{ width: `${responsePct}%` }}
                      title={`Response: ${formatMinutes(c.response_minutes)}`}
                    />
                    <div
                      className="absolute inset-y-0 left-0 bg-amber-300 rounded-full opacity-50"
                      style={{ width: `${updatePct}%` }}
                      title={`Update: ${formatMinutes(c.update_minutes)}`}
                    />
                    <div className="absolute inset-y-0 left-0 right-0 bg-green-200 rounded-full opacity-30" />
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
                    <span>Response: {formatMinutes(c.response_minutes)}</span>
                    <span>Update: {formatMinutes(c.update_minutes)}</span>
                    <span>Resolution: {formatMinutes(c.resolution_minutes)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
