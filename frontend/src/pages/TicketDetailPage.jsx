import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ticketApi, jiraApi } from '../api/client';
import { toast } from '../components/UI/Toast';
import { format, formatDistanceToNow } from 'date-fns';
import {
  ArrowLeftIcon,
  ClockIcon,
  UserIcon,
  ChatBubbleLeftIcon,
  ArrowUpIcon,
  LinkIcon,
} from '@heroicons/react/24/outline';

const PRIORITY_BADGE = {
  P1: 'bg-red-100 text-red-700',
  P2: 'bg-orange-100 text-orange-700',
  P3: 'bg-blue-100 text-blue-700',
  P4: 'bg-gray-100 text-gray-600',
};

const STATUS_BADGE = {
  new: 'bg-blue-100 text-blue-700',
  assigned: 'bg-indigo-100 text-indigo-700',
  in_progress: 'bg-yellow-100 text-yellow-700',
  pending_customer: 'bg-purple-100 text-purple-700',
  pending_vendor: 'bg-purple-100 text-purple-700',
  resolved: 'bg-green-100 text-green-700',
  closed: 'bg-gray-100 text-gray-600',
  cancelled: 'bg-red-100 text-red-700',
};

const VALID_TRANSITIONS = {
  new: ['assigned', 'in_progress', 'cancelled'],
  assigned: ['in_progress', 'pending_customer', 'pending_vendor', 'cancelled'],
  in_progress: ['pending_customer', 'pending_vendor', 'resolved', 'cancelled'],
  pending_customer: ['in_progress', 'resolved', 'closed'],
  pending_vendor: ['in_progress', 'resolved'],
  resolved: ['closed', 'in_progress'],
  closed: [],
  cancelled: [],
};

