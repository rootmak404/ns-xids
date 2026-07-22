const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Monitoring control
  startMonitoring: (source = "manual", mode = "manual") =>
    request("/monitoring/start", { method: "POST", body: JSON.stringify({ source, mode }) }),
  stopMonitoring: () => request("/monitoring/stop", { method: "POST" }),
  monitoringStatus: () => request("/monitoring/status"),

  // Prediction
  predict: (payload) => request("/predict", { method: "POST", body: JSON.stringify(payload) }),

  // Events / Alerts
  getEvents: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/events${qs ? `?${qs}` : ""}`);
  },
  getEvent: (id) => request(`/events/${id}`),
  getEventExplanation: (id) => request(`/events/${id}/explanation`),

  // Stats
  overview: () => request("/stats/overview"),
  attackDistribution: () => request("/stats/attack-distribution"),
  severityDistribution: () => request("/stats/severity-distribution"),

  // Rules
  getRules: () => request("/rules"),

  // Test data tools
  uploadCsv: async (file) => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${BASE}/predict/csv`, { method: "POST", body: formData });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Upload failed: ${res.status}`);
    }
    return res.json();
  },
  generateDemoTraffic: (perClass = 1) =>
    request("/demo/generate", { method: "POST", body: JSON.stringify({ per_class: perClass }) }),
};
