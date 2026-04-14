import { useState, useRef, useEffect } from 'react';
import api from '../api/client';
import {
  MicrophoneIcon, StopIcon, PlayIcon, ArrowPathIcon,
  CheckCircleIcon, XCircleIcon, ExclamationTriangleIcon,
  ChevronRightIcon, SpeakerWaveIcon, ChatBubbleLeftRightIcon,
  ShieldCheckIcon, PhoneXMarkIcon, SignalIcon,
} from '@heroicons/react/24/outline';

const REQUIRED_FIELDS = {
  caller_name: { label: 'Arayan Adi', icon: '👤' },
  company_or_project: { label: 'Firma/Proje', icon: '🏢' },
  issue_summary: { label: 'Sorun Ozeti', icon: '📝' },
  affected_system: { label: 'Etkilenen Sistem', icon: '🖥' },
  urgency: { label: 'Aciliyet', icon: '⚡' },
};

const STATE_LABELS = {
  greeting: { label: 'Karsilama', color: 'bg-blue-100 text-blue-700' },
  collect: { label: 'Bilgi Toplama', color: 'bg-yellow-100 text-yellow-700' },
  clarify: { label: 'Detaylandirma', color: 'bg-orange-100 text-orange-700' },
  confirm: { label: 'Teyit', color: 'bg-purple-100 text-purple-700' },
  create: { label: 'Ticket Olustur', color: 'bg-green-100 text-green-700' },
  close: { label: 'Kapanis', color: 'bg-gray-100 text-gray-600' },
  transfer: { label: 'Transfer', color: 'bg-red-100 text-red-700' },
};

const PIPELINE_NODES = [
  { id: 'mic', label: 'Mic/Browser' },
  { id: 'livekit', label: 'LiveKit' },
  { id: 'pipecat', label: 'Pipecat' },
  { id: 'stt', label: 'STT' },
  { id: 'guard', label: 'Guardrail' },
  { id: 'llm', label: 'LLM' },
  { id: 'tts', label: 'TTS' },
  { id: 'speaker', label: 'Speaker' },
];

