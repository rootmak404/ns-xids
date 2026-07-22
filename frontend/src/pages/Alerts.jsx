import { useState } from "react";
import { api } from "../api/client.js";
import { usePolling } from "../hooks/usePolling.js";
import EventTable from "../components/EventTable.jsx";

const SEVERITIES = ["Low", "Medium", "High", "Critical"];
const CLASSES = ["PortScan", "Brute_Force", "DoS_Attack", "DoS Hulk", "DDoS"];

export default function Alerts() {
  const [severity, setSeverity] = useState("");
  const [predictedClass, setPredictedClass] = useState("");

  const params = { limit: "100" };
  if (severity) params.severity = severity;
  if (predictedClass) params.predicted_class = predictedClass;

  const { data: events } = usePolling(() => api.getEvents(params), 4000, [severity, predictedClass]);

  // Alerts page only shows non-benign events by default
  const filtered = (events || []).filter((e) => e.predicted_class !== "BENIGN");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Alerts</h1>
        <p className="text-muted text-sm mt-1">
          All non-benign detections, filterable by severity and attack type.
        </p>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <select
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
          className="bg-panel2 border border-border rounded px-3 py-1.5 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-signal"
        >
          <option value="">All severities</option>
          {SEVERITIES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <select
          value={predictedClass}
          onChange={(e) => setPredictedClass(e.target.value)}
          className="bg-panel2 border border-border rounded px-3 py-1.5 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-signal"
        >
          <option value="">All attack types</option>
          {CLASSES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        {(severity || predictedClass) && (
          <button
            onClick={() => { setSeverity(""); setPredictedClass(""); }}
            className="text-muted text-xs hover:text-text underline"
          >
            Clear filters
          </button>
        )}

        <span className="text-muted text-xs ml-auto font-mono">{filtered.length} result(s)</span>
      </div>

      <EventTable
        events={filtered}
        emptyMessage="No alerts match the current filters."
      />
    </div>
  );
}
