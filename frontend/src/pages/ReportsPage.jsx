import { useEffect, useState } from 'react';
import { reportApi } from '../api/client';
import { toast } from '../components/UI/Toast';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

const PERIOD_OPTIONS = [
  { value: 7, label: '7 days' },
  { value: 30, label: '30 days' },
  { value: 90, label: '90 days' },
];

const COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899'];

const TABS = ['SLA Compliance', 'Ticket Volume', 'Escalation', 'Agent Performance', 'Call Analytics'];

export default function ReportsPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [period, setPeriod] = useState(30);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({});

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [sla, volume, escalation, agents, calls] = await Promise.allSettled([
          reportApi.slaCompliance(period),
          reportApi.ticketVolume(period),
          reportApi.escalationFrequency(period),
          reportApi.agentPerformance(period),
          reportApi.callAnalytics(period),
        ]);
        setData({
          sla: sla.status === 'fulfilled' ? sla.value.data : null,
          volume: volume.status === 'fulfilled' ? volume.value.data : null,
          escalation: escalation.status === 'fulfilled' ? escalation.value.data : null,
          agents: agents.status === 'fulfilled' ? agents.value.data : null,
          calls: calls.status === 'fulfilled' ? calls.value.data : null,
        });
      } catch {
        toast.error('Failed to load reports');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [period]);

  function renderSLA() {
    const items = data.sla?.by_priority || data.sla?.items || [];
    if (items.length === 0) return <EmptyState />;
    return (
      <div className="space-y-4">
        {data.sla?.compliance_pct != null && (
          <div className="text-center">
            <span className="text-4xl font-bold text-slate-800">{data.sla.compliance_pct}%</span>
            <p className="text-sm text-slate-500">Overall SLA Compliance</p>
          </div>
        )}
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={items}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="priority" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="compliance_pct" name="Compliance %" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="breached" name="Breached" fill="#ef4444" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  function renderVolume() {
    const items = data.volume?.by_date || data.volume?.items || [];
    if (items.length === 0) return <EmptyState />;
    return (
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={items}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="email" stroke="#3b82f6" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="phone" stroke="#10b981" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="web" stroke="#f59e0b" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="total" stroke="#6b7280" strokeWidth={2} strokeDasharray="5 5" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    );
  }

  function renderEscalation() {
    const items = data.escalation?.by_level || data.escalation?.items || [];
    if (items.length === 0) return <EmptyState />;
    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={items} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis type="number" tick={{ fontSize: 12 }} />
          <YAxis dataKey="level" type="category" tick={{ fontSize: 12 }} width={40} />
          <Tooltip />
          <Bar dataKey="count" name="Escalations" fill="#f59e0b" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    );
  }

  function renderAgents() {
    const items = data.agents?.items || data.agents || [];
    if (!Array.isArray(items) || items.length === 0) return <EmptyState />;
    return (
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              {['Agent', 'Tickets Handled', 'Avg Response (min)', 'Avg Resolution (min)', 'SLA %', 'CSAT'].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map((a, i) => (
              <tr key={i} className="border-b border-slate-100">
                <td className="px-4 py-3 font-medium text-slate-800">{a.agent_name || a.name || '-'}</td>
                <td className="px-4 py-3 text-slate-600">{a.tickets_handled ?? '-'}</td>
                <td className="px-4 py-3 text-slate-600">{a.avg_response_minutes ?? '-'}</td>
                <td className="px-4 py-3 text-slate-600">{a.avg_resolution_minutes ?? '-'}</td>
                <td className="px-4 py-3">
                  <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${
                    (a.sla_pct || 0) >= 90 ? 'bg-green-100 text-green-700' :
                    (a.sla_pct || 0) >= 70 ? 'bg-amber-100 text-amber-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {a.sla_pct ?? '-'}%
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-600">{a.csat ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  function renderCalls() {
    const callData = data.calls;
    if (!callData) return <EmptyState />;
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Total Calls', value: callData.total_calls ?? 0 },
            { label: 'Avg Duration', value: callData.avg_duration ? `${Math.round(callData.avg_duration)}s` : '-' },
            { label: 'Answered', value: callData.answered ?? 0 },
            { label: 'Missed', value: callData.missed ?? 0 },
          ].map((c) => (
            <div key={c.label} className="bg-slate-50 rounded-lg p-3 text-center">
              <p className="text-xl font-bold text-slate-800">{c.value}</p>
              <p className="text-xs text-slate-500">{c.label}</p>
            </div>
          ))}
        </div>
        {callData.by_date && callData.by_date.length > 0 && (
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={callData.by_date}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="calls" name="Calls" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    );
  }

  function EmptyState() {
    return (
      <div className="py-12 text-center text-slate-400 text-sm">
        No data available for this period
      </div>
    );
  }

  const tabRenderers = [renderSLA, renderVolume, renderEscalation, renderAgents, renderCalls];

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-slate-800">Reports</h1>
        <select
          value={period}
          onChange={(e) => setPeriod(Number(e.target.value))}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {PERIOD_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <div className="flex gap-0 overflow-x-auto">
          {TABS.map((tab, i) => (
            <button
              key={tab}
              onClick={() => setActiveTab(i)}
              className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                activeTab === i
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        {loading ? (
          <div className="py-12 text-center text-slate-400">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto" />
            <p className="mt-3 text-sm">Loading reports...</p>
          </div>
        ) : (
          tabRenderers[activeTab]()
        )}
      </div>
    </div>
  );
}
