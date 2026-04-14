import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import api, { voiceApi } from '../api/client';
import {
  PlusIcon,
  CheckCircleIcon,
  XCircleIcon,
  KeyIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

const TABS = [
  { id: 'general', label: 'General' },
  { id: 'stt', label: 'STT (Speech-to-Text)' },
  { id: 'llm', label: 'LLM (Language Model)' },
  { id: 'tts', label: 'TTS (Text-to-Speech)' },
  { id: 'livekit', label: 'LiveKit' },
  { id: 'did', label: 'DID Mappings' },
  { id: 'keys', label: 'API Keys' },
];

export default function VoiceSettingsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'general';
  const [providers, setProviders] = useState({ stt: [], tts: [], llm: [] });
  const [config, setConfig] = useState({});
  const [didMappings, setDidMappings] = useState([]);
  const [apiKeys, setApiKeys] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const [provRes, cfgRes, didRes, keysRes] = await Promise.allSettled([
        voiceApi.providers(),
        api.get('/voice/config'),
        voiceApi.didMappings(),
        api.get('/voice/api-keys'),
      ]);
      if (provRes.status === 'fulfilled') setProviders(provRes.value.data);
      if (cfgRes.status === 'fulfilled') setConfig(cfgRes.value.data);
      if (didRes.status === 'fulfilled') setDidMappings(didRes.value.data);
      if (keysRes.status === 'fulfilled') setApiKeys(keysRes.value.data);
    } catch {} finally { setLoading(false); }
  }

  useEffect(() => { load(); }, []);

  async function saveConfig(updates) {
    setSaving(true);
    try {
      const { data } = await api.put('/voice/config', updates);
      setConfig(data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Save failed');
    } finally { setSaving(false); }
  }

  async function saveApiKey(keyName, keyValue) {
    try {
      await api.post('/voice/api-keys', { key_name: keyName, key_value: keyValue });
      setApiKeys(prev => ({ ...prev, [keyName]: { configured: true, masked: '****' + keyName.slice(-4) } }));
      return true;
    } catch (err) {
      alert(err.response?.data?.detail || 'Save failed');
      return false;
    }
  }

  if (loading) {
    return <div className="p-6 flex items-center gap-2"><ArrowPathIcon className="w-5 h-5 animate-spin" /> Loading...</div>;
  }

  return (
    <div className="p-6 max-w-5xl space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Voice Pipeline Settings</h1>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-slate-200">
        {TABS.map(tab => (
          <button key={tab.id}
            onClick={() => setSearchParams({ tab: tab.id })}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeTab === tab.id ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* General Tab */}
      {activeTab === 'general' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
            <h2 className="font-semibold text-slate-800">Pipeline Configuration</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SelectField label="Language" value={config.language || 'tr'}
                options={[['tr','Turkish'],['en','English'],['de','German'],['fr','French'],['es','Spanish']]}
                onChange={v => saveConfig({ language: v })} />
            </div>
            <p className="text-xs text-slate-400">Active: STT={config.stt_provider}, LLM={config.llm_provider}, TTS={config.tts_provider}</p>
          </div>

          {/* Turn Detection Settings */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
            <h2 className="font-semibold text-slate-800">Turn Detection & Interruption</h2>
            <p className="text-xs text-slate-500">Controls when the agent decides the user has finished speaking and how it handles interruptions.</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Min Silence (ms)</label>
                <input type="number" value={config.min_endpointing_delay || 500}
                  onChange={e => saveConfig({ min_endpointing_delay: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
                <p className="text-xs text-slate-400 mt-1">Minimum sessizlik suresi. Bundan kisa sessizlik "konusma bitti" sayilmaz.</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Max Silence (ms)</label>
                <input type="number" value={config.max_endpointing_delay || 3000}
                  onChange={e => saveConfig({ max_endpointing_delay: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
                <p className="text-xs text-slate-400 mt-1">Maksimum bekleme. Bu kadar sessizlik varsa kesin konusma bitmis.</p>
              </div>
              <SelectField label="Interruption Mode" value={config.interruption_mode || 'adaptive'}
                options={[['adaptive','Adaptive (onerilen)'],['eager','Eager (hemen kes)'],['conservative','Conservative (gecikme)']]}
                onChange={v => saveConfig({ interruption_mode: v })} />
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Backchannel Threshold (ms)</label>
                <input type="number" value={config.backchannel_threshold || 300}
                  onChange={e => saveConfig({ backchannel_threshold: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
                <p className="text-xs text-slate-400 mt-1">Bu sureden kisa sesler (ihi, evet) interrupt sayilmaz.</p>
              </div>
            </div>
            <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-600">
              <p className="font-medium mb-1">Nasil calisiyor:</p>
              <ul className="list-disc list-inside space-y-0.5">
                <li>VAD (Voice Activity Detection): Ses var mi yok mu algiler</li>
                <li>Endpointing: Sessizlik suresi + cumle tamlik modeli ile "konusma bitti" karari</li>
                <li>Interruption: Musteri araya girerse TTS iptal, yeni dinleme baslar</li>
                <li>Adaptive modda "ihi/evet" gibi kisa sesler agent'i kesmez</li>
              </ul>
            </div>
          </div>

          {/* Transfer & On-Call Settings */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
            <h2 className="font-semibold text-slate-800">Transfer & Nobetci Bildirim</h2>
            <p className="text-xs text-slate-500">Ticket olusturulduktan sonra musteri temsilciye aktarilir. Ulasilamazsa nobetci ekibe mail gider.</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Transfer Telefon / Dahili</label>
                <input value={config.transfer_phone || ''} onChange={e => saveConfig({ transfer_phone: e.target.value })}
                  placeholder="orn: +902121234567 veya 100 (PBX dahili)"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Zil Suresi (sn)</label>
                <input type="number" value={config.transfer_ring_timeout || 30}
                  onChange={e => saveConfig({ transfer_ring_timeout: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
                <p className="text-xs text-slate-400 mt-1">Bu sure icinde acilamazsa nobetciye mail gider.</p>
              </div>
              <div className="md:col-span-2">
                <label className="block text-xs font-medium text-slate-600 mb-1">Nobetci Email</label>
                <input value={config.oncall_email || ''} onChange={e => saveConfig({ oncall_email: e.target.value })}
                  placeholder="oncall@company.com"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
                <p className="text-xs text-slate-400 mt-1">Temsilciye ulasilamadiginda bu adrese arayan bilgileri + ticket detayi gonderilir.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STT Tab */}
      {activeTab === 'stt' && (
        <ProviderSection
          title="Speech-to-Text Provider"
          providers={providers.stt}
          activeProvider={config.stt_provider || 'deepgram'}
          fallbackProvider={config.stt_fallback || 'groq'}
          onSelectPrimary={v => saveConfig({ stt_provider: v })}
          onSelectFallback={v => saveConfig({ stt_fallback: v })}
          apiKeys={apiKeys}
          onSaveKey={saveApiKey}
          saving={saving}
        />
      )}

      {/* LLM Tab */}
      {activeTab === 'llm' && (
        <ProviderSection
          title="Language Model (NLP)"
          providers={providers.llm}
          activeProvider={config.llm_provider || 'claude'}
          fallbackProvider={config.llm_fallback || 'groq'}
          onSelectPrimary={v => saveConfig({ llm_provider: v })}
          onSelectFallback={v => saveConfig({ llm_fallback: v })}
          apiKeys={apiKeys}
          onSaveKey={saveApiKey}
          saving={saving}
        />
      )}

      {/* TTS Tab */}
      {activeTab === 'tts' && (
        <ProviderSection
          title="Text-to-Speech Provider"
          providers={providers.tts}
          activeProvider={config.tts_provider || 'openai'}
          fallbackProvider={config.tts_fallback || 'edge'}
          onSelectPrimary={v => saveConfig({ tts_provider: v })}
          onSelectFallback={v => saveConfig({ tts_fallback: v })}
          apiKeys={apiKeys}
          onSaveKey={saveApiKey}
          saving={saving}
        />
      )}

      {/* LiveKit Tab */}
      {activeTab === 'livekit' && (
        <LiveKitSection />
      )}

      {/* DID Tab */}
      {activeTab === 'did' && (
        <DIDSection mappings={didMappings} onReload={load} />
      )}

      {/* API Keys Tab */}
      {activeTab === 'keys' && (
        <ApiKeysSection apiKeys={apiKeys} onSaveKey={saveApiKey} />
      )}
    </div>
  );
}

function ProviderSection({ title, providers, activeProvider, fallbackProvider, onSelectPrimary, onSelectFallback, apiKeys, onSaveKey, saving }) {
  return (
    <div className="space-y-4">
      <h2 className="font-semibold text-slate-800">{title}</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {providers.map(p => {
          const isPrimary = p.name === activeProvider;
          const isFallback = p.name === fallbackProvider;
          const keyConfigured = !p.api_key_env || apiKeys[p.api_key_env]?.configured || p.available;
          return (
            <div key={p.name} className={`rounded-xl border-2 p-4 transition-all ${isPrimary ? 'border-blue-500 bg-blue-50' : isFallback ? 'border-amber-400 bg-amber-50' : 'border-slate-200 bg-white'}`}>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-medium text-slate-800">{p.label}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{p.description}</p>
                </div>
                <div className="flex items-center gap-1">
                  {keyConfigured
                    ? <CheckCircleIcon className="w-5 h-5 text-green-500" title="API key configured" />
                    : <XCircleIcon className="w-5 h-5 text-red-400" title="API key missing" />}
                </div>
              </div>
              {p.languages && <p className="text-xs text-slate-400 mb-2">Languages: {p.languages.join(', ')}</p>}
              {p.self_hostable && <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded mr-1">Self-hostable</span>}
              {p.cost != null && <span className="text-xs text-slate-400">${p.cost}/unit</span>}
              <div className="flex gap-2 mt-3">
                <button onClick={() => onSelectPrimary(p.name)} disabled={isPrimary || saving}
                  className={`px-3 py-1.5 rounded text-xs font-medium ${isPrimary ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                  {isPrimary ? 'Primary' : 'Set Primary'}
                </button>
                <button onClick={() => onSelectFallback(p.name)} disabled={isFallback || saving}
                  className={`px-3 py-1.5 rounded text-xs font-medium ${isFallback ? 'bg-amber-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                  {isFallback ? 'Fallback' : 'Set Fallback'}
                </button>
              </div>
              {p.api_key_env && (
                <ApiKeyInput keyName={p.api_key_env} onSave={onSaveKey} alreadyConfigured={keyConfigured} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ApiKeyInput({ keyName, onSave, alreadyConfigured }) {
  const [value, setValue] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [editing, setEditing] = useState(!alreadyConfigured);

  async function handleSave() {
    if (!value.trim()) return;
    setSaving(true);
    const ok = await onSave(keyName, value.trim());
    setSaving(false);
    if (ok) { setSaved(true); setValue(''); setEditing(false); }
  }

  if (!editing && alreadyConfigured) {
    return (
      <div className="mt-2 flex items-center gap-2">
        <span className="text-xs text-green-600 flex items-center gap-1">
          <CheckCircleIcon className="w-3.5 h-3.5" /> Key configured
        </span>
        <button onClick={() => { setEditing(true); setSaved(false); }}
          className="text-xs text-blue-600 hover:underline">Change</button>
      </div>
    );
  }

  return (
    <div className="mt-2 flex gap-2">
      <input type="password" placeholder={`Enter ${keyName}`} value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && handleSave()}
        className="flex-1 px-2 py-1.5 border border-slate-300 rounded text-xs" />
      <button onClick={handleSave} disabled={saving || !value.trim()}
        className="px-3 py-1.5 bg-green-600 text-white rounded text-xs hover:bg-green-700 disabled:opacity-50">
        {saving ? '...' : saved ? 'Saved!' : alreadyConfigured ? 'Update' : 'Save Key'}
      </button>
      {alreadyConfigured && (
        <button onClick={() => setEditing(false)} className="px-2 py-1.5 text-xs text-slate-500 hover:text-slate-700">Cancel</button>
      )}
    </div>
  );
}

function DIDSection({ mappings, onReload }) {
  const [form, setForm] = useState({ did_number: '', project_id: '', description: '' });
  const [creating, setCreating] = useState(false);

  async function handleCreate(e) {
    e.preventDefault();
    setCreating(true);
    try {
      await voiceApi.createDid({ did_number: form.did_number, description: form.description });
      setForm({ did_number: '', project_id: '', description: '' });
      onReload();
    } catch (err) { alert(err.response?.data?.detail || 'Error'); }
    finally { setCreating(false); }
  }

  return (
    <div className="space-y-4">
      <h2 className="font-semibold text-slate-800">DID Number Mappings</h2>
      <form onSubmit={handleCreate} className="flex gap-2">
        <input placeholder="+905321234567" required value={form.did_number} onChange={e => setForm({...form, did_number: e.target.value})}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm flex-1" />
        <input placeholder="Description" value={form.description} onChange={e => setForm({...form, description: e.target.value})}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm flex-1" />
        <button type="submit" disabled={creating} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
          <PlusIcon className="w-4 h-4" />
        </button>
      </form>
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50"><tr>
            <th className="text-left px-4 py-2">DID Number</th>
            <th className="text-left px-4 py-2">Description</th>
          </tr></thead>
          <tbody>
            {mappings.map(m => (
              <tr key={m.id} className="border-t border-slate-100">
                <td className="px-4 py-2 font-mono">{m.did_number}</td>
                <td className="px-4 py-2 text-slate-500">{m.description || '—'}</td>
              </tr>
            ))}
            {mappings.length === 0 && <tr><td colSpan="2" className="px-4 py-4 text-center text-slate-400">No DID mappings</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ApiKeysSection({ apiKeys, onSaveKey }) {
  const allKeys = [
    { name: 'DEEPGRAM_API_KEY', label: 'Deepgram', for: 'STT' },
    { name: 'MISTRAL_API_KEY', label: 'Mistral (Voxtral)', for: 'STT + TTS + LLM' },
    { name: 'ANTHROPIC_API_KEY', label: 'Anthropic (Claude)', for: 'LLM' },
    { name: 'OPENAI_API_KEY', label: 'OpenAI', for: 'STT + TTS + LLM' },
    { name: 'GROQ_API_KEY', label: 'Groq', for: 'STT + LLM' },
    { name: 'ELEVENLABS_API_KEY', label: 'ElevenLabs', for: 'TTS' },
  ];

  return (
    <div className="space-y-4">
      <h2 className="font-semibold text-slate-800">API Keys</h2>
      <p className="text-sm text-slate-500">Keys are encrypted (AES-256) before storage. Values are never displayed after saving.</p>
      <div className="space-y-3">
        {allKeys.map(k => {
          const configured = apiKeys[k.name]?.configured;
          return (
            <div key={k.name} className="bg-white rounded-xl border border-slate-200 p-4">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-medium text-slate-800">{k.label}</p>
                  <p className="text-xs text-slate-400">Used for: {k.for}</p>
                </div>
                {configured
                  ? <span className="flex items-center gap-1 text-xs text-green-600"><CheckCircleIcon className="w-4 h-4" /> Configured</span>
                  : <span className="flex items-center gap-1 text-xs text-red-500"><XCircleIcon className="w-4 h-4" /> Not set</span>}
              </div>
              <ApiKeyInput keyName={k.name} onSave={onSaveKey} alreadyConfigured={configured} />
            </div>
          );
        })}
      </div>
    </div>
  );
}

function LiveKitSection() {
  const [config, setConfig] = useState({ url: '', api_key: '', api_secret_configured: false });
  const [form, setForm] = useState({ url: '', api_key: '', api_secret: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const { data } = await api.get('/voice/livekit/config');
        setConfig(data);
        setForm({ url: data.url || '', api_key: data.api_key || '', api_secret: '' });
      } catch {} finally { setLoading(false); }
    }
    load();
  }, []);

  async function handleSave(e) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {};
      if (form.url) payload.url = form.url;
      if (form.api_key) payload.api_key = form.api_key;
      if (form.api_secret) payload.api_secret = form.api_secret;
      const { data } = await api.put('/voice/livekit/config', payload);
      setConfig(data);
      setForm(prev => ({ ...prev, api_secret: '' }));
    } catch (err) {
      alert(err.response?.data?.detail || 'Save failed');
    } finally { setSaving(false); }
  }

  async function handleTest() {
    setTestResult(null);
    try {
      const { data } = await api.post('/voice/livekit/test');
      setTestResult(data);
    } catch (err) {
      setTestResult({ status: 'error', message: err.response?.data?.detail || err.message });
    }
  }

  if (loading) return <div className="text-sm text-slate-400">Loading...</div>;

  return (
    <div className="space-y-4">
      <h2 className="font-semibold text-slate-800">LiveKit Server Configuration</h2>
      <p className="text-sm text-slate-500">LiveKit provides WebRTC media transport for voice calls (browser and SIP).</p>

      <form onSubmit={handleSave} className="bg-white rounded-xl border border-slate-200 p-5 space-y-4">
        <div>
          <label className="block text-xs font-medium text-slate-600 mb-1">LiveKit Server URL</label>
          <input value={form.url} onChange={e => setForm({ ...form, url: e.target.value })}
            placeholder="ws://localhost:7880 or wss://livekit.yourcompany.com"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">API Key</label>
            <input value={form.api_key} onChange={e => setForm({ ...form, api_key: e.target.value })}
              placeholder="your-livekit-api-key"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono" />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">
              API Secret {config.api_secret_configured && <span className="text-green-600">(configured)</span>}
            </label>
            <input type="password" value={form.api_secret} onChange={e => setForm({ ...form, api_secret: e.target.value })}
              placeholder={config.api_secret_configured ? '••••••• (leave blank to keep current)' : 'your-livekit-api-secret'}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono" />
          </div>
        </div>
        <div className="flex gap-2">
          <button type="submit" disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50">
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
          <button type="button" onClick={handleTest}
            className="px-4 py-2 border border-slate-300 rounded-lg text-sm hover:bg-slate-50">
            Test Connection
          </button>
        </div>
      </form>

      {testResult && (
        <div className={`p-3 rounded-lg text-sm ${testResult.status === 'ok' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {testResult.status === 'ok' ? <CheckCircleIcon className="w-4 h-4 inline mr-1" /> : <XCircleIcon className="w-4 h-4 inline mr-1" />}
          {testResult.message}
        </div>
      )}
    </div>
  );
}

function SelectField({ label, value, options, onChange }) {
  return (
    <div>
      <label className="block text-xs font-medium text-slate-600 mb-1">{label}</label>
      <select value={value} onChange={e => onChange(e.target.value)}
        className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm">
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    </div>
  );
}
