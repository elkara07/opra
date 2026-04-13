import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/client';
import {
  ArrowLeftIcon,
  Cog6ToothIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

const STATUS_COLORS = {
  ok: { bg: 'bg-green-50', border: 'border-green-300', dot: 'bg-green-500', text: 'text-green-700' },
  warning: { bg: 'bg-amber-50', border: 'border-amber-300', dot: 'bg-amber-500', text: 'text-amber-700' },
  error: { bg: 'bg-red-50', border: 'border-red-300', dot: 'bg-red-500', text: 'text-red-700' },
  not_configured: { bg: 'bg-gray-50', border: 'border-gray-300', dot: 'bg-gray-400', text: 'text-gray-600' },
  disabled: { bg: 'bg-gray-50', border: 'border-gray-200', dot: 'bg-gray-300', text: 'text-gray-500' },
};

// Each node navigates to its specific config section
const CONFIG_ROUTES_FALLBACK = {
  stt: '/settings/voice?tab=stt',
  llm: '/settings/voice?tab=llm',
  tts: '/settings/voice?tab=tts',
  pbx: '/settings/voice?tab=general',
  sip_bridge: '/settings/voice?tab=general',
  livekit: '/settings/voice?tab=general',
  pipecat: '/settings/voice?tab=general',
  phone_ingest: '/settings/voice?tab=general',
  email_ingest: '/settings/email',
  notification: '/settings/email',
  jira: '/settings/jira',
  ldap: '/settings/ldap',
  sla_engine: '/settings/sla',
  escalation_engine: '/settings/escalation',
  ticket_engine: '/tickets',
  postgres: '/system',
  redis: '/system',
  minio: '/system',
};

export default function NodeDetailPage() {
  const { nodeId } = useParams();
  const navigate = useNavigate();
  const [nodeInfo, setNodeInfo] = useState(null);
  const [topology, setTopology] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      // Get topology for node basic info
      const { data: topoData } = await api.get('/system/topology');
      setTopology(topoData);
      const node = (topoData.nodes || []).find((n) => n.id === nodeId);
      setNodeInfo(node || { id: nodeId, label: nodeId, status: 'unknown', error: null });

      // Get node detail
      try {
        const { data: detailData } = await api.get(`/system/topology/${nodeId}`);
        setDetail(detailData);
      } catch {
        setDetail(null);
      }
    } catch {
      setNodeInfo({ id: nodeId, label: nodeId, status: 'error', error: 'Failed to load' });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [nodeId]);

  if (loading) {
    return (
      <div className="p-6 flex items-center gap-3">
        <ArrowPathIcon className="w-5 h-5 animate-spin text-blue-600" />
        <span className="text-slate-600">Loading component details...</span>
      </div>
    );
  }

  const status = nodeInfo?.status || 'unknown';
  const colors = STATUS_COLORS[status] || STATUS_COLORS.not_configured;
  // Use backend config_url first, fallback to static map
  const configRoute = detail?.config_url || CONFIG_ROUTES_FALLBACK[nodeId] || null;

  // Find connected nodes (edges from/to this node)
  const connectedFrom = (topology?.edges || []).filter((e) => e.to === nodeId);
  const connectedTo = (topology?.edges || []).filter((e) => e.from === nodeId);

  return (
    <div className="p-6 max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/topology')} className="p-2 rounded-lg hover:bg-slate-100">
          <ArrowLeftIcon className="w-5 h-5 text-slate-600" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-slate-800">{nodeInfo?.label || nodeId}</h1>
          <p className="text-sm text-slate-500">Component: {nodeId} &middot; Group: {nodeInfo?.group || '—'}</p>
        </div>
        {configRoute && (
          <button
            onClick={() => navigate(configRoute)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
          >
            <Cog6ToothIcon className="w-4 h-4" />
            Configure
          </button>
        )}
      </div>

      {/* Status Card */}
      <div className={`rounded-xl border-2 p-5 ${colors.bg} ${colors.border}`}>
        <div className="flex items-center gap-3">
          <div className={`w-4 h-4 rounded-full ${colors.dot} ring-4 ${colors.dot === 'bg-green-500' ? 'ring-green-100' : colors.dot === 'bg-red-500' ? 'ring-red-100' : 'ring-amber-100'}`} />
          <div>
            <p className={`text-lg font-semibold ${colors.text}`}>
              {status === 'ok' ? 'Operational' : status === 'warning' ? 'Degraded' : status === 'error' ? 'Down / Error' : status === 'not_configured' ? 'Not Configured' : 'Disabled'}
            </p>
            {nodeInfo?.latency_ms && (
              <p className="text-sm text-slate-500">Latency: {nodeInfo.latency_ms}ms</p>
            )}
          </div>
        </div>
        {nodeInfo?.error && (
          <div className="mt-3 p-3 bg-red-100 border border-red-200 rounded-lg">
            <p className="text-sm font-mono text-red-800">{nodeInfo.error}</p>
          </div>
        )}
      </div>

      {/* Detail Info */}
      {detail && (
        <div className="rounded-xl border border-slate-200 p-5">
          <h2 className="text-lg font-semibold text-slate-800 mb-3">Component Details</h2>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(detail).filter(([k]) => k !== 'node_id').map(([key, value]) => (
              <div key={key} className="flex flex-col">
                <dt className="text-xs font-medium text-slate-500 uppercase">{key.replace(/_/g, ' ')}</dt>
                <dd className="text-sm text-slate-800 mt-0.5">
                  {typeof value === 'object' && value !== null ? (
                    <pre className="text-xs bg-slate-50 p-2 rounded overflow-x-auto">{JSON.stringify(value, null, 2)}</pre>
                  ) : value === null || value === undefined ? (
                    <span className="text-slate-400">—</span>
                  ) : typeof value === 'boolean' ? (
                    <span className={value ? 'text-green-600' : 'text-red-600'}>{value ? 'Yes' : 'No'}</span>
                  ) : (
                    String(value)
                  )}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      )}

      {/* Connection Map */}
      <div className="rounded-xl border border-slate-200 p-5">
        <h2 className="text-lg font-semibold text-slate-800 mb-3">Connections</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Incoming */}
          <div>
            <h3 className="text-sm font-medium text-slate-500 mb-2">Incoming</h3>
            {connectedFrom.length === 0 ? (
              <p className="text-sm text-slate-400">No incoming connections</p>
            ) : (
              <ul className="space-y-1">
                {connectedFrom.map((e, i) => {
                  const fromNode = (topology?.nodes || []).find((n) => n.id === e.from);
                  return (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <span className="text-slate-400">&larr;</span>
                      <button
                        onClick={() => navigate(`/topology/${e.from}`)}
                        className="text-blue-600 hover:underline"
                      >
                        {fromNode?.label || e.from}
                      </button>
                      <span className="text-xs text-slate-400">({e.label})</span>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
          {/* Outgoing */}
          <div>
            <h3 className="text-sm font-medium text-slate-500 mb-2">Outgoing</h3>
            {connectedTo.length === 0 ? (
              <p className="text-sm text-slate-400">No outgoing connections</p>
            ) : (
              <ul className="space-y-1">
                {connectedTo.map((e, i) => {
                  const toNode = (topology?.nodes || []).find((n) => n.id === e.to);
                  return (
                    <li key={i} className="flex items-center gap-2 text-sm">
                      <span className="text-slate-400">&rarr;</span>
                      <button
                        onClick={() => navigate(`/topology/${e.to}`)}
                        className="text-blue-600 hover:underline"
                      >
                        {toNode?.label || e.to}
                      </button>
                      <span className="text-xs text-slate-400">({e.label})</span>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>
      </div>

      {/* Action buttons based on node type */}
      {status === 'not_configured' && configRoute && (
        <div className="rounded-xl border-2 border-dashed border-blue-200 bg-blue-50 p-5 text-center">
          <p className="text-sm text-blue-700 mb-3">This component is not configured yet. Set it up to enable this part of the pipeline.</p>
          <button
            onClick={() => navigate(configRoute)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
          >
            Configure Now
          </button>
        </div>
      )}

      {status === 'error' && (
        <div className="rounded-xl border-2 border-dashed border-red-200 bg-red-50 p-5">
          <p className="text-sm text-red-700 font-medium mb-1">Troubleshooting</p>
          <ul className="text-sm text-red-600 list-disc list-inside space-y-1">
            {nodeId === 'livekit' || nodeId === 'sip_bridge' ? (
              <>
                <li>Check if LiveKit server container is running</li>
                <li>Verify LIVEKIT_URL environment variable</li>
                <li>Check port 7880 is accessible</li>
              </>
            ) : nodeId === 'stt' || nodeId === 'llm' || nodeId === 'tts' ? (
              <>
                <li>API key is not configured — add it in Voice Settings</li>
                <li>Check provider service status on their status page</li>
              </>
            ) : (
              <li>Check service logs for error details</li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
