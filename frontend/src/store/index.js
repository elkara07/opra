import { create } from 'zustand';
import { authApi, ticketApi } from '../api/client';

export const useAuthStore = create((set, get) => ({
  user: null,
  token: sessionStorage.getItem('access_token'),
  loading: false,
  error: null,

  login: async (email, password) => {
    // CRITICAL: clear everything from previous session first
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    set({ loading: true, error: null, user: null, token: null });

    try {
      const { data } = await authApi.login(email, password);
      sessionStorage.setItem('access_token', data.access_token);
      sessionStorage.setItem('refresh_token', data.refresh_token);
      // Set token — this triggers App.jsx useEffect to fetchMe
      set({ token: data.access_token, loading: false });
      // Immediately fetch new user profile
      const { data: me } = await authApi.me();
      set({ user: me });
    } catch (err) {
      sessionStorage.removeItem('access_token');
      sessionStorage.removeItem('refresh_token');
      set({ error: err.response?.data?.detail || 'Login failed', loading: false, token: null, user: null });
    }
  },

  fetchMe: async () => {
    try {
      const { data } = await authApi.me();
      set({ user: data });
    } catch {
      sessionStorage.removeItem('access_token');
      sessionStorage.removeItem('refresh_token');
      set({ user: null, token: null });
    }
  },

  logout: async () => {
    const rt = sessionStorage.getItem('refresh_token');
    // Clear storage FIRST before any async call
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    // Clear store
    set({ user: null, token: null, error: null });
    // Fire and forget server-side logout
    if (rt) authApi.logout(rt).catch(() => {});
  },
}));

export const useTicketStore = create((set) => ({
  tickets: [],
  total: 0,
  loading: false,
  filters: { status: '', priority: '', page: 1, size: 50 },

  setFilters: (f) => set((s) => ({ filters: { ...s.filters, ...f } })),

  fetch: async (params) => {
    set({ loading: true });
    try {
      const { data } = await ticketApi.list(params);
      set({ tickets: data.items, total: data.total, loading: false });
    } catch {
      set({ loading: false });
    }
  },
}));
