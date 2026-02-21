import axios from 'axios';

const BASE = '/api';
const api = axios.create({ baseURL: BASE });

// ── REQUEST: inject token on every call ───────────────────────────────────
api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('sfda_token');
  if (token) cfg.headers.Authorization = `Token ${token}`;
  return cfg;
});

// ── RESPONSE: on 401 → wipe stale token and force re-login ───────────────
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      // Only clear if it's NOT an auth endpoint (avoid loop on wrong password)
      const url = err.config?.url || '';
      const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/signup');
      if (!isAuthEndpoint) {
        localStorage.removeItem('sfda_token');
        localStorage.removeItem('sfda_user');
        // Reload → App.jsx will detect no token and show login
        window.dispatchEvent(new CustomEvent('sfda_unauthorized'));
        
      }
    }
    return Promise.reject(err);
  }
);

// ── Auth API ──────────────────────────────────────────────────────────────
export const authLogin    = (email, password) => api.post('/auth/login/',  { email, password });
export const authSignup   = (data)            => api.post('/auth/signup/', data);
export const authForgot   = (email)           => api.post('/auth/forgot/', { email });
export const authLogout   = ()                => api.post('/auth/logout/');
export const authMe       = ()                => api.get('/auth/me/');

// ── Auth helpers (localStorage) ───────────────────────────────────────────
export const saveAuth        = (token, user) => { localStorage.setItem('sfda_token', token); localStorage.setItem('sfda_user', JSON.stringify(user)); };
export const clearAuth       = ()            => { localStorage.removeItem('sfda_token'); localStorage.removeItem('sfda_user'); };
export const getStoredUser   = ()            => { try { return JSON.parse(localStorage.getItem('sfda_user')); } catch { return null; } };
export const isAuthenticated = ()            => !!localStorage.getItem('sfda_token');

// ── Reports API ───────────────────────────────────────────────────────────
export const getReports      = ()          => api.get('/reports/');
export const getReport       = id          => api.get(`/reports/${id}/`);
export const createReport    = data        => api.post('/reports/', data);
export const updateReport    = (id, data)  => api.patch(`/reports/${id}/`, data);
export const deleteReport    = id          => api.delete(`/reports/${id}/`);
export const generateAI      = id          => api.post(`/reports/${id}/generate/`);
export const getStats        = ()          => api.get('/stats/');
export const chatAssistant   = (messages, system) => api.post('/assistant/', { messages, system });

// ── PDF / Preview URLs ────────────────────────────────────────────────────
export const getPDFUrl       = id => `${BASE}/reports/${id}/pdf/`;
export const getInlinePDFUrl = id => `${BASE}/reports/${id}/pdf/inline/`;
export const getPreviewUrl   = id => `${BASE}/reports/${id}/preview/`;
