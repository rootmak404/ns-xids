import SeverityBadge from "./SeverityBadge.jsx";

function EvidenceBar({ feature, value, shap_contribution, maxAbs }) {
  const positive = shap_contribution >= 0;
  const widthPct = maxAbs > 0 ? Math.min(100, (Math.abs(shap_contribution) / maxAbs) * 100) : 0;
  return (
    <div className="flex items-center gap-3 py-1.5">
      <span className="w-48 shrink-0 text-xs font-mono text-muted truncate" title={feature}>
        {feature}
      </span>
      <div className="flex-1 h-2 bg-panel2 rounded-full overflow-hidden relative">
        <div
          className={`h-full ${positive ? "bg-signal" : "bg-critical/70"}`}
          style={{ width: `${widthPct}%` }}
        />
      </div>
      <span className={`w-16 text-right text-xs font-mono ${positive ? "text-signal" : "text-critical"}`}>
        {positive ? "+" : ""}
        {shap_contribution.toFixed(3)}
      </span>
    </div>
  );
}

export default function ExplanationPanel({ explanation }) {
  if (!explanation) return null;

  const {
    detection,
    confidence,
    model_confidence,
    evidence = [],
    triggered_rules = [],
    conflicting_rules = [],
    final_reasoning,
    risk_level,
    risk_score,
  } = explanation;

  const maxAbs = Math.max(...evidence.map((e) => Math.abs(e.shap_contribution)), 0.001);

  return (
    <div className="bg-panel border border-border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border flex items-center justify-between">
        <div>
          <span className="text-muted text-xs uppercase tracking-wide">Detection</span>
          <div className="text-2xl font-semibold">{detection}</div>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-right">
            <span className="text-muted text-xs uppercase tracking-wide block">Confidence</span>
            <span className="font-mono text-lg">{confidence?.toFixed(1)}%</span>
            {model_confidence !== undefined && (
              <span className="block text-muted text-xs font-mono">model: {model_confidence.toFixed(1)}%</span>
            )}
          </div>
          <div className="text-right">
            <span className="text-muted text-xs uppercase tracking-wide block mb-1">Risk</span>
            <SeverityBadge severity={risk_level} />
            <span className="block text-muted text-xs font-mono mt-1">{risk_score?.toFixed(3)}</span>
          </div>
        </div>
      </div>

      {/* Reasoning trace: Evidence -> Rule -> Verdict */}
      <div className="grid grid-cols-1 lg:grid-cols-3 divide-y lg:divide-y-0 lg:divide-x divide-border">
        {/* Column 1: SHAP Evidence */}
        <div className="p-5">
          <h4 className="text-xs uppercase tracking-wide text-muted font-medium mb-3">
            Feature Evidence
          </h4>
          {evidence.length === 0 ? (
            <p className="text-muted text-sm">No evidence computed for this event.</p>
          ) : (
            evidence.map((e) => (
              <EvidenceBar key={e.feature} {...e} maxAbs={maxAbs} />
            ))
          )}
        </div>

        {/* Column 2: Triggered Rules */}
        <div className="p-5">
          <h4 className="text-xs uppercase tracking-wide text-muted font-medium mb-3">
            Triggered Rules
          </h4>
          {triggered_rules.length === 0 ? (
            <p className="text-muted text-sm">No symbolic rules fired for this prediction.</p>
          ) : (
            <ul className="space-y-2">
              {triggered_rules.map((r) => (
                <li key={r.id} className="flex flex-col gap-0.5">
                  <span className="font-mono text-xs text-signal">{r.id}</span>
                  <span className="text-sm text-text">{r.description}</span>
                </li>
              ))}
            </ul>
          )}

          {conflicting_rules.length > 0 && (
            <>
              <h4 className="text-xs uppercase tracking-wide text-critical font-medium mt-4 mb-2">
                Conflicting Indicators
              </h4>
              <ul className="space-y-2">
                {conflicting_rules.map((r) => (
                  <li key={r.id} className="flex flex-col gap-0.5">
                    <span className="font-mono text-xs text-critical">
                      {r.id} · {r.class}
                    </span>
                    <span className="text-sm text-muted">{r.description}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>

        {/* Column 3: Final Reasoning */}
        <div className="p-5">
          <h4 className="text-xs uppercase tracking-wide text-muted font-medium mb-3">
            Final Reasoning
          </h4>
          <p className="text-sm leading-relaxed text-text">{final_reasoning}</p>
        </div>
      </div>
    </div>
  );
}
