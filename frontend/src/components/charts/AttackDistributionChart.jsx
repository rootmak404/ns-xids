import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";

const COLORS = ["#2DD4BF", "#FBBF24", "#FB923C", "#F87171", "#818CF8", "#34D399"];

export default function AttackDistributionChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="text-muted text-sm">No data yet.</p>;
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="class"
          cx="50%"
          cy="50%"
          outerRadius={90}
          label={({ class: cls, count }) => `${cls} (${count})`}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: "#171C27", border: "1px solid #232838", borderRadius: 8 }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
