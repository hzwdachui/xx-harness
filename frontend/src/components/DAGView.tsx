export function DAGView({ runs }: { runs: any[] }) {
  const nodeStyle = (status: string) => ({
    padding: "8px 16px", borderRadius: 4, display: "inline-block",
    background: status === "done" ? "#4caf50" : status === "running" ? "#2196f3" :
                status === "failed" ? "#f44336" : status === "waiting_review" ? "#ff9800" : "#9e9e9e",
    color: "#fff", fontSize: 14,
  });

  return (
    <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
      {runs.map((r, i) => (
        <div key={r.node_id} style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={nodeStyle(r.status)}>{r.node_id}</div>
          {i < runs.length - 1 && <span>&rarr;</span>}
        </div>
      ))}
    </div>
  );
}