export default function VoiceTestPage() {
  const [config, setConfig] = useState(null);
  const [apiKeys, setApiKeys] = useState({});
  const [livekitStatus, setLivekitStatus] = useState('disconnected');
  const [livekitInfo, setLivekitInfo] = useState(null);
  const [recording, setRecording] = useState(false);
  const [textMode, setTextMode] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [language, setLanguage] = useState('tr');
  const [loading, setLoading] = useState(false);
  const [activeNode, setActiveNode] = useState(null);
  const [conversation, setConversation] = useState([]);
  const [context, setContext] = useState(null);
  const [lastTimings, setLastTimings] = useState(null);
  const mediaRecorder = useRef(null);
  const chunks = useRef([]);
  const chatEndRef = useRef(null);

  useEffect(() => {
    async function load() {
      try {
        const [cfgRes, keysRes] = await Promise.allSettled([
          api.get('/voice/config'), api.get('/voice/api-keys'),
        ]);
        if (cfgRes.status === 'fulfilled') setConfig(cfgRes.value.data);
        if (keysRes.status === 'fulfilled') setApiKeys(keysRes.value.data);
      } catch {}
    }
    load();
  }, []);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [conversation]);

  // --- LiveKit Connection ---
  async function connectLiveKit() {
    setLivekitStatus('connecting');
    try {
      const { data } = await api.post('/voice/livekit/token');
      setLivekitInfo(data);
      setLivekitStatus('connected');
      // Send greeting
      const greetRes = await api.post('/voice/test-conversation', { text: '', context: null });
      setContext(greetRes.data.context);
      addMessage('agent', greetRes.data.agent_text, greetRes.data.tts);
      if (greetRes.data.tts?.audio_base64) {
        playAudio(greetRes.data.tts.audio_base64, greetRes.data.tts.content_type);
      }
    } catch (err) {
      setLivekitStatus('error');
      addMessage('system', 'LiveKit baglanti hatasi: ' + (err.response?.data?.detail || err.message));
    }
  }

  // --- Full Pipeline: Mic → LiveKit → Pipecat → STT → LLM → TTS → Speaker ---
  async function processAudioThroughPipeline(audioBlob) {
    setLoading(true);
    setActiveNode('livekit');

    try {
      // Convert blob to base64 (chunk-safe, no stack overflow)
      const buffer = await audioBlob.arrayBuffer();
      const bytes = new Uint8Array(buffer);
      let binary = '';
      const chunkSize = 8192;
      for (let i = 0; i < bytes.length; i += chunkSize) {
        binary += String.fromCharCode.apply(null, bytes.slice(i, i + chunkSize));
      }
      const base64 = btoa(binary);

      // Animate through pipeline
      for (const nodeId of ['livekit', 'pipecat', 'stt']) {
        setActiveNode(nodeId);
        await new Promise((r) => setTimeout(r, 200));
      }

      setActiveNode('stt');
      const { data } = await api.post('/voice/livekit/process', {
        audio_base64: base64,
        context,
        language,
      });

      // Update pipeline visualization based on result
      if (data.error) {
        setActiveNode(data.step || 'stt');
        addMessage('system', `Pipeline error at ${data.step}: ${data.error}`);
      } else {
        // Animate remaining steps
        setActiveNode('guard');
        await new Promise((r) => setTimeout(r, 150));
        setActiveNode('llm');
        await new Promise((r) => setTimeout(r, 150));
        setActiveNode('tts');
        await new Promise((r) => setTimeout(r, 150));
        setActiveNode('speaker');

        setContext(data.context);
        setLastTimings(data.timings);

        // Add user message (transcript)
        if (data.transcript) {
          addMessage('user', data.transcript, null, null, null, data.stt);
        }

        // Add agent response
        if (data.agent_text) {
          addMessage('agent', data.agent_text, data.tts, data.guardrail, data.extracted_fields, data.llm);
        }

        // Auto-play TTS response
        if (data.tts?.audio_base64) {
          playAudio(data.tts.audio_base64, data.tts.content_type);
        }
      }
    } catch (err) {
      addMessage('system', 'Pipeline error: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
      setTimeout(() => setActiveNode(null), 500);
    }
  }

  // --- Text mode: bypass mic/stt, go through LLM→TTS ---
  async function sendText(text) {
    if (!text?.trim() || loading) return;
    setLoading(true);
    setTextInput('');
    addMessage('user', text);

    setActiveNode('guard');
    try {
      const { data } = await api.post('/voice/test-conversation', { text, context });
      setActiveNode('llm');
      await new Promise((r) => setTimeout(r, 200));
      setActiveNode('tts');

      setContext(data.context);
      if (data.agent_text) {
        addMessage('agent', data.agent_text, data.tts, data.guardrail, data.extracted_fields);
      }
      if (data.error) {
        addMessage('system', 'LLM Error: ' + data.error);
      }
      if (data.tts?.audio_base64) {
        setActiveNode('speaker');
        playAudio(data.tts.audio_base64, data.tts.content_type);
      }
    } catch (err) {
      addMessage('system', 'Error: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
      setTimeout(() => setActiveNode(null), 500);
    }
  }

  // --- Microphone ---
  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, sampleRate: 16000 }
      });
      // Try opus/webm, fallback to default
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : '';
      const options = mimeType ? { mimeType } : {};
      mediaRecorder.current = new MediaRecorder(stream, options);
      chunks.current = [];
      mediaRecorder.current.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunks.current.push(e.data);
      };
      mediaRecorder.current.onstop = () => {
        const blob = new Blob(chunks.current, { type: mimeType || 'audio/webm' });
        stream.getTracks().forEach((t) => t.stop());
        if (blob.size > 100) {
          processAudioThroughPipeline(blob);
        } else {
          addMessage('system', 'Kayit cok kisa veya bos — tekrar deneyin');
          setLoading(false);
        }
      };
      mediaRecorder.current.start(1000); // Collect data every 1s
      setRecording(true);
      setActiveNode('mic');
    } catch (err) {
      alert('Mikrofon erisimi reddedildi: ' + err.message);
    }
  }

  function stopRecording() {
    if (mediaRecorder.current && mediaRecorder.current.state !== 'inactive') {
      mediaRecorder.current.stop();
      setRecording(false);
    }
  }

  function addMessage(role, text, tts, guardrail, extractedFields, providerInfo) {
    setConversation((prev) => [...prev, { role, text, tts, guardrail, extractedFields, providerInfo, time: new Date().toLocaleTimeString() }]);
  }

  function playAudio(b64, ct) { new Audio(`data:${ct};base64,${b64}`).play(); }

  function resetAll() {
    setConversation([]); setContext(null); setLivekitStatus('disconnected');
    setLivekitInfo(null); setLastTimings(null); setActiveNode(null);
  }

  const fields = context?.fields || {};
  const state = context?.state || 'greeting';
  const stateInfo = STATE_LABELS[state] || STATE_LABELS.greeting;
  const isConnected = livekitStatus === 'connected';

  return (
    <div className="p-6 max-w-6xl space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Voice Pipeline Test</h1>
          <p className="text-sm text-slate-500">Full pipeline: Browser → LiveKit → Pipecat → STT → Guardrail → LLM → TTS → Speaker</p>
        </div>
        <div className="flex items-center gap-3">
          <select value={language} onChange={(e) => setLanguage(e.target.value)} className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm">
            <option value="tr">Turkce</option><option value="en">English</option>
          </select>
          {isConnected && <button onClick={resetAll} className="px-3 py-1.5 border border-red-300 text-red-600 rounded-lg text-sm hover:bg-red-50">Sifirla</button>}
        </div>
      </div>

      {/* Pipeline Visualization */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex items-center justify-between gap-1 overflow-x-auto">
          {PIPELINE_NODES.map((node, i) => {
            const isActive = activeNode === node.id;
            const isPassed = activeNode && PIPELINE_NODES.findIndex(n => n.id === activeNode) > i;
            return (
              <div key={node.id} className="flex items-center gap-1 shrink-0">
                {i > 0 && <ChevronRightIcon className={`w-3 h-3 ${isPassed ? 'text-green-400' : 'text-slate-300'}`} />}
                <div className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                  isActive ? 'bg-blue-500 text-white border-blue-500 animate-pulse shadow-lg shadow-blue-200' :
                  isPassed ? 'bg-green-100 text-green-700 border-green-300' :
                  'bg-slate-50 text-slate-500 border-slate-200'
                }`}>
                  {node.label}
                </div>
              </div>
            );
          })}
        </div>
        {lastTimings && (
          <div className="flex gap-3 mt-2 text-xs text-slate-400">
            {lastTimings.stt_ms && <span>STT: {lastTimings.stt_ms}ms</span>}
            {lastTimings.llm_ms && <span>LLM: {lastTimings.llm_ms}ms</span>}
            {lastTimings.tts_ms && <span>TTS: {lastTimings.tts_ms}ms</span>}
            {lastTimings.total_ms && <span className="font-medium text-slate-600">Total: {lastTimings.total_ms}ms</span>}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Chat Area */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl border border-slate-200 flex flex-col" style={{ height: '480px' }}>
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {!isConnected && (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <SignalIcon className="w-16 h-16 text-slate-200 mb-4" />
                  <p className="text-sm text-slate-500 mb-2">LiveKit'e baglanip konusmayi baslatin</p>
                  <p className="text-xs text-slate-400 mb-4">Browser → LiveKit (WebRTC) → Pipecat Agent → STT → LLM → TTS</p>
                  <button onClick={connectLiveKit} disabled={livekitStatus === 'connecting'}
                    className="px-6 py-3 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
                    <SignalIcon className="w-5 h-5" />
                    {livekitStatus === 'connecting' ? 'Baglaniyor...' : 'LiveKit Baglantisi Kur'}
                  </button>
                  {livekitStatus === 'error' && <p className="text-xs text-red-500 mt-2">Baglanti hatasi — LiveKit server calismiyor olabilir</p>}
                </div>
              )}
              {conversation.map((msg, i) => (
                <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : msg.role === 'system' ? 'justify-center' : 'justify-start'}`}>
                  {msg.role === 'system' ? (
                    <div className="px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-700 max-w-md">{msg.text}</div>
                  ) : (
                    <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-800'}`}>
                      <p className="text-sm">{msg.text}</p>
                      <div className="flex items-center gap-2 mt-1 flex-wrap">
                        {msg.tts?.audio_base64 && (
                          <button onClick={() => playAudio(msg.tts.audio_base64, msg.tts.content_type)}
                            className={`text-xs flex items-center gap-1 ${msg.role === 'user' ? 'text-blue-200' : 'text-slate-400 hover:text-slate-600'}`}>
                            <SpeakerWaveIcon className="w-3 h-3" /> Dinle
                          </button>
                        )}
                        {msg.providerInfo && <span className="text-xs opacity-60">{msg.providerInfo.provider} {msg.providerInfo.latency_ms}ms</span>}
                        {msg.guardrail && !msg.guardrail.safe && (
                          <span className="text-xs flex items-center gap-1 text-amber-500"><ShieldCheckIcon className="w-3 h-3" />{msg.guardrail.reason}</span>
                        )}
                        <span className={`text-xs ml-auto ${msg.role === 'user' ? 'text-blue-200' : 'text-slate-400'}`}>{msg.time}</span>
                      </div>
                      {msg.extractedFields && Object.keys(msg.extractedFields).length > 0 && (
                        <div className="mt-1.5 pt-1.5 border-t border-slate-200">
                          {Object.entries(msg.extractedFields).map(([k, v]) => (
                            <span key={k} className="inline-block mr-1 mb-1 px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">
                              {REQUIRED_FIELDS[k]?.icon || '📌'} {v}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex justify-start"><div className="bg-slate-100 rounded-2xl px-4 py-3"><ArrowPathIcon className="w-4 h-4 animate-spin text-slate-400" /></div></div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input Bar */}
            {isConnected && (
              <div className="border-t border-slate-200 p-3">
                <div className="flex gap-2">
                  {!textMode ? (
                    !recording ? (
                      <button onClick={startRecording} disabled={loading}
                        className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-red-600 text-white rounded-xl hover:bg-red-700 disabled:opacity-50 font-medium text-sm">
                        <MicrophoneIcon className="w-5 h-5" /> Kayit Baslat (Mikrofon → Full Pipeline)
                      </button>
                    ) : (
                      <button onClick={stopRecording}
                        className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-slate-800 text-white rounded-xl animate-pulse font-medium text-sm">
                        <StopIcon className="w-5 h-5" /> Kaydi Durdur
                      </button>
                    )
                  ) : (
                    <>
                      <input value={textInput} onChange={(e) => setTextInput(e.target.value)}
                        placeholder="Mesajinizi yazin (STT bypass, direkt LLM)..."
                        onKeyDown={(e) => e.key === 'Enter' && sendText(textInput)}
                        disabled={loading} className="flex-1 px-4 py-2.5 border border-slate-300 rounded-xl text-sm disabled:opacity-50" />
                      <button onClick={() => sendText(textInput)} disabled={loading || !textInput.trim()}
                        className="px-5 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 text-sm font-medium">Gonder</button>
                    </>
                  )}
                  <button onClick={() => setTextMode(!textMode)}
                    className="px-3 py-2.5 border border-slate-300 rounded-xl hover:bg-slate-50" title={textMode ? 'Mikrofona gec' : 'Text moduna gec'}>
                    {textMode ? <MicrophoneIcon className="w-4 h-4 text-slate-600" /> : <ChatBubbleLeftRightIcon className="w-4 h-4 text-slate-600" />}
                  </button>
                </div>
                <p className="text-xs text-slate-400 mt-1.5 text-center">
                  {textMode ? 'Text modu: STT atlanir, Guardrail → LLM → TTS' : 'Mikrofon modu: Mic → LiveKit → Pipecat → STT → Guardrail → LLM → TTS → Speaker'}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel */}
        <div className="space-y-4">
          {/* LiveKit Status */}
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <h3 className="text-sm font-semibold text-slate-700 mb-2">LiveKit</h3>
            <div className="flex items-center gap-2">
              <div className={`w-2.5 h-2.5 rounded-full ${livekitStatus === 'connected' ? 'bg-green-500' : livekitStatus === 'connecting' ? 'bg-amber-400 animate-pulse' : 'bg-red-400'}`} />
              <span className="text-sm text-slate-600 capitalize">{livekitStatus}</span>
            </div>
            {livekitInfo && (
              <div className="text-xs text-slate-400 mt-1">
                <p>Room: {livekitInfo.room_name}</p>
                <p>URL: {livekitInfo.livekit_url}</p>
              </div>
            )}
          </div>

          {/* Conversation State */}
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <h3 className="text-sm font-semibold text-slate-700 mb-2">Konusma Durumu</h3>
            <div className="flex items-center gap-2 mb-2">
              <span className={`px-2.5 py-1 rounded-lg text-xs font-medium ${stateInfo.color}`}>{stateInfo.label}</span>
              <span className="text-xs text-slate-400">Turn {context?.turn_count || 0}/20</span>
            </div>
            <div className="flex gap-0.5">
              {['greeting','collect','confirm','create','close'].map((s) => (
                <div key={s} className={`h-1.5 flex-1 rounded-full ${state === s ? 'bg-blue-500' : ['greeting','collect','confirm','create','close'].indexOf(s) < ['greeting','collect','confirm','create','close'].indexOf(state) ? 'bg-green-400' : 'bg-slate-200'}`} />
              ))}
            </div>
          </div>

          {/* Required Fields */}
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <h3 className="text-sm font-semibold text-slate-700 mb-2">Gerekli Bilgiler</h3>
            <div className="space-y-1.5">
              {Object.entries(REQUIRED_FIELDS).map(([key, { label, icon }]) => {
                const value = fields[key];
                return (
                  <div key={key} className={`flex items-center gap-2 p-2 rounded-lg ${value ? 'bg-green-50' : 'bg-slate-50'}`}>
                    <span className="text-sm">{icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-slate-600">{label}</p>
                      {value ? <p className="text-xs font-medium text-green-700 truncate">{value}</p> : <p className="text-xs text-slate-400 italic">-</p>}
                    </div>
                    {value ? <CheckCircleIcon className="w-4 h-4 text-green-500 shrink-0" /> : <div className="w-3.5 h-3.5 rounded-full border-2 border-slate-300 shrink-0" />}
                  </div>
                );
              })}
            </div>
            {context?.all_required_filled && <p className="text-xs text-green-700 font-medium mt-2 text-center bg-green-100 rounded p-1.5">Tum bilgiler toplandi</p>}
          </div>

          {/* Guardrails */}
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <h3 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-1"><ShieldCheckIcon className="w-4 h-4" />Guardrails</h3>
            <div className="space-y-1 text-xs">
              <Row label="Prompt injection" value="Aktif" ok />
              <Row label="Off-topic redirect" value="Aktif" ok />
              <Row label="PII detection" value="Aktif" ok />
              <Row label="Max turns" value={`${context?.turn_count || 0} / 20`} />
              <Row label="Warnings" value={context?.guardrail_warnings || 0} ok={!context?.guardrail_warnings} />
            </div>
          </div>

          {/* Pipeline Config */}
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <h3 className="text-sm font-semibold text-slate-700 mb-2">Pipeline Config</h3>
            <div className="space-y-1 text-xs">
              <Row label="STT" value={config?.stt_provider || '-'} />
              <Row label="LLM" value={config?.llm_provider || '-'} />
              <Row label="TTS" value={config?.tts_provider || '-'} />
              <Row label="Language" value={language} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value, ok }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-slate-500">{label}</span>
      <span className={ok === true ? 'text-green-600' : ok === false ? 'text-amber-600 font-medium' : 'text-slate-700 font-medium'}>{String(value)}</span>
    </div>
  );
}
