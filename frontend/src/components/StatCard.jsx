export default function StatCard({ label, value, accentClass = "text-text", sublabel }) {
  return (
    <div className="bg-panel border border-border rounded-lg p-4 flex flex-col gap-1">
      <span className="text-muted text-xs font-medium uppercase tracking-wide">{label}</span>
      <span className={`text-3xl font-mono font-semibold ${accentClass}`}>{value}</span>
      {sublabel && <span className="text-muted text-xs">{sublabel}</span>}
    </div>
  );
}
