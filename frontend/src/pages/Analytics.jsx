import { api } from "../api/client.js";
import { usePolling } from "../hooks/usePolling.js";
import AttackDistributionChart from "../components/charts/AttackDistributionChart.jsx";
import SeverityDistributionChart from "../components/charts/SeverityDistributionChart.jsx";
import TimelineChart from "../components/charts/TimelineChart.jsx";

export default function Analytics() {
  const { data: attackDist } = usePolling(() => api.attackDistribution(), 8000);
  const { data: severityDist } = usePolling(() => api.severityDistribution(), 8000);
  const { data: events } = usePolling(() => api.getEvents({ limit: "200" }), 8000);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Analytics</h1>
        <p className="text-muted text-sm mt-1">
          Aggregate trends across all recorded detections.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-panel border border-border rounded-lg p-5">
          <h2 className="text-sm font-medium text-muted uppercase tracking-wide mb-3">
            Attack Distribution
          </h2>
          <AttackDistributionChart data={attackDist} />
        </div>

        <div className="bg-panel border border-border rounded-lg p-5">
          <h2 className="text-sm font-medium text-muted uppercase tracking-wide mb-3">
            Severity Distribution
          </h2>
          <SeverityDistributionChart data={severityDist} />
        </div>
      </div>

      <div className="bg-panel border border-border rounded-lg p-5">
        <h2 className="text-sm font-medium text-muted uppercase tracking-wide mb-3">
          Traffic Timeline (last 200 events, grouped by hour)
        </h2>
        <TimelineChart events={events} />
      </div>
    </div>
  );
}
