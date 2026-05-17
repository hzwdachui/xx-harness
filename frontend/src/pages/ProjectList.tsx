import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { Project } from "../api";
import { ConfirmModal } from "../components/ConfirmModal";
import { ErrorBanner } from "../components/ErrorBanner";

export function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);

  function loadProjects() {
    setLoading(true);
    setError(null);
    api.projects.list()
      .then(setProjects)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => { loadProjects(); }, []);

  async function handleCreate() {
    if (!name.trim()) return;
    try {
      await api.projects.create({ name: name.trim(), description: description.trim() || undefined });
      setName(""); setDescription("");
      setShowForm(false);
      loadProjects();
    } catch (e: any) { setError(e.message); }
  }

  async function handleDelete() {
    if (confirmDeleteId == null) return;
    try {
      await api.projects.delete(confirmDeleteId);
      setConfirmDeleteId(null);
      loadProjects();
    } catch (e: any) { setError(e.message); }
  }

  return (
    <>
      <div className="page-header">
        <h1>Projects</h1>
        <p>Manage AI agent orchestration projects. Each project owns its workflows, tasks, and learned constraints.</p>
      </div>

      <div className="page-content">
        <div className="toolbar">
          <div />
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? "CANCEL" : "+ NEW PROJECT"}
          </button>
        </div>

        {showForm && (
          <div className="inline-form">
            <input
              className="form-input"
              placeholder="Project name"
              value={name}
              onChange={e => setName(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleCreate()}
              autoFocus
            />
            <input
              className="form-input"
              placeholder="Description (optional)"
              value={description}
              onChange={e => setDescription(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleCreate()}
            />
            <button className="btn btn-primary" onClick={handleCreate}>CREATE</button>
          </div>
        )}

        {error && <ErrorBanner message={`Error: ${error}`} />}

        {loading ? (
          <div className="loading">LOADING</div>
        ) : projects.length === 0 ? (
          <div className="empty-state">
            <h3>No Projects</h3>
            <p>Create your first project to start orchestrating AI agents.</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Description</th>
                  <th style={{ width: 1 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((p) => (
                  <tr key={p.id}>
                    <td>#{p.id}</td>
                    <td><Link to={`/projects/${p.id}`} className="link">{p.name}</Link></td>
                    <td style={{ color: "var(--text-secondary)" }}>{p.description || "—"}</td>
                    <td style={{ display: "flex", gap: 8, whiteSpace: "nowrap" }}>
                      <Link to={`/projects/${p.id}/tasks/new`}>
                        <button className="btn btn-sm">NEW TASK</button>
                      </Link>
                      <button className="btn btn-sm btn-danger" onClick={() => setConfirmDeleteId(p.id)}>DEL</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <ConfirmModal
        open={confirmDeleteId != null}
        title="DELETE PROJECT"
        message={`Permanently delete project #${confirmDeleteId}? This action cannot be undone.`}
        onConfirm={handleDelete}
        onCancel={() => setConfirmDeleteId(null)}
        confirmLabel="DELETE"
        danger
      />
    </>
  );
}
