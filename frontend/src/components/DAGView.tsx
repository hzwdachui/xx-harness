import type { TraceRun } from "../api";

export function DAGView({ runs }: { runs: TraceRun[] }) {
  return (
    <div className="pipeline">
      {runs.map((r, i) => (
        <div key={r.node_id} style={{ display: "flex", alignItems: "center", gap: 0 }}>
          <div className={`pipeline-node ${r.status}`}>{r.agent_name || `Node ${r.node_id}`}</div>
          {i < runs.length - 1 && <span className="pipeline-arrow">&rarr;</span>}
        </div>
      ))}
    </div>
  );
}
