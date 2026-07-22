const SEVERITY_STYLES = {
  Low: "bg-low/10 text-low border-low/30",
  Medium: "bg-medium/10 text-medium border-medium/30",
  High: "bg-high/10 text-high border-high/30",
  Critical: "bg-critical/10 text-critical border-critical/30 animate-pulse",
};

export default function SeverityBadge({ severity }) {
  const style = SEVERITY_STYLES[severity] || "bg-muted/10 text-muted border-muted/30";
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded border text-xs font-mono font-medium tracking-wide uppercase ${style}`}
    >
      {severity || "Unknown"}
    </span>
  );
}
