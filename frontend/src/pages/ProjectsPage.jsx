import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import { PlusIcon, ArrowUpTrayIcon, LinkIcon } from '@heroicons/react/24/outline';

export default function ProjectsPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ code: '', name: '', description: '', jira_project_key: '', default_priority: 'P3' });
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const fileRef = useRef();

  async function load() {
    try {
      const { data } = await api.get('/projects');
      setProjects(data);
    } catch {} finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(e) {
    e.preventDefault();
    try {
      await api.post('/projects', form);
      setShowCreate(false);
      setForm({ code: '', name: '', description: '', jira_project_key: '', default_priority: 'P3' });
      load();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error');
    }
  }

  async function handleCSVImport(e) {
    const file = e.target.files[0];
    if (!file) return;
    setImporting(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const { data } = await api.post('/projects/import-csv', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setImportResult(data);
      load();
    } catch (err) {
      setImportResult({ error: err.response?.data?.detail || 'Import failed' });
    } finally { setImporting(false); e.target.value = ''; }
  }

  async function handleJiraMapping(projectId, currentKey) {
    const key = prompt('Jira Project Key:', currentKey || '');
    if (key === null) return;
    try {
      await api.put(`/projects/${projectId}/jira-mapping?jira_project_key=${encodeURIComponent(key)}`);
      load();
    } catch (err) { alert(err.response?.data?.detail || 'Error'); }
  }

  return (
    <div className="p-6 max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Projects</h1>
        <div className="flex gap-2">
          <input type="file" accept=".csv" ref={fileRef} className="hidden" onChange={handleCSVImport} />
          <button onClick={() => fileRef.current.click()} disabled={importing}
            className="flex items-center gap-2 px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 hover:bg-slate-50">
            <ArrowUpTrayIcon className="w-4 h-4" /> {importing ? 'Importing...' : 'Import CSV'}
          </button>
          <button onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
            <PlusIcon className="w-4 h-4" /> New Project
          </button>
        </div>
      </div>

      {importResult && (
        <div className={`p-3 rounded-lg text-sm ${importResult.error ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
          {importResult.error ? importResult.error : `Created: ${importResult.created}, Updated: ${importResult.updated}`}
          {importResult.errors?.length > 0 && <p className="mt-1 text-xs">{importResult.errors.join('; ')}</p>}
          <button onClick={() => setImportResult(null)} className="ml-2 underline">dismiss</button>
        </div>
      )}

      {showCreate && (
        <form onSubmit={handleCreate} className="bg-white border border-slate-200 rounded-xl p-5 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <input placeholder="Code (e.g. INFRA)" required value={form.code} onChange={e => setForm({...form, code: e.target.value.toUpperCase()})}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm" />
            <input placeholder="Name" required value={form.name} onChange={e => setForm({...form, name: e.target.value})}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm" />
            <input placeholder="Jira Project Key (optional)" value={form.jira_project_key} onChange={e => setForm({...form, jira_project_key: e.target.value})}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm" />
            <select value={form.default_priority} onChange={e => setForm({...form, default_priority: e.target.value})}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm">
              <option value="P1">P1 - Critical</option>
              <option value="P2">P2 - High</option>
              <option value="P3">P3 - Medium</option>
              <option value="P4">P4 - Low</option>
            </select>
          </div>
          <input placeholder="Description (optional)" value={form.description} onChange={e => setForm({...form, description: e.target.value})}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          <div className="flex gap-2">
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm">Create</button>
            <button type="button" onClick={() => setShowCreate(false)} className="px-4 py-2 border border-slate-300 rounded-lg text-sm">Cancel</button>
          </div>
        </form>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Code</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Name</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Jira Key</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Priority</th>
              <th className="text-left px-4 py-3 font-medium text-slate-600">Status</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {projects.map(p => (
              <tr key={p.id} className="border-b border-slate-100 hover:bg-slate-50">
                <td className="px-4 py-3 font-mono font-medium">{p.code}</td>
                <td className="px-4 py-3">{p.name}</td>
                <td className="px-4 py-3">
                  {p.jira_project_key ? (
                    <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-medium">{p.jira_project_key}</span>
                  ) : (
                    <span className="text-slate-400">—</span>
                  )}
                </td>
                <td className="px-4 py-3"><span className="text-xs">{p.default_priority}</span></td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs ${p.is_active ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {p.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <button onClick={() => handleJiraMapping(p.id, p.jira_project_key)} title="Map to Jira"
                    className="p-1 text-slate-400 hover:text-blue-600">
                    <LinkIcon className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
            {projects.length === 0 && !loading && (
              <tr><td colSpan="6" className="px-4 py-8 text-center text-slate-400">No projects. Create one or import CSV.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="text-xs text-slate-400">
        CSV format: <code>code,name,description,jira_project_key,default_priority</code>
      </div>
    </div>
  );
}
