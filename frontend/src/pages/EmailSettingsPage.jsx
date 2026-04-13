import { useEffect, useState } from 'react';
import { emailApi } from '../api/client';
import { toast } from '../components/UI/Toast';
import { PlusIcon, TrashIcon, XMarkIcon, EnvelopeIcon } from '@heroicons/react/24/outline';

export default function EmailSettingsPage() {
  const [mailboxes, setMailboxes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [form, setForm] = useState({
    email_address: '',
    ms_user_id: '',
    project_id: '',
  });

  async function loadMailboxes() {
    setLoading(true);
    try {
      const { data } = await emailApi.listMailboxes();
      setMailboxes(data.items || data || []);
    } catch {
      toast.error('Failed to load mailboxes');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMailboxes();
  }, []);

  async function handleCreate(e) {
    e.preventDefault();
    setSaving(true);
    try {
      await emailApi.createMailbox(form);
      toast.success('Mailbox added');
      setShowForm(false);
      setForm({ email_address: '', ms_user_id: '', project_id: '' });
      loadMailboxes();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add mailbox');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id) {
    if (!confirm('Delete this mailbox?')) return;
    setDeleting(id);
    try {
      await emailApi.deleteMailbox(id);
      toast.success('Mailbox deleted');
      loadMailboxes();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete mailbox');
    } finally {
      setDeleting(null);
    }
  }

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Email Settings</h1>
          <p className="text-sm text-slate-500 mt-1">Manage inbound mailboxes for ticket creation</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          <PlusIcon className="w-4 h-4" />
          Add Mailbox
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-800">Add Mailbox</h2>
            <button onClick={() => setShowForm(false)} className="text-slate-400 hover:text-slate-600">
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Email Address</label>
              <input
                type="email"
                value={form.email_address}
                onChange={(e) => setForm((p) => ({ ...p, email_address: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="support@company.com"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">MS User ID</label>
              <input
                type="text"
                value={form.ms_user_id}
                onChange={(e) => setForm((p) => ({ ...p, ms_user_id: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Azure AD User ID"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Project ID</label>
              <input
                type="text"
                value={form.project_id}
                onChange={(e) => setForm((p) => ({ ...p, project_id: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Project to map tickets to"
              />
            </div>
            <div className="md:col-span-3 flex justify-end gap-2">
              <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2 text-sm text-slate-600">
                Cancel
              </button>
              <button type="submit" disabled={saving} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
                {saving ? 'Adding...' : 'Add Mailbox'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              {['Email Address', 'Project', 'Subscription', ''].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-slate-400">Loading...</td></tr>
            )}
            {!loading && mailboxes.length === 0 && (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-slate-400">No mailboxes configured</td></tr>
            )}
            {!loading && mailboxes.map((m) => (
              <tr key={m.id} className="border-b border-slate-100">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <EnvelopeIcon className="w-4 h-4 text-slate-400" />
                    <span className="font-medium text-slate-800">{m.email_address}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-600">{m.project_name || m.project_id || '-'}</td>
                <td className="px-4 py-3">
                  <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold ${
                    m.subscription_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                  }`}>
                    {m.subscription_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => handleDelete(m.id)}
                    disabled={deleting === m.id}
                    className="text-slate-400 hover:text-red-600 transition-colors disabled:opacity-50"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
