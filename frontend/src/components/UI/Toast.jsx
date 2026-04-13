import { useEffect, useState } from 'react';

let toastId = 0;
const listeners = [];

export function toast(message, type = 'info', duration = 4000) {
  const id = ++toastId;
  listeners.forEach(fn => fn({ id, message, type, duration }));
}

toast.success = (msg, dur) => toast(msg, 'success', dur);
toast.error   = (msg, dur) => toast(msg, 'error',   dur);
toast.warning = (msg, dur) => toast(msg, 'warning', dur);
toast.info    = (msg, dur) => toast(msg, 'info',     dur);

export function ToastContainer() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const handler = (t) => {
      setToasts(prev => [...prev, t]);
      setTimeout(() => {
        setToasts(prev => prev.filter(x => x.id !== t.id));
      }, t.duration);
    };
    listeners.push(handler);
    return () => {
      const idx = listeners.indexOf(handler);
      if (idx > -1) listeners.splice(idx, 1);
    };
  }, []);

  const colors = {
    success: { bg: '#f0fdf4', border: '#86efac', text: '#166534', icon: '✓' },
    error:   { bg: '#fef2f2', border: '#fca5a5', text: '#991b1b', icon: '✗' },
    warning: { bg: '#fffbeb', border: '#fcd34d', text: '#92400e', icon: '!' },
    info:    { bg: '#eff6ff', border: '#93c5fd', text: '#1e40af', icon: 'i' },
  };

  return (
    <div style={{
      position: 'fixed', bottom: '1.5rem', right: '1.5rem',
      zIndex: 9999, display: 'flex', flexDirection: 'column', gap: '0.5rem',
      maxWidth: '360px', width: '100%',
    }}>
      {toasts.map(t => {
        const c = colors[t.type] || colors.info;
        return (
          <div key={t.id} style={{
            background: c.bg,
            border: `1px solid ${c.border}`,
            color: c.text,
            borderRadius: '0.75rem',
            padding: '0.875rem 1rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.625rem',
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
            animation: 'slideIn 0.2s ease',
          }}>
            <span style={{
              width: 20, height: 20, borderRadius: '50%',
              background: c.border, display: 'flex',
              alignItems: 'center', justifyContent: 'center',
              fontSize: 11, fontWeight: 700, flexShrink: 0,
            }}>{c.icon}</span>
            <span style={{ fontSize: 14, lineHeight: 1.5 }}>{t.message}</span>
          </div>
        );
      })}
      <style>{`@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }`}</style>
    </div>
  );
}
