import { useEffect, useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { api, S } from "../api";
import type { TraceData, Task } from "../api";
import { DAGView } from "../components/DAGView";
import { ErrorBanner } from "../components/ErrorBanner";

export function TaskTrace() {
  const { taskId } = useParams<{ taskId: string }>();
  const [data, setData] = useState<TraceData | null>(null);
  const [task, setTask] = useState<Task | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!taskId) return;
    const numId = Number(taskId);

    // Load initial data via REST
    api.tasks.get(numId)
      .then(res => { setTask(res.task); })
      .catch(e => setError(e.message));
    api.tasks.trace(numId)
      .then(setData)
      .catch(e => setError(e.message));

    // Connect WebSocket for live updates
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${location.host}/ws/tasks/${numId}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);

        // On any update, refresh the trace data
        if (msg.type === "node_update" || msg.type === "task_start" ||
            msg.type === "task_queued" || msg.type === "task_complete" || msg.type === "task_failed") {
          api.tasks.trace(numId).then(setData).catch(() => {});
          if (msg.type !== "node_update") {
            // Task-level status change — refresh task metadata too
            api.tasks.get(numId)
              .then(res => setTask(res.task))
              .catch(() => {});
          }
        }
      } catch { /* ignore parse errors */ }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [taskId]);

  if (error) {
    return (
      <>
        <div className="page-header"><h1>Task Trace</h1></div>
        <div className="page-content">
          <ErrorBanner message={`Error: ${error}`} />
        </div>
      </>
    );
  }

  async function handleCancel() {
    try { await api.tasks.cancel(Number(taskId)); setTask(t => t ? { ...t, status: "cancelled" } : null); } catch (e: any) { setError(e.message); }
  }
  async function handleRetry() {
    try { await api.tasks.retry(Number(taskId)); setTask(t => t ? { ...t, status: "pending" } : null); } catch (e: any) { setError(e.message); }
  }

  if (!data || !task) return <div className="loading">LOADING</div>;

  return (
    <>
      <div className="page-header">
        <h1>{task.title}</h1>
        <p>
          Task #{data.task_id} &middot; {task.task_type} &middot;{" "}
          <span className={`badge badge-${task.status}`}>{task.status}</span>
          {task.project_id && (
            <> &middot; <Link to={`/projects/${task.project_id}`} className="link">Project #{task.project_id}</Link></>
          )}
          {" "}&middot; <span style={{ fontSize: 10, color: connected ? "var(--success)" : "var(--text-muted)" }}>
            {connected ? "LIVE" : "REST"}
          </span>
          {(task.status === S.RUNNING || task.status === S.QUEUED) && (
            <button className="btn btn-sm" style={{ marginLeft: 12 }} onClick={handleCancel}>CANCEL</button>
          )}
          {(task.status === S.FAILED || task.status === S.CANCELLED) && (
            <button className="btn btn-sm" style={{ marginLeft: 12 }} onClick={handleRetry}>RETRY</button>
          )}
        </p>
      </div>

      <div className="page-content">
        <div className="card" style={{ marginBottom: 28 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px 32px" }}>
            <div>
              <span className="form-label">Description</span>
              <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                {task.description || "(no description)"}
              </p>
            </div>
            <div>
              <span className="form-label">Complexity</span>
              <p style={{ fontSize: 13, fontWeight: 600, textTransform: "uppercase" }}>
                {task.complexity || "medium"}
              </p>
            </div>
            <div>
              <span className="form-label">Workflow</span>
              <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                {task.workflow_id ? (
                  <Link to={`/projects/${task.project_id}/workflows/${task.workflow_id}`} className="link">
                    Workflow #{task.workflow_id}
                  </Link>
                ) : "default"}
              </p>
            </div>
            <div>
              <span className="form-label">Created</span>
              <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                {task.created_at || "—"}
              </p>
            </div>
          </div>
        </div>

        <h2 className="section-title">Pipeline</h2>
        {data.runs.length === 0 ? (
          <div className="empty-state">
            <h3>No nodes dispatched</h3>
            <p>The orchestrator has not yet dispatched any agent nodes for this task.</p>
          </div>
        ) : (
          <DAGView runs={data.runs} />
        )}

        <h2 className="section-title" style={{ marginTop: 36 }}>Run Log</h2>
        {data.runs.length === 0 ? (
          <div className="empty-state">
            <h3>No runs</h3>
            <p>Waiting for the orchestrator to dispatch the first agent node.</p>
          </div>
        ) : (
          <div className="trace-log">
            {data.runs.map((r) => (
              <div key={r.node_id} className="trace-log-item">
                <div className={`trace-log-status ${r.status}`}>{r.status}</div>
                <div className="trace-log-body">
                  <strong>{r.agent_name || `Node ${r.node_id}`}</strong>
                  {r.result && Object.keys(r.result).length > 0 && (
                    <pre>{JSON.stringify(r.result, null, 2)}</pre>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        <p className="trace-refresh-hint">
          {connected ? "WebSocket connected — live updates" : "WebSocket disconnected — reload to reconnect"}
        </p>
      </div>
    </>
  );
}
