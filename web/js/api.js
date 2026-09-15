async function request(path, options = {}) {
  const response = await fetch(path, { credentials: "same-origin", ...options });
  let data = null;
  try { data = await response.json(); } catch { data = null; }
  if (!response.ok) throw new Error(data && typeof data.error === "string" ? data.error : "Request failed");
  return data;
}

export const apiGet = (path, options = {}) => request(path, { ...options, method: "GET" });
export const apiPost = (path, payload, options = {}) => request(path, {
  ...options,
  method: "POST",
  headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  body: JSON.stringify(payload),
});

export const health = () => apiGet('/api/health');
export const status = () => apiGet('/api/status');
export const providers = (check = false) => apiGet(`/api/providers?check=${check ? "1" : "0"}`);
export const models = () => apiGet('/api/models');
export const capabilities = () => apiGet('/api/capabilities');
export const mcp = () => apiGet('/api/mcp');
export const skills = () => apiGet('/api/skills');
export const integrations = () => apiGet('/api/integrations');
export const tasks = (id = null) => apiGet(id ? `/api/tasks?id=${encodeURIComponent(id)}` : '/api/tasks');
export const events = (runId) => apiGet('/api/events?run_id=' + encodeURIComponent(runId));
export const chat = (message, signal) => apiPost('/api/chat', { message }, { signal });
export const enqueueTask = (message) => apiPost('/api/tasks', { message });
