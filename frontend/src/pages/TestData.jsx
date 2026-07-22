import { useState, useRef } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import SeverityBadge from "../components/SeverityBadge.jsx";

const SEVERITY_ORDER = ["Critical", "High", "Medium", "Low"];

function SeveritySummary({ counts }) {
  if (!counts || Object.keys(counts).length === 0) return null;
  return (
    <div className="flex items-center gap-3 flex-wrap">
      {SEVERITY_ORDER.filter((s) => counts[s]).map((s) => (
        <div key={s} className="flex items-center gap-2 bg-panel2 border border-border rounded px-3 py-1.5">
          <SeverityBadge severity={s} />
          <span className="font-mono text-sm">{counts[s]}</span>
        </div>
      ))}
    </div>
  );
}

function ResultsTable({ results, showIntended }) {
  if (!results || results.length === 0) return null;
  return (
    <div className="border border-border rounded-lg overflow-hidden mt-4">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-panel2 text-muted text-xs uppercase tracking-wide">
            {showIntended && <th className="text-left font-medium px-4 py-2">Intended</th>}
            <th className="text-left font-medium px-4 py-2">Predicted</th>
            <th className="text-left font-medium px-4 py-2">Confidence</th>
            <th className="text-left font-medium px-4 py-2">Severity</th>
            <th className="text-left font-medium px-4 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {results.map((r) => (
            <tr key={r.event_id} className="border-t border-border">
              {showIntended && <td className="px-4 py-2 text-muted">{r.intended_class}</td>}
              <td className="px-4 py-2 font-medium">{r.predicted_class}</td>
              <td className="px-4 py-2 font-mono text-muted">{r.confidence.toFixed(1)}%</td>
              <td className="px-4 py-2"><SeverityBadge severity={r.severity} /></td>
              <td className="px-4 py-2 text-right">
                <Link to={`/explainability/${r.event_id}`} className="text-signal text-xs hover:underline">
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

export default function TestData() {
  const fileInputRef = useRef(null);
  const [csvFile, setCsvFile] = useState(null);
  const [csvBusy, setCsvBusy] = useState(false);
  const [csvError, setCsvError] = useState(null);
  const [csvResult, setCsvResult] = useState(null);

  const [perClass, setPerClass] = useState(1);
  const [demoBusy, setDemoBusy] = useState(false);
  const [demoError, setDemoError] = useState(null);
  const [demoResult, setDemoResult] = useState(null);

  async function handleCsvUpload() {
    if (!csvFile) return;
    setCsvBusy(true);
    setCsvError(null);
    setCsvResult(null);
    try {
      const result = await api.uploadCsv(csvFile);
      setCsvResult(result);
    } catch (e) {
      setCsvError(e.message);
    } finally {
      setCsvBusy(false);
    }
  }

  async function handleGenerate() {
    setDemoBusy(true);
    setDemoError(null);
    setDemoResult(null);
    try {
      const result = await api.generateDemoTraffic(perClass);
      setDemoResult(result);
    } catch (e) {
      setDemoError(e.message);
    } finally {
      setDemoBusy(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold">Test Data</h1>
        <p className="text-muted text-sm mt-1">
          Feed the pipeline traffic without needing a live capture or curl commands.
        </p>
      </div>

      {/* CSV Upload */}
      <section className="bg-panel border border-border rounded-lg p-5 space-y-4">
        <div>
          <h2 className="font-medium">Upload CSV</h2>
          <p className="text-muted text-sm mt-1">
            Upload a CSV containing the 35 required flow-feature columns (a CICIDS2017-style
            export, or your own captured/labeled data). Extra columns like a{" "}
            <code className="font-mono text-signal">Label</code> column are ignored. Every row
            is run through the full pipeline and shows up on the dashboard immediately.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={(e) => { setCsvFile(e.target.files?.[0] || null); setCsvResult(null); setCsvError(null); }}
            className="text-sm text-muted file:mr-3 file:py-1.5 file:px-3 file:rounded file:border file:border-border file:bg-panel2 file:text-text file:text-sm file:cursor-pointer hover:file:bg-panel2/70"
          />
          <button
            onClick={handleCsvUpload}
            disabled={!csvFile || csvBusy}
            className="px-4 py-1.5 rounded bg-signal/10 text-signal border border-signal/30 text-sm font-medium hover:bg-signal/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {csvBusy ? "Processing…" : "Upload & Run"}
          </button>
        </div>

        {csvError && (
          <div className="text-critical text-sm bg-critical/10 border border-critical/30 rounded px-4 py-2">
            {csvError}
          </div>
        )}

        {csvResult && (
          <div className="space-y-3">
            <div className="text-sm text-muted">
              Processed <span className="text-text font-mono">{csvResult.rows_processed}</span> row(s)
              {csvResult.rows_skipped > 0 && (
                <> · skipped <span className="text-high font-mono">{csvResult.rows_skipped}</span> malformed row(s)</>
              )}
              {" "}from <span className="text-text">{csvResult.filename}</span>
            </div>
            <SeveritySummary counts={csvResult.severity_counts} />
            <ResultsTable results={csvResult.results} showIntended={false} />
          </div>
        )}
      </section>

      {/* Quick severity generator */}
      <section className="bg-panel border border-border rounded-lg p-5 space-y-4">
        <div>
          <h2 className="font-medium">Generate Test Traffic</h2>
          <p className="text-muted text-sm mt-1">
            One click: creates rule-shaped samples across every class (BENIGN + all 5 attack
            types) so you immediately see a full spread of severity levels on the dashboard.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-sm text-muted flex items-center gap-2">
            Samples per class
            <input
              type="number"
              min="1"
              max="10"
              value={perClass}
              onChange={(e) => setPerClass(Math.max(1, Math.min(10, Number(e.target.value) || 1)))}
              className="bg-panel2 border border-border rounded px-2 py-1 text-sm font-mono w-16 focus:outline-none focus:ring-1 focus:ring-signal"
            />
          </label>
          <button
            onClick={handleGenerate}
            disabled={demoBusy}
            className="px-4 py-1.5 rounded bg-signal/10 text-signal border border-signal/30 text-sm font-medium hover:bg-signal/20 transition-colors disabled:opacity-40"
          >
            {demoBusy ? "Generating…" : "Generate Test Traffic"}
          </button>
        </div>

        {demoError && (
          <div className="text-critical text-sm bg-critical/10 border border-critical/30 rounded px-4 py-2">
            {demoError}
          </div>
        )}

        {demoResult && (
          <div className="space-y-3">
            <div className="text-sm text-muted">
              Generated <span className="text-text font-mono">{demoResult.generated}</span> event(s)
              across all severity levels.
            </div>
            <SeveritySummary counts={demoResult.severity_counts} />
            <ResultsTable results={demoResult.results} showIntended={true} />
          </div>
        )}
      </section>
    </div>
  );
}
