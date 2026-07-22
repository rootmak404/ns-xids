import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const SEVERITY_COLORS = {
  Low: "#4ADE80",
  Medium: "#FBBF24",
  High: "#FB923C",
  Critical: "#F87171",
};

export default function SeverityDistributionChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="text-muted text-sm">No data yet.</p>;
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data}>
        <XAxis dataKey="severity" stroke="#7C8494" fontSize={12} />
        <YAxis stroke="#7C8494" fontSize={12} allowDecimals={false} />
        <Tooltip
          contentStyle={{ background: "#171C27", border: "1px solid #232838", borderRadius: 8 }}
          cursor={{ fill: "#171C27" }}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {data.map((d, i) => (
            <Cell key={i} fill={SEVERITY_COLORS[d.severity] || "#7C8494"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
