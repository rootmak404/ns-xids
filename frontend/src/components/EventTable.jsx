import { Link } from "react-router-dom";
import SeverityBadge from "./SeverityBadge.jsx";

function formatTime(ts) {
  try {
    return new Date(ts).toLocaleTimeString();
  } catch {
    return ts;
  }
}

export default function EventTable({ events, emptyMessage = "No events yet." }) {
  if (!events || events.length === 0) {
    return (
      <div className="border border-border rounded-lg p-8 text-center text-muted text-sm">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-panel2 text-muted text-xs uppercase tracking-wide">
            <th className="text-left font-medium px-4 py-2">Time</th>
            <th className="text-left font-medium px-4 py-2">Source</th>
            <th className="text-left font-medium px-4 py-2">Destination</th>
            <th className="text-left font-medium px-4 py-2">Detection</th>
            <th className="text-left font-medium px-4 py-2">Confidence</th>
            <th className="text-left font-medium px-4 py-2">Severity</th>
            <th className="text-left font-medium px-4 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {events.map((e) => (
            <tr key={e.id} className="border-t border-border hover:bg-panel2/60 transition-colors">
              <td className="px-4 py-2 font-mono text-muted">{formatTime(e.timestamp)}</td>
              <td className="px-4 py-2 font-mono">
                {e.src_ip || "—"}
                {e.src_port ? `:${e.src_port}` : ""}
              </td>
              <td className="px-4 py-2 font-mono">
                {e.dst_ip || "—"}
                {e.dst_port ? `:${e.dst_port}` : ""}
              </td>
              <td className="px-4 py-2 font-medium">{e.predicted_class}</td>
              <td className="px-4 py-2 font-mono text-muted">{e.adjusted_confidence?.toFixed(1)}%</td>
              <td className="px-4 py-2">
                <SeverityBadge severity={e.severity} />
              </td>
              <td className="px-4 py-2 text-right">
                <Link to={`/explainability/${e.id}`} className="text-signal text-xs hover:underline">
                  Explain →
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
