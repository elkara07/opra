import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import {
  PhoneIcon,
  EnvelopeIcon,
  ServerIcon,
  ClockIcon,
  ArrowUpIcon,
  BellIcon,
  CircleStackIcon,
  LinkIcon,
  CloudIcon,
  MicrophoneIcon,
  SpeakerWaveIcon,
  CpuChipIcon,
  SignalIcon,
} from '@heroicons/react/24/outline';

const STATUS_COLORS = {
  ok: { dot: 'bg-green-500', ring: 'ring-green-200', shadow: 'shadow-green-100' },
  warning: { dot: 'bg-amber-500', ring: 'ring-amber-200', shadow: 'shadow-amber-100' },
  error: { dot: 'bg-red-500', ring: 'ring-red-200', shadow: 'shadow-red-100' },
  not_configured: { dot: 'bg-gray-400', ring: 'ring-gray-200', shadow: '' },
  disabled: { dot: 'bg-gray-300', ring: 'ring-gray-100', shadow: '' },
};

const NODE_ICONS = {
  pbx: PhoneIcon,
  sip_bridge: SignalIcon,
  livekit: SpeakerWaveIcon,
  pipecat: CpuChipIcon,
  stt: MicrophoneIcon,
  llm: CpuChipIcon,
  tts: SpeakerWaveIcon,
  email_in: EnvelopeIcon,
  phone_in: PhoneIcon,
  ticket_engine: ServerIcon,
  sla_engine: ClockIcon,
  escalation: ArrowUpIcon,
  notifications: BellIcon,
  email_out: EnvelopeIcon,
  postgresql: CircleStackIcon,
  jira_sync: LinkIcon,
  minio: CloudIcon,
};

const VOICE_PIPELINE = [
  { id: 'pbx', label: 'PBX' },
  { id: 'sip_bridge', label: 'SIP Bridge' },
  { id: 'livekit', label: 'LiveKit' },
  { id: 'pipecat', label: 'Pipecat' },
  { id: 'stt', label: 'STT' },
  { id: 'llm', label: 'LLM' },
  { id: 'tts', label: 'TTS' },
];

const TICKET_PIPELINE_TOP = [
  { id: 'email_in', label: 'Email' },
  { id: 'ticket_engine', label: 'Ticket Engine' },
  { id: 'sla_engine', label: 'SLA Engine' },
  { id: 'escalation', label: 'Escalation' },
  { id: 'notifications', label: 'Notifications' },
];

const TICKET_BRANCH_DOWN = [
  { id: 'postgresql', label: 'PostgreSQL' },
  { id: 'jira_sync', label: 'Jira Sync' },
  { id: 'minio', label: 'MinIO' },
];

// All nodes navigate to NodeDetailPage — configure button is there
function nodeUrl(id) {
  return `/topology/${id}`;
}

