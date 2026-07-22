import { useState } from "react";
import { api } from "../api/client.js";
import { usePolling } from "../hooks/usePolling.js";
import EventTable from "../components/EventTable.jsx";

export default function LiveMonitoring() {
  const [source, setSource] = useState("en0");
  const [mode, setMode] = useState("manual");
  const [actionError, setActionError] = useState(null);
  const [busy, setBusy] = useState(false);

  const { data: status, refresh: refreshStatus } = usePolling(() => api.monitoringStatus(), 3000);
  const { data: events } = usePolling(() => api.getEvents({ limit: "25" }), 3000);

  const isRunning = status?.status === "running";

  async function handleStart() {
    setBusy(true);
    setActionError(null);
    try {
      await api.startMonitoring(source, mode);
      await refreshStatus();
    } catch (e) {
      setActionError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleStop() {
    setBusy(true);
    setActionError(null);
    try {
      await api.stopMonitoring();
      await refreshStatus();
    } catch (e) {
      setActionError(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Live Monitoring</h1>
        <p className="text-muted text-sm mt-1">
          Start or stop the capture session and watch flow-level detections as they arrive.
        </p>
      </div>

      <div className="bg-panel border border-border rounded-lg p-5 flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <span
            className={`w-2.5 h-2.5 rounded-full ${isRunning ? "bg-signal pulse-dot" : "bg-muted"}`}
          />
          <div>
            <div className="font-mono text-sm">
              {isRunning
                ? `Running · ${status.mode === "live" ? "live capture" : "manual/demo"} · source: ${status.source}`
                : "Stopped"}
            </div>
            {isRunning && status?.started_at && (
              <div className="text-muted text-xs font-mono">
                since {new Date(status.started_at).toLocaleTimeString()}
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!isRunning && (
            <>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="bg-panel2 border border-border rounded px-3 py-1.5 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-signal"
              >
                <option value="manual">Manual / demo (session tracking only)</option>
                <option value="live">Live capture (real interface, needs sudo)</option>
              </select>
              <input
                value={source}
                onChange={(e) => setSource(e.target.value)}
                placeholder={mode === "live" ? "interface, e.g. en0" : "source label"}
                className="bg-panel2 border border-border rounded px-3 py-1.5 text-sm font-mono w-44 focus:outline-none focus:ring-1 focus:ring-signal"
              />
            </>
          )}
          {isRunning ? (
            <button
              onClick={handleStop}
              disabled={busy}
              className="px-4 py-1.5 rounded bg-critical/10 text-critical border border-critical/30 text-sm font-medium hover:bg-critical/20 transition-colors disabled:opacity-50"
            >
              Stop monitoring
            </button>
          ) : (
            <button
              onClick={handleStart}
              disabled={busy}
              className="px-4 py-1.5 rounded bg-signal/10 text-signal border border-signal/30 text-sm font-medium hover:bg-signal/20 transition-colors disabled:opacity-50"
            >
              Start monitoring
            </button>
          )}
        </div>
      </div>

      {actionError && (
        <div className="text-critical text-sm bg-critical/10 border border-critical/30 rounded px-4 py-2">
          {actionError}
        </div>
      )}

      <div className="bg-panel2/40 border border-border rounded-lg p-4 text-sm text-muted">
        {mode === "live" ? (
          <>
            Live capture sniffs a real network interface and requires the backend to be run
            with root/administrator privileges. If it fails to start, check the interface name
            (<code className="font-mono text-signal">en0</code> on macOS,{" "}
            <code className="font-mono text-signal">eth0</code> on most Linux) and that you
            launched <code className="font-mono text-signal">uvicorn</code> with sudo.
          </>
        ) : (
          <>
            Manual/demo mode tracks session state without capturing real traffic. Use{" "}
            <code className="font-mono text-signal">scripts/generate_demo_traffic.py</code> or{" "}
            <code className="font-mono text-signal">scripts/replay_pcap_to_api.py</code> to
            populate events while in this mode.
          </>
        )}
      </div>

      <div>
        <h2 className="text-sm font-medium text-muted uppercase tracking-wide mb-3">
          Recent Traffic Events
        </h2>
        <EventTable events={events} />
      </div>
    </div>
  );
}
