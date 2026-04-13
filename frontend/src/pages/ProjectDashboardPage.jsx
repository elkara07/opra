import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { ticketApi, reportApi } from '../api/client';
import { ArrowLeftIcon, ExclamationTriangleIcon, ClockIcon, ArrowUpIcon } from '@heroicons/react/24/outline';

const PRIORITY_COLORS = {
  P1: 'bg-red-100 text-red-700 border-red-200',
  P2: 'bg-orange-100 text-orange-700 border-orange-200',
  P3: 'bg-blue-100 text-blue-700 border-blue-200',
  P4: 'bg-gray-100 text-gray-600 border-gray-200',
};

const STATUS_COLORS = {
  new: 'bg-blue-500', assigned: 'bg-indigo-500', in_progress: 'bg-yellow-500',
  pending_customer: 'bg-purple-500', pending_vendor: 'bg-purple-400',
  resolved: 'bg-green-500', closed: 'bg-gray-400', cancelled: 'bg-red-400',
};

export default function ProjectDashboardPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [projRes, ticketRes] = await Promise.all([
          api.get(`/projects/${projectId}`),
          ticketApi.list({ project_id: projectId, size: 200 }),
        ]);
        setProject(projRes.data);
        setTickets(ticketRes.data.items || []);
      } catch {} finally { setLoading(false); }
    }
    load();
  }, [projectId]);

  if (loading) {
    return <div className="p-6"><div className="animate-pulse h-8 w-48 bg-slate-200 rounded" /></div>;
  }

  if (!project) {
    return <div className="p-6 text-red-600">Project not found</div>;
  }

  const openStatuses = new Set(['new', 'assigned', 'in_progress', 'pending_customer', 'pending_vendor']);
  const activeTickets = tickets.filter(t => openStatuses.has(t.status));
  const breached = tickets.filter(t => t.sla_breached);
  const escalated = activeTickets.filter(t => t.current_escalation_level > 0);

  const byPriority = { P1: 0, P2: 0, P3: 0, P4: 0 };
  const byStatus = {};
  activeTickets.forEach(t => {
    byPriority[t.priority] = (byPriority[t.priority] || 0) + 1;
    byStatus[t.status] = (byStatus[t.status] || 0) + 1;
  });

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/')} className="p-2 rounded-lg hover:bg-slate-100">
          <ArrowLeftIcon className="w-5 h-5 text-slate-600" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-slate-800">{project.name}</h1>
          <div className="flex items-center gap-3 mt-1">
            <span className="font-mono text-sm text-slate-500">{project.code}</span>
            {project.jira_project_key && (
              <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-medium">
                Jira: {project.jira_project_key}
              </span>
            )}
          </div>
        </div>
        <button onClick={() => navigate(`/tickets?project_id=${projectId}`)}
          className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
          View All Tickets
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPI title="Active" value={activeTickets.length} icon={ExclamationTriangleIcon} color="bg-blue-50 text-blue-600" />
        <KPI title="Total" value={tickets.length} icon={ClockIcon} color="bg-slate-50 text-slate-600" />
        <KPI title="SLA Breached" value={breached.length} icon={ClockIcon} color="bg-red-50 text-red-600" />
        <KPI title="Escalated" value={escalated.length} icon={ArrowUpIcon} color="bg-amber-50 text-amber-600" />
      </div>

      {/* Priority breakdown */}
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <h2 className="text-sm font-semibold text-slate-700 mb-3">Active by Priority</h2>
        <div className="flex gap-3">
          {Object.entries(byPriority).map(([p, count]) => (
            <button key={p} onClick={() => navigate(`/tickets?project_id=${projectId}&priority=${p}`)}
              className={`flex-1 rounded-lg border px-4 py-3 text-center hover:shadow-md transition-shadow ${PRIORITY_COLORS[p]}`}>
              <span className="text-2xl font-bold">{count}</span>
              <span className="block text-xs font-medium mt-0.5">{p}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Status + Recent tickets */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">Status Distribution</h2>
          <div className="space-y-2">
            {Object.entries(byStatus).sort((a, b) => b[1] - a[1]).map(([status, count]) => {
              const pct = activeTickets.length ? Math.round(count / activeTickets.length * 100) : 0;
              return (
                <div key={status} className="flex items-center gap-3">
                  <span className="text-xs text-slate-500 w-32 truncate">{status.replace(/_/g, ' ')}</span>
                  <div className="flex-1 h-5 bg-slate-100 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${STATUS_COLORS[status] || 'bg-slate-300'}`} style={{ width: `${Math.max(pct, 4)}%` }} />
                  </div>
                  <span className="text-xs font-medium text-slate-600 w-10 text-right">{count}</span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">Recent Tickets</h2>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {tickets.slice(0, 10).map(t => (
              <button key={t.id} onClick={() => navigate(`/tickets/${t.id}`)}
                className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 text-left">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-xs font-mono text-slate-400">{t.ticket_number}</span>
                  <span className="text-sm text-slate-700 truncate">{t.subject}</span>
                </div>
                <span className={`px-2 py-0.5 rounded text-xs shrink-0 ${PRIORITY_COLORS[t.priority]}`}>{t.priority}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Escalated tickets */}
      {escalated.length > 0 && (
        <div className="bg-amber-50 rounded-xl border border-amber-200 p-5">
          <h2 className="text-sm font-semibold text-amber-800 mb-3">Escalated ({escalated.length})</h2>
          <div className="space-y-2">
            {escalated.map(t => (
              <button key={t.id} onClick={() => navigate(`/tickets/${t.id}`)}
                className="w-full flex items-center justify-between p-2 bg-white rounded-lg border border-amber-100 hover:border-amber-300 text-left">
                <span className="text-sm">{t.ticket_number} — {t.subject}</span>
                <span className="text-xs font-medium text-amber-700 bg-amber-100 px-2 py-0.5 rounded">L{t.current_escalation_level}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function KPI({ title, value, icon: Icon, color }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-500 uppercase">{title}</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{value}</p>
        </div>
        <div className={`p-2 rounded-lg ${color}`}><Icon className="w-5 h-5" /></div>
      </div>
    </div>
  );
}
