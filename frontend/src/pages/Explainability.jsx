import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import { usePolling } from "../hooks/usePolling.js";
import ExplanationPanel from "../components/ExplanationPanel.jsx";
import SeverityBadge from "../components/SeverityBadge.jsx";

export default function Explainability() {
  const { eventId } = useParams();
  const navigate = useNavigate();
  const [explanation, setExplanation] = useState(null);
  const [loadError, setLoadError] = useState(null);

  const { data: events } = usePolling(() => api.getEvents({ limit: "30" }), 5000);

  useEffect(() => {
    if (!eventId) {
      setExplanation(null);
      return;
    }
    setLoadError(null);
    api
      .getEventExplanation(eventId)
      .then((exp) => {
        setExplanation({
          detection: exp.detection,
          confidence: exp.confidence,
          model_confidence: exp.model_confidence,
          evidence: exp.evidence || [],
          triggered_rules: exp.triggered_rules || [],
          conflicting_rules: exp.conflicting_rules || [],
          final_reasoning: exp.final_reasoning,
          risk_level: exp.risk_level,
          risk_score: exp.risk_score,
        });
      })
      .catch((e) => setLoadError(e.message));
  }, [eventId]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Explainability</h1>
        <p className="text-muted text-sm mt-1">
          Select a detection to see the model's prediction, the supporting evidence, the rules
          it triggered, and the final reasoning behind the verdict.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Event picker */}
        <div className="lg:col-span-1 space-y-2 max-h-[70vh] overflow-y-auto pr-1">
          {(events || []).length === 0 && (
            <p className="text-muted text-sm">No events yet.</p>
          )}
          {(events || []).map((e) => (
            <button
              key={e.id}
              onClick={() => navigate(`/explainability/${e.id}`)}
              className={`w-full text-left px-3 py-2 rounded border text-sm transition-colors ${
                String(e.id) === eventId
                  ? "border-signal bg-panel2"
                  : "border-border bg-panel hover:bg-panel2/60"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs text-muted">#{e.id}</span>
                <SeverityBadge severity={e.severity} />
              </div>
              <div className="font-medium mt-1">{e.predicted_class}</div>
              <div className="text-muted text-xs font-mono">
                {new Date(e.timestamp).toLocaleTimeString()}
              </div>
            </button>
          ))}
        </div>

        {/* Explanation detail */}
        <div className="lg:col-span-3">
          {loadError && (
            <div className="text-critical text-sm bg-critical/10 border border-critical/30 rounded px-4 py-2 mb-4">
              {loadError}
            </div>
          )}
          {!eventId && (
            <div className="border border-border rounded-lg p-10 text-center text-muted text-sm">
              Select an event from the list to view its explanation.
            </div>
          )}
          {eventId && explanation && <ExplanationPanel explanation={explanation} />}
        </div>
      </div>
    </div>
  );
}
