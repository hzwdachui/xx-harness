import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";

export function TaskTrace() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      api.tasks.trace(Number(id)).then(setData);
    }, 2000);
    api.tasks.trace(Number(id)).then(setData);
    return () => clearInterval(interval);
  }, [id]);

  if (!data) return <div>Loading...</div>;

  const statusColor = (status: string) => {
    switch (status) {
      case "done": return "#e8f5e9";
      case "failed": return "#ffebee";
      case "waiting_review": return "#fff3e0";
      case "running": return "#e3f2fd";
      default: return "#f5f5f5";
    }
  };

  return (
    <div>
      <h1>Task #{data.task_id} Trace</h1>
      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginTop: 16 }}>
        {data.runs.map((r: any, i: number) => (
          <div key={r.node_id} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ padding: "8px 16px", borderRadius: 4, background: r.status === "done" ? "#4caf50" : r.status === "running" ? "#2196f3" : r.status === "failed" ? "#f44336" : r.status === "waiting_review" ? "#ff9800" : "#9e9e9e", color: "#fff", fontSize: 14 }}>
              Node {r.node_id}: {r.status}
            </div>
            {i < data.runs.length - 1 && <span>&rarr;</span>}
          </div>
        ))}
      </div>
      <div style={{ marginTop: 24 }}>
        {data.runs.map((r: any) => (
          <div key={r.node_id} style={{ border: "1px solid #ccc", padding: 12, marginBottom: 8, background: statusColor(r.status), borderRadius: 4 }}>
            <strong>Node {r.node_id}</strong>: {r.status}
            {r.result && Object.keys(r.result).length > 0 && <pre style={{ fontSize: 12, marginTop: 4 }}>{JSON.stringify(r.result, null, 2)}</pre>}
          </div>
        ))}
      </div>
    </div>
  );
}