export default function TicketDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState('');
  const [isPublic, setIsPublic] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [assignTo, setAssignTo] = useState('');

  async function loadTicket() {
    try {
      const [tRes, tlRes] = await Promise.allSettled([
        ticketApi.get(id),
        ticketApi.timeline(id),
      ]);
      if (tRes.status === 'fulfilled') setTicket(tRes.value.data);
      if (tlRes.status === 'fulfilled') setTimeline(tlRes.value.data?.items || tlRes.value.data || []);
    } catch {
      toast.error('Failed to load ticket');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTicket();
  }, [id]);

  async function handleStatusChange(newStatus) {
    try {
      await ticketApi.changeStatus(id, newStatus);
      toast.success(`Status changed to ${newStatus}`);
      loadTicket();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to change status');
    }
  }

  async function handleAddComment(e) {
    e.preventDefault();
    if (!comment.trim()) return;
    setSubmitting(true);
    try {
      await ticketApi.addComment(id, comment, isPublic);
      toast.success('Comment added');
      setComment('');
      loadTicket();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add comment');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAssign() {
    if (!assignTo.trim()) return;
    try {
      await ticketApi.assign(id, { user_id: assignTo });
      toast.success('Ticket assigned');
      setAssignTo('');
      loadTicket();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to assign');
    }
  }

  async function handleJiraSync() {
    try {
      await jiraApi.forceSync(id);
      toast.success('Synced to Jira');
      loadTicket();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Jira sync failed');
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 w-32 bg-slate-200 rounded" />
          <div className="h-8 w-64 bg-slate-200 rounded" />
          <div className="h-48 bg-slate-200 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="p-6 text-center text-slate-500">
        Ticket not found.
        <button onClick={() => navigate('/tickets')} className="ml-2 text-blue-600 hover:underline">
          Back to list
        </button>
      </div>
    );
  }

  const validNext = VALID_TRANSITIONS[ticket.status] || [];

  // SLA countdown
  const slaDeadline = ticket.sla_resolution_deadline ? new Date(ticket.sla_resolution_deadline) : null;
  const slaRemaining = slaDeadline ? slaDeadline.getTime() - Date.now() : null;
  const slaBreached = slaRemaining !== null && slaRemaining < 0;
  const slaWarning = slaRemaining !== null && slaRemaining > 0 && slaRemaining < 30 * 60 * 1000;

  return (
    <div className="p-6 space-y-6">
      {/* Back button + header */}
      <button
        onClick={() => navigate('/tickets')}
        className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
      >
        <ArrowLeftIcon className="w-4 h-4" />
        Back to Tickets
      </button>

      <div className="flex flex-wrap items-start gap-4 justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="text-sm font-mono text-slate-500">{ticket.ticket_number}</span>
            <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${PRIORITY_BADGE[ticket.priority] || ''}`}>
              {ticket.priority}
            </span>
            <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${STATUS_BADGE[ticket.status] || ''}`}>
              {ticket.status?.replace(/_/g, ' ')}
            </span>
          </div>
          <h1 className="text-xl font-bold text-slate-800">{ticket.subject}</h1>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content - timeline */}
        <div className="lg:col-span-2 space-y-4">
          {/* Description */}
          {ticket.description && (
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">Description</h3>
              <p className="text-sm text-slate-600 whitespace-pre-wrap">{ticket.description}</p>
            </div>
          )}

          {/* Timeline */}
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h3 className="text-sm font-semibold text-slate-700 mb-4">Timeline</h3>
            {timeline.length === 0 && (
              <p className="text-sm text-slate-400">No activity yet</p>
            )}
            <div className="space-y-4">
              {timeline.map((entry, i) => (
                <div key={i} className="flex gap-3">
                  <div className="flex-shrink-0 mt-1">
                    {entry.type === 'comment' && (
                      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs ${entry.is_public ? 'bg-blue-100 text-blue-600' : 'bg-amber-100 text-amber-600'}`}>
                        <ChatBubbleLeftIcon className="w-3.5 h-3.5" />
                      </div>
                    )}
                    {entry.type === 'status_change' && (
                      <div className="w-7 h-7 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-xs">
                        <ClockIcon className="w-3.5 h-3.5" />
                      </div>
                    )}
                    {entry.type === 'escalation' && (
                      <div className="w-7 h-7 rounded-full bg-red-100 text-red-600 flex items-center justify-center text-xs">
                        <ArrowUpIcon className="w-3.5 h-3.5" />
                      </div>
                    )}
                    {!['comment', 'status_change', 'escalation'].includes(entry.type) && (
                      <div className="w-7 h-7 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center text-xs">
                        <ClockIcon className="w-3.5 h-3.5" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-700">
                        {entry.user_name || entry.actor || 'System'}
                      </span>
                      {entry.type === 'comment' && !entry.is_public && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-600 font-semibold">
                          INTERNAL
                        </span>
                      )}
                      <span className="text-xs text-slate-400">
                        {entry.created_at
                          ? formatDistanceToNow(new Date(entry.created_at), { addSuffix: true })
                          : ''}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600 mt-0.5">
                      {entry.content || entry.message || entry.description || `Status: ${entry.old_status || '?'} -> ${entry.new_status || '?'}`}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Add comment */}
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Add Comment</h3>
            <form onSubmit={handleAddComment} className="space-y-3">
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={3}
                placeholder="Write a comment..."
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm text-slate-600">
                  <input
                    type="checkbox"
                    checked={isPublic}
                    onChange={(e) => setIsPublic(e.target.checked)}
                    className="rounded"
                  />
                  Public (visible to customer)
                </label>
                <button
                  type="submit"
                  disabled={submitting || !comment.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {submitting ? 'Sending...' : 'Add Comment'}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Actions */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-3">
            <h3 className="text-sm font-semibold text-slate-700">Actions</h3>

            {/* Status transitions */}
            {validNext.length > 0 && (
              <div>
                <label className="block text-xs text-slate-500 mb-1">Change Status</label>
                <div className="flex flex-wrap gap-1">
                  {validNext.map((s) => (
                    <button
                      key={s}
                      onClick={() => handleStatusChange(s)}
                      className={`px-2 py-1 rounded text-xs font-medium border transition-colors hover:shadow-sm ${STATUS_BADGE[s] || 'bg-slate-100 text-slate-600'}`}
                    >
                      {s.replace(/_/g, ' ')}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Assign */}
            <div>
              <label className="block text-xs text-slate-500 mb-1">Assign To (User ID)</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={assignTo}
                  onChange={(e) => setAssignTo(e.target.value)}
                  placeholder="User ID"
                  className="flex-1 px-2 py-1 border border-slate-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleAssign}
                  disabled={!assignTo.trim()}
                  className="px-3 py-1 bg-indigo-600 text-white rounded text-xs font-medium hover:bg-indigo-700 disabled:opacity-50"
                >
                  Assign
                </button>
              </div>
            </div>

            {/* Jira sync */}
            <button
              onClick={handleJiraSync}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition-colors"
            >
              <LinkIcon className="w-4 h-4" />
              Sync to Jira
            </button>
          </div>

          {/* Ticket details sidebar */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-3">
            <h3 className="text-sm font-semibold text-slate-700">Details</h3>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Assigned Team</span>
                <span className="text-slate-700 font-medium">{ticket.assigned_team_name || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Assigned User</span>
                <span className="text-slate-700 font-medium">{ticket.assigned_to_name || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Contact</span>
                <span className="text-slate-700 font-medium">{ticket.contact_name || ticket.contact_email || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Source</span>
                <span className="text-slate-700 font-medium">{ticket.source || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Created</span>
                <span className="text-slate-700 text-xs">
                  {ticket.created_at ? format(new Date(ticket.created_at), 'MMM d, yyyy HH:mm') : '-'}
                </span>
              </div>
              {ticket.jira_issue_key && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Jira</span>
                  <span className="text-blue-600 font-medium">{ticket.jira_issue_key}</span>
                </div>
              )}
            </div>
          </div>

          {/* SLA countdown */}
          <div className={`rounded-xl border p-5 ${slaBreached ? 'bg-red-50 border-red-200' : slaWarning ? 'bg-amber-50 border-amber-200' : 'bg-white border-slate-200'}`}>
            <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <ClockIcon className="w-4 h-4" />
              SLA
            </h3>
            {slaDeadline ? (
              <div className="mt-2">
                <div className={`text-lg font-bold ${slaBreached ? 'text-red-600' : slaWarning ? 'text-amber-600' : 'text-green-600'}`}>
                  {slaBreached
                    ? `Breached ${formatDistanceToNow(slaDeadline)} ago`
                    : `${formatDistanceToNow(slaDeadline)} remaining`}
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Deadline: {format(slaDeadline, 'MMM d, HH:mm')}
                </p>
                {/* SLA gauge */}
                <div className="mt-3 h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${slaBreached ? 'bg-red-500' : slaWarning ? 'bg-amber-500' : 'bg-green-500'}`}
                    style={{
                      width: slaBreached
                        ? '100%'
                        : `${Math.max(0, Math.min(100, 100 - (slaRemaining / (60 * 60 * 1000)) * 10))}%`,
                    }}
                  />
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-400 mt-2">No SLA configured</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
