import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

function bucketByHour(events) {
  const buckets = {};
  events.forEach((e) => {
    const d = new Date(e.timestamp);
    const key = `${d.getHours().toString().padStart(2, "0")}:00`;
    buckets[key] = buckets[key] || { time: key, total: 0, attacks: 0 };
    buckets[key].total += 1;
    if (e.predicted_class !== "BENIGN") buckets[key].attacks += 1;
  });
  return Object.values(buckets).sort((a, b) => a.time.localeCompare(b.time));
}

export default function TimelineChart({ events }) {
  const data = bucketByHour(events || []);
  if (data.length === 0) {
    return <p className="text-muted text-sm">No traffic history yet.</p>;
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data}>
        <XAxis dataKey="time" stroke="#7C8494" fontSize={12} />
        <YAxis stroke="#7C8494" fontSize={12} allowDecimals={false} />
        <Tooltip
          contentStyle={{ background: "#171C27", border: "1px solid #232838", borderRadius: 8 }}
        />
        <Line type="monotone" dataKey="total" stroke="#7C8494" strokeWidth={2} dot={false} name="All traffic" />
        <Line type="monotone" dataKey="attacks" stroke="#F87171" strokeWidth={2} dot={false} name="Attacks" />
      </LineChart>
    </ResponsiveContainer>
  );
}
