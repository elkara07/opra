import axios from 'axios';

const api = axios.create({ baseURL: '/api/v1' });

// Attach JWT from sessionStorage
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => (error ? prom.reject(error) : prom.resolve(token)));
  failedQueue = [];
};

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          original.headers.Authorization = `Bearer ${token}`;
          return api(original);
        });
      }
      original._retry = true;
      isRefreshing = true;
      try {
        const rt = sessionStorage.getItem('refresh_token');
        if (!rt) throw new Error('No refresh token');
        const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: rt });
        sessionStorage.setItem('access_token', data.access_token);
        sessionStorage.setItem('refresh_token', data.refresh_token);
        processQueue(null, data.access_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch (err) {
        processQueue(err, null);
        sessionStorage.clear();
        window.location.href = '/login';
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// --- API functions ---
export const authApi = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  logout: (refresh_token) => api.post('/auth/logout', { refresh_token }),
};

export const ticketApi = {
  list: (params) => api.get('/tickets', { params }),
  get: (id) => api.get(`/tickets/${id}`),
  create: (data) => api.post('/tickets', data),
  update: (id, data) => api.put(`/tickets/${id}`, data),
  changeStatus: (id, status) => api.post(`/tickets/${id}/status`, { status }),
  assign: (id, data) => api.post(`/tickets/${id}/assign`, data),
  addComment: (id, comment, isPublic) => api.post(`/tickets/${id}/comments`, { comment, is_public: isPublic }),
  timeline: (id) => api.get(`/tickets/${id}/timeline`),
};

export const contactApi = {
  list: (params) => api.get('/contacts', { params }),
  get: (id) => api.get(`/contacts/${id}`),
  create: (data) => api.post('/contacts', data),
  update: (id, data) => api.put(`/contacts/${id}`, data),
};

export const slaApi = {
  list: () => api.get('/sla-configs'),
  create: (data) => api.post('/sla-configs', data),
};

export const escalationApi = {
  list: () => api.get('/escalation-rules'),
  create: (data) => api.post('/escalation-rules', data),
};

export const projectApi = {
  list: () => api.get('/projects'),
  stats: () => api.get('/projects/stats'),
  get: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  setJiraMapping: (id, key) => api.put(`/projects/${id}/jira-mapping?jira_project_key=${encodeURIComponent(key)}`),
  importCSV: (formData) => api.post('/projects/import-csv', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
};

export const emailApi = {
  listMailboxes: () => api.get('/email/mailboxes'),
  createMailbox: (data) => api.post('/email/mailboxes', data),
  deleteMailbox: (id) => api.delete(`/email/mailboxes/${id}`),
};

export const voiceApi = {
  calls: (params) => api.get('/voice/calls', { params }),
  callDetail: (id) => api.get(`/voice/calls/${id}`),
  didMappings: () => api.get('/voice/did-mappings'),
  createDid: (data) => api.post('/voice/did-mappings', data),
  providers: () => api.get('/voice/providers'),
  agentStatus: () => api.get('/voice/agent/status'),
  getConfig: () => api.get('/voice/config'),
  updateConfig: (data) => api.put('/voice/config', data),
  saveApiKey: (key_name, key_value) => api.post('/voice/api-keys', { key_name, key_value }),
  listApiKeys: () => api.get('/voice/api-keys'),
};

export const jiraApi = {
  getConfig: () => api.get('/jira/config'),
  updateConfig: (data) => api.put('/jira/config', data),
  testConnection: () => api.post('/jira/test-connection'),
  forceSync: (ticketId) => api.post(`/jira/sync/${ticketId}`),
};

export const ldapApi = {
  getConfig: () => api.get('/ldap/config'),
  updateConfig: (data) => api.put('/ldap/config', data),
  testConnection: () => api.post('/ldap/test-connection'),
  triggerSync: () => api.post('/ldap/sync'),
};

export const reportApi = {
  slaCompliance: (days) => api.get('/reports/sla-compliance', { params: { days } }),
  ticketVolume: (days) => api.get('/reports/ticket-volume', { params: { days } }),
  escalationFrequency: (days) => api.get('/reports/escalation-frequency', { params: { days } }),
  agentPerformance: (days) => api.get('/reports/agent-performance', { params: { days } }),
  callAnalytics: (days) => api.get('/reports/call-analytics', { params: { days } }),
};
