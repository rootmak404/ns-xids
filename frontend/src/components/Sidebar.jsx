import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Overview", exact: true },
  { to: "/live", label: "Live Monitoring" },
  { to: "/alerts", label: "Alerts" },
  { to: "/explainability", label: "Explainability" },
  { to: "/analytics", label: "Analytics" },
  { to: "/test-data", label: "Test Data" },
];

export default function Sidebar({ monitoringStatus }) {
  const isRunning = monitoringStatus === "running";

  return (
    <aside className="w-60 shrink-0 bg-panel border-r border-border flex flex-col">
      <div className="px-5 py-5 border-b border-border">
        <div className="font-mono text-signal text-sm font-semibold tracking-wide">NS-XIDS</div>
        <div className="text-muted text-xs mt-0.5">Neuro-Symbolic IDS</div>
      </div>

      <nav className="flex-1 py-4">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.exact}
            className={({ isActive }) =>
              `block px-5 py-2.5 text-sm transition-colors border-l-2 ${
                isActive
                  ? "border-signal text-text bg-panel2 font-medium"
                  : "border-transparent text-muted hover:text-text hover:bg-panel2/50"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="px-5 py-4 border-t border-border flex items-center gap-2">
        <span
          className={`w-2 h-2 rounded-full ${
            isRunning ? "bg-signal pulse-dot" : "bg-muted"
          }`}
        />
        <span className="text-xs font-mono text-muted uppercase tracking-wide">
          {isRunning ? "Monitoring active" : "Monitoring stopped"}
        </span>
      </div>
    </aside>
  );
}
