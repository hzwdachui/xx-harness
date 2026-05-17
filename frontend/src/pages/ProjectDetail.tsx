import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, S } from "../api";
import type { Project, Task, WorkflowItem, Issue } from "../api";
import { ErrorBanner } from "../components/ErrorBanner";

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const [project, setProject] = useState<Project | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");

  function loadAll() {
    setLoading(true);
    setError(null);
    Promise.all([
      api.projects.get(projectId).then(setProject),
      api.tasks.listByProject(projectId).then(setTasks),
      api.workflows.listByProject(projectId).then(setWorkflows),
      api.issues.listByProject(projectId).then(setIssues),
    ]).catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => { loadAll(); }, [projectId]);

  async function cancelTask(taskId: number) {
    try { await api.tasks.cancel(taskId); loadAll(); } catch (e: any) { setError(e.message); }
  }
  async function retryTask(taskId: number) {
    try { await api.tasks.retry(taskId); loadAll(); } catch (e: any) { setError(e.message); }
  }

  function startEdit() {
    if (!project) return;
    setEditName(project.name);
    setEditDesc(project.description || "");
    setEditing(true);
  }

  async function handleSave() {
    if (!editName.trim()) return;
    try {
      const updated = await api.projects.update(projectId, {
        name: editName.trim(),
        description: editDesc.trim() || undefined,
      });
      setProject(updated);
      setEditing(false);
    } catch (e: any) { setError(e.message); }
  }

  if (loading) return <div className="loading">LOADING</div>;
  if (!project) return <div className="empty-state"><h3>Not Found</h3><p>Project #{projectId} does not exist.</p></div>;

  const doneCount = tasks.filter(t => t.status === S.COMPLETED || t.status === S.PLAN_READY).length;
  const failedCount = tasks.filter(t => t.status === S.FAILED).length;

  return (
    <>
      <div className="page-header">
        {editing ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 8, maxWidth: 480 }}>
            <input
              className="form-input"
              value={editName}
              onChange={e => setEditName(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSave()}
              onKeyUp={e => e.key === "Escape" && setEditing(false)}
              autoFocus
            />
            <input
              className="form-input"
              value={editDesc}
              onChange={e => setEditDesc(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSave()}
              onKeyUp={e => e.key === "Escape" && setEditing(false)}
              placeholder="Description (optional)"
            />
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn btn-primary btn-sm" onClick={handleSave}>SAVE</button>
              <button className="btn btn-sm" onClick={() => setEditing(false)}>CANCEL</button>
            </div>
          </div>
        ) : (
          <>
            <h1>{project.name}</h1>
            <p>{project.description || "No description"} &middot; <button className="btn btn-sm" onClick={startEdit} style={{ marginLeft: 8 }}>EDIT</button></p>
          </>
        )}
      </div>

      <div className="page-content">
        {error && <ErrorBanner message={`Error: ${error}`} />}

        {/* Stat cards */}
        <div className="grid-3" style={{ marginBottom: 36 }}>
          <div className="stat-card">
            <span className="stat-label">Total Tasks</span>
            <span className="stat-value">{tasks.length}</span>
            <span className="stat-sub">all statuses</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Done</span>
            <span className="stat-value">{doneCount}</span>
            <span className="stat-sub">completed</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Failed</span>
            <span className="stat-value">{failedCount}</span>
            <span className="stat-sub">needs review</span>
          </div>
        </div>

        {/* Toolbar */}
        <div className="toolbar">
          <div />
          <div style={{ display: "flex", gap: 12 }}>
            <Link to={`/projects/${projectId}/workflows/new`}>
              <button className="btn">+ NEW WORKFLOW</button>
            </Link>
            <Link to={`/projects/${projectId}/tasks/new`}>
              <button className="btn btn-primary">+ NEW TASK</button>
            </Link>
          </div>
        </div>

        {/* Tasks */}
        <h2 className="section-title">Tasks <span>({tasks.length})</span></h2>
        {tasks.length === 0 ? (
          <div className="empty-state">
            <h3>No Tasks</h3>
            <p>Create a task to start orchestrating agents.</p>
          </div>
        ) : (
          <div className="table-wrapper" style={{ marginBottom: 40 }}>
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Title</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th style={{ width: 1 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((t) => (
                  <tr key={t.id}>
                    <td>#{t.id}</td>
                    <td>{t.title}</td>
                    <td style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-secondary)" }}>
                      {t.task_type}
                    </td>
                    <td><span className={`badge badge-${t.status}`}>{t.status}</span></td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      <Link to={`/tasks/${t.id}/trace`} className="link">TRACE</Link>
                      {(t.status === S.RUNNING || t.status === S.QUEUED) && (
                        <button className="btn btn-sm" style={{ marginLeft: 8 }}
                          onClick={() => cancelTask(t.id)}>CANCEL</button>
                      )}
                      {(t.status === S.FAILED || t.status === S.CANCELLED) && (
                        <button className="btn btn-sm" style={{ marginLeft: 8 }}
                          onClick={() => retryTask(t.id)}>RETRY</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Workflows */}
        <h2 className="section-title">Workflows <span>({workflows.length})</span></h2>
        {workflows.length === 0 ? (
          <div className="empty-state" style={{ marginBottom: 40 }}>
            <h3>No Workflows</h3>
            <p>Define a workflow to structure agent collaboration.</p>
          </div>
        ) : (
          <div className="grid-2" style={{ marginBottom: 40 }}>
            {workflows.map((w) => (
              <Link to={`/projects/${projectId}/workflows/${w.workflow.id}`} key={w.workflow.id}>
                <div className="card-interactive">
                  <strong style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    {w.workflow.name}
                  </strong>
                  <p style={{ fontSize: 10, color: "var(--text-secondary)", textTransform: "uppercase", marginTop: 6, fontWeight: 500 }}>
                    {w.workflow.task_type} &middot; {w.nodes.length} NODES
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* Issues */}
        <h2 className="section-title">Known Issues <span>({issues.length})</span></h2>
        {issues.length === 0 ? (
          <div className="empty-state">
            <h3>No Known Issues</h3>
            <p>The system has not recorded any recurring issues for this project.</p>
          </div>
        ) : (
          <div className="grid-2">
            {issues.map((i) => (
              <div key={i.id} className="card">
                <strong style={{ fontSize: 11, fontWeight: 900, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                  {i.error_pattern}
                </strong>
                <p style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 8, fontWeight: 400 }}>
                  {i.root_cause}
                </p>
                {i.rule_update && (
                  <p style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 6, fontStyle: "italic" }}>
                    Rule: {i.rule_update}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
