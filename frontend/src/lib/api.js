export function apiBaseUrl() {
  const configured = import.meta.env.VITE_API_URL;
  if (configured) return configured.replace(/\/$/, '');
  if (window.location.hostname.includes('frontend')) {
    return window.location.origin.replace('frontend', 'backend').replace('-3000', '-8000');
  }
  return 'http://localhost:8000';
}

export function deviceId() {
  let id = localStorage.getItem('smartroll_device_id');
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem('smartroll_device_id', id);
  }
  return id;
}

export function normalizeUser(user) {
  if (!user) return user;
  const role = user.role?.toLowerCase();
  return { ...user, role: role === 'teacher' || role === 'faculty' ? 'faculty' : 'student' };
}

export async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = localStorage.getItem('smartroll_access_token');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const response = await fetch(`${apiBaseUrl()}${path}`, { ...options, headers });
  let data = {};
  try { data = await response.json(); } catch { /* no response body */ }
  if (!response.ok) throw new Error(data.detail || 'The request could not be completed.');
  if (data.user) data.user = normalizeUser(data.user);
  return data;
}

export async function signInWithGoogle(credential) {
  const result = await api('/api/auth/google', {
    method: 'POST',
    body: JSON.stringify({ credential, device_id: deviceId() }),
  });
  localStorage.setItem('smartroll_access_token', result.access_token);
  return result.user;
}

export function currentPath() {
  return `${window.location.pathname}${window.location.search}${window.location.hash}`;
}

export function safeNextPath() {
  const next = new URLSearchParams(window.location.search).get('next');
  return next && next.startsWith('/') && !next.startsWith('//') ? next : '/faculty';
}
