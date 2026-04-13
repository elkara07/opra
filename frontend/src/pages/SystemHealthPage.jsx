import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import { toast } from '../components/UI/Toast';
import {
  ServerIcon,
  CircleStackIcon,
  CpuChipIcon,
  ArrowPathIcon,
  MapIcon,
} from '@heroicons/react/24/outline';

const SERVICE_ICONS = {
  postgres: CircleStackIcon,
  postgresql: CircleStackIcon,
  redis: CpuChipIcon,
  celery: ServerIcon,
  livekit: ServerIcon,
};

const STATUS_STYLES = {
  healthy: { bg: 'bg-green-50', border: 'border-green-200', dot: 'bg-green-500', text: 'text-green-700', label: 'Healthy' },
  ok: { bg: 'bg-green-50', border: 'border-green-200', dot: 'bg-green-500', text: 'text-green-700', label: 'OK' },
  unhealthy: { bg: 'bg-red-50', border: 'border-red-200', dot: 'bg-red-500', text: 'text-red-700', label: 'Unhealthy' },
  error: { bg: 'bg-red-50', border: 'border-red-200', dot: 'bg-red-500', text: 'text-red-700', label: 'Error' },
  degraded: { bg: 'bg-amber-50', border: 'border-amber-200', dot: 'bg-amber-500', text: 'text-amber-700', label: 'Degraded' },
  unknown: { bg: 'bg-gray-50', border: 'border-gray-200', dot: 'bg-gray-400', text: 'text-gray-600', label: 'Unknown' },
};

export default function SystemHealthPage() {
  const navigate = useNavigate();
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastCheck, setLastCheck] = useState(null);

  async function loadHealth() {
    setLoading(true);
    try {
      const { data } = await api.get('/system/health');
      setHealth(data);
      setLastCheck(new Date().toLocaleTimeString());
    } catch {
      toast.error('Failed to load system health');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const services = health?.services || [];
  const overallOk = health?.status === 'ok' || health?.status === 'healthy';

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">System Health</h1>
          {lastCheck && (
            <p className="text-xs text-slate-400 mt-1">Last check: {lastCheck} -- auto-refreshes every 30s</p>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate('/topology')}
            className="flex items-center gap-2 px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <MapIcon className="w-4 h-4" />
            Full Topology
          </button>
          <button
            onClick={loadHealth}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50"
          >
            <ArrowPathIcon className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Overall status banner */}
      {health && (
        <div className={`rounded-xl border p-4 ${overallOk ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'}`}>
          <div className="flex items-center gap-3">
            <div className={`w-4 h-4 rounded-full ${overallOk ? 'bg-green-500' : 'bg-amber-500'}`} />
            <div>
              <p className="text-sm font-semibold text-slate-800">
                {overallOk ? 'All systems operational' : 'Some services need attention'}
              </p>
              {health.uptime != null && (
                <p className="text-xs text-slate-500">
                  Uptime: {Math.floor(health.uptime / 3600)}h {Math.floor((health.uptime % 3600) / 60)}m
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Service cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {loading && services.length === 0 && (
          <>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-slate-200 rounded-xl animate-pulse" />
            ))}
          </>
        )}
        {services.map((svc, i) => {
          const s = STATUS_STYLES[svc.status] || STATUS_STYLES.unknown;
          const Icon = SERVICE_ICONS[svc.name?.toLowerCase()] || ServerIcon;
          return (
            <div key={i} className={`rounded-xl border p-4 ${s.bg} ${s.border}`}>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <Icon className="w-6 h-6 text-slate-600" />
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{svc.name}</p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <div className={`w-2 h-2 rounded-full ${s.dot}`} />
                      <span className={`text-xs font-medium ${s.text}`}>{s.label}</span>
                    </div>
                  </div>
                </div>
                {svc.latency != null && (
                  <span className="text-xs text-slate-500">{svc.latency}ms</span>
                )}
              </div>
              {svc.error && (
                <p className="text-xs text-red-600 mt-2 bg-red-50 rounded px-2 py-1">{svc.error}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
