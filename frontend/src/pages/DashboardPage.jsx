import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { reportApi } from '../api/client';
import {
  ExclamationTriangleIcon,
  ClockIcon,
  ArrowUpIcon,
  PlusIcon,
  MapIcon,
  FolderIcon,
} from '@heroicons/react/24/outline';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [projectStats, setProjectStats] = useState([]);
  const [sla, setSla] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [projRes, slaRes] = await Promise.allSettled([
          api.get('/projects/stats'),
          reportApi.slaCompliance(7),
        ]);
        if (projRes.status === 'fulfilled') setProjectStats(projRes.value.data);
        if (slaRes.status === 'fulfilled') setSla(slaRes.value.data);
      } catch {} finally { setLoading(false); }
    }
    load();
  }, []);

  // Global aggregations
  const totalOpen = projectStats.reduce((s, p) => s + p.open_tickets, 0);
  const totalBreached = projectStats.reduce((s, p) => s + p.breached_tickets, 0);
  const totalEscalated = projectStats.reduce((s, p) => s + p.escalated_count, 0);
  const slaCompliancePct = sla?.data?.length
    ? Math.round(sla.data.reduce((sum, d) => sum + d.compliance_pct, 0) / sla.data.length)
    : null;

  if (loading) {
    return (
      <div className="p-6 animate-pulse space-y-6">
        <div className="h-8 w-48 bg-slate-200 rounded" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-24 bg-slate-200 rounded-xl" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Operations Dashboard</h1>
        <div className="flex gap-2">
          <button onClick={() => navigate('/tickets?new=1')} className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
            <PlusIcon className="w-4 h-4" /> New Ticket
          </button>
          <button onClick={() => navigate('/topology')} className="flex items-center gap-2 px-3 py-2 bg-slate-700 text-white rounded-lg text-sm hover:bg-slate-800">
            <MapIcon className="w-4 h-4" /> Topology
          </button>
        </div>
      </div>

      {/* Global KPI Summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPI title="Total Open" value={totalOpen} icon={ExclamationTriangleIcon} color="bg-blue-50 text-blue-600" />
        <KPI title="SLA Compliance" value={slaCompliancePct != null ? `${slaCompliancePct}%` : '—'} icon={ClockIcon}
          color={slaCompliancePct == null ? 'bg-slate-50 text-slate-600' : slaCompliancePct >= 90 ? 'bg-green-50 text-green-600' : slaCompliancePct >= 70 ? 'bg-amber-50 text-amber-600' : 'bg-red-50 text-red-600'} />
        <KPI title="SLA Breached" value={totalBreached} icon={ClockIcon} color="bg-red-50 text-red-600" />
        <KPI title="Escalated" value={totalEscalated} icon={ArrowUpIcon} color="bg-amber-50 text-amber-600" />
      </div>

      {/* SLA by Priority */}
      {sla?.data && sla.data.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-3">SLA Compliance by Priority (7 days)</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {sla.data.map(d => (
              <div key={d.priority} className="text-center p-3 rounded-lg bg-slate-50">
                <p className="text-xs text-slate-500 mb-1">{d.priority}</p>
                <p className={`text-xl font-bold ${d.compliance_pct >= 90 ? 'text-green-600' : d.compliance_pct >= 70 ? 'text-amber-600' : 'text-red-600'}`}>
                  {d.compliance_pct}%
                </p>
                <p className="text-xs text-slate-400">{d.total} tickets</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Project Cards */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-slate-800">Projects</h2>
          <button onClick={() => navigate('/projects')} className="text-sm text-blue-600 hover:underline">Manage Projects</button>
        </div>

        {projectStats.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
            <FolderIcon className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500">No projects yet.</p>
            <button onClick={() => navigate('/projects')} className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm">Create Project</button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projectStats.map(proj => (
              <button key={proj.id} onClick={() => navigate(`/projects/${proj.id}/dashboard`)}
                className="bg-white rounded-xl border border-slate-200 p-5 text-left hover:shadow-lg hover:border-blue-200 transition-all group">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-semibold text-slate-800 group-hover:text-blue-700">{proj.name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="font-mono text-xs text-slate-400">{proj.code}</span>
                      {proj.jira_project_key && (
                        <span className="px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded text-xs">{proj.jira_project_key}</span>
                      )}
                    </div>
                  </div>
                  {proj.escalated_count > 0 && (
                    <span className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded text-xs font-medium">
                      {proj.escalated_count} esc.
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-2 mb-3">
                  <Stat label="Open" value={proj.open_tickets} />
                  <Stat label="Total" value={proj.total_tickets} />
                  <Stat label="Breached" value={proj.breached_tickets} warn={proj.breached_tickets > 0} />
                </div>

                {/* Priority mini-bars */}
                <div className="flex gap-1">
                  {['P1', 'P2', 'P3', 'P4'].map(p => {
                    const count = proj.by_priority[p] || 0;
                    const total = proj.open_tickets || 1;
                    const pct = Math.max(count > 0 ? 10 : 0, (count / total) * 100);
                    return (
                      <div key={p} className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden" title={`${p}: ${count}`}>
                        <div className={`h-full rounded-full ${p === 'P1' ? 'bg-red-500' : p === 'P2' ? 'bg-orange-500' : p === 'P3' ? 'bg-blue-500' : 'bg-gray-400'}`}
                          style={{ width: `${pct}%` }} />
                      </div>
                    );
                  })}
                </div>
                <div className="flex justify-between mt-1">
                  {['P1', 'P2', 'P3', 'P4'].map(p => (
                    <span key={p} className="text-xs text-slate-400">{proj.by_priority[p] || 0}</span>
                  ))}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function KPI({ title, value, icon: Icon, color }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wide">{title}</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{value}</p>
        </div>
        <div className={`p-2 rounded-lg ${color}`}><Icon className="w-5 h-5" /></div>
      </div>
    </div>
  );
}

function Stat({ label, value, warn }) {
  return (
    <div className={`text-center p-2 rounded-lg ${warn ? 'bg-red-50' : 'bg-slate-50'}`}>
      <p className={`text-lg font-bold ${warn ? 'text-red-600' : 'text-slate-800'}`}>{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}