export default function TopologyPage() {
  const navigate = useNavigate();
  const [nodes, setNodes] = useState({});
  const [loading, setLoading] = useState(true);
  const [tooltip, setTooltip] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const { data } = await api.get('/system/topology');
        const nodeMap = {};
        (data.nodes || []).forEach((n) => {
          nodeMap[n.id] = n;
        });
        setNodes(nodeMap);
      } catch {
        // Use empty fallback — nodes will show as not_configured
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  function getNodeStatus(id) {
    return nodes[id]?.status || 'not_configured';
  }

  function getNodeData(id) {
    return nodes[id] || {};
  }

  function handleNodeClick(id) {
    navigate(nodeUrl(id));
  }

  function NodeBox({ id, label }) {
    const status = getNodeStatus(id);
    const nodeData = getNodeData(id);
    const colors = STATUS_COLORS[status] || STATUS_COLORS.not_configured;
    const Icon = NODE_ICONS[id] || ServerIcon;

    return (
      <div
        className={`relative flex flex-col items-center justify-center w-28 h-24 rounded-xl border-2 bg-white cursor-pointer transition-all hover:shadow-lg hover:-translate-y-0.5 ${colors.shadow}`}
        style={{ borderColor: status === 'ok' ? '#22c55e' : status === 'warning' ? '#f59e0b' : status === 'error' ? '#ef4444' : '#d1d5db' }}
        onClick={() => handleNodeClick(id)}
        onMouseEnter={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          setTooltip({
            id,
            x: rect.left + rect.width / 2,
            y: rect.top - 8,
            status,
            error: nodeData.error,
            latency: nodeData.latency_ms,
            label,
          });
        }}
        onMouseLeave={() => setTooltip(null)}
      >
        {/* Status dot */}
        <div className={`absolute top-2 right-2 w-2.5 h-2.5 rounded-full ${colors.dot}`} />
        <Icon className="w-6 h-6 text-slate-600 mb-1" />
        <span className="text-xs font-semibold text-slate-700 text-center leading-tight">
          {label}
        </span>
      </div>
    );
  }

  function Arrow({ direction = 'right' }) {
    if (direction === 'right') {
      return (
        <div className="flex items-center justify-center w-8 h-24">
          <svg width="24" height="12" viewBox="0 0 24 12" fill="none">
            <path d="M0 6H20M20 6L15 1M20 6L15 11" stroke="#94a3b8" strokeWidth="1.5" />
          </svg>
        </div>
      );
    }
    if (direction === 'down') {
      return (
        <div className="flex items-center justify-center w-28 h-6">
          <svg width="12" height="20" viewBox="0 0 12 20" fill="none">
            <path d="M6 0V16M6 16L1 11M6 16L11 11" stroke="#94a3b8" strokeWidth="1.5" />
          </svg>
        </div>
      );
    }
    return null;
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 w-48 bg-slate-200 rounded" />
          <div className="h-64 bg-slate-200 rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Pipeline Topology</h1>
        <p className="text-sm text-slate-500 mt-1">Click any node to navigate to its configuration. Hover for details.</p>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 text-xs text-slate-600">
        {Object.entries(STATUS_COLORS).map(([key, val]) => (
          <div key={key} className="flex items-center gap-1.5">
            <div className={`w-3 h-3 rounded-full ${val.dot}`} />
            <span>{key.replace(/_/g, ' ')}</span>
          </div>
        ))}
      </div>

      {/* Voice Pipeline */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">
          Voice Pipeline
        </h2>
        <div className="flex items-center overflow-x-auto pb-4">
          {VOICE_PIPELINE.map((node, i) => (
            <div key={node.id} className="flex items-center">
              <NodeBox id={node.id} label={node.label} />
              {i < VOICE_PIPELINE.length - 1 && <Arrow direction="right" />}
            </div>
          ))}
        </div>
        {/* Pipecat -> Ticket Engine connection */}
        <div className="ml-[calc(3*(7rem+2rem)+3.5rem)] flex flex-col items-center">
          <Arrow direction="down" />
          <NodeBox id="ticket_engine" label="Ticket Engine" />
        </div>
      </div>

      {/* Ticket Pipeline */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">
          Ticket Pipeline
        </h2>

        {/* Main flow: Email + Phone -> Ticket Engine -> SLA -> Escalation -> Notifications */}
        <div className="flex items-start overflow-x-auto pb-4">
          {/* Inputs */}
          <div className="flex flex-col items-center gap-2 mr-0">
            <NodeBox id="email_in" label="Email" />
            <NodeBox id="phone_in" label="Phone" />
          </div>
          <div className="flex items-center self-center">
            <Arrow direction="right" />
          </div>

          {/* Main pipeline nodes */}
          {TICKET_PIPELINE_TOP.slice(1).map((node, i) => (
            <div key={node.id} className="flex items-center">
              <NodeBox id={node.id} label={node.label} />
              {i < TICKET_PIPELINE_TOP.length - 2 && <Arrow direction="right" />}
            </div>
          ))}
        </div>

        {/* Branch down from Ticket Engine */}
        <div className="ml-[calc(7rem+2rem+2rem)] flex items-start gap-4 mt-2">
          <div className="flex flex-col items-center">
            <Arrow direction="down" />
            <div className="flex gap-3">
              {TICKET_BRANCH_DOWN.map((node) => (
                <NodeBox key={node.id} id={node.id} label={node.label} />
              ))}
            </div>
          </div>
          {/* Notifications -> Email Out branch */}
          <div className="ml-auto flex flex-col items-center">
            <Arrow direction="down" />
            <NodeBox id="email_out" label="Email Out" />
          </div>
        </div>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="fixed z-50 bg-slate-800 text-white text-xs rounded-lg px-3 py-2 shadow-lg pointer-events-none"
          style={{
            left: tooltip.x,
            top: tooltip.y,
            transform: 'translate(-50%, -100%)',
          }}
        >
          <div className="font-semibold mb-0.5">{tooltip.label}</div>
          <div>Status: {tooltip.status.replace(/_/g, ' ')}</div>
          {tooltip.latency != null && <div>Latency: {tooltip.latency}ms</div>}
          {tooltip.error && <div className="text-red-300 mt-0.5">{tooltip.error}</div>}
        </div>
      )}
    </div>
  );
}
