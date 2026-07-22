import { api } from "../api/client.js";
import { usePolling } from "../hooks/usePolling.js";
import StatCard from "../components/StatCard.jsx";
import EventTable from "../components/EventTable.jsx";

export default function Overview() {
  const { data: stats } = usePolling(() => api.overview(), 5000);
  const { data: events } = usePolling(() => api.getEvents({ limit: "8" }), 5000);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Overview</h1>
        <p className="text-muted text-sm mt-1">
          Live summary of detection activity across the monitored source.
        </p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Events" value={stats?.total_events ?? "—"} />
        <StatCard
          label="Normal Traffic"
          value={stats?.benign_events ?? "—"}
          accentClass="text-low"
        />
        <StatCard
          label="Detected Attacks"
          value={stats?.detected_attacks ?? "—"}
          accentClass="text-high"
        />
        <StatCard
          label="High-Risk Alerts"
          value={stats?.high_risk_alerts ?? "—"}
          accentClass="text-critical"
        />
      </div>

      <div className="bg-panel border border-border rounded-lg p-4 flex items-center justify-between">
        <div>
          <span className="text-muted text-xs uppercase tracking-wide">Monitoring status</span>
          <div className="font-mono text-lg mt-0.5 capitalize">
            {stats?.monitoring_status ?? "unknown"}
          </div>
        </div>
        <span className="text-muted text-xs">
          Control monitoring from the Live Monitoring page.
        </span>
      </div>

      <div>
        <h2 className="text-sm font-medium text-muted uppercase tracking-wide mb-3">
          Recent Events
        </h2>
        <EventTable events={events} emptyMessage="No events recorded yet. Start monitoring or submit a prediction to see activity here." />
      </div>
    </div>
  );
}
