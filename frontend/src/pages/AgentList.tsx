import { useEffect, useState } from "react";
import { api } from "../api";
import type { Agent } from "../api";
import { ConfirmModal } from "../components/ConfirmModal";
import { ErrorBanner } from "../components/ErrorBanner";

const ROLES = ["researcher", "planner", "executor", "reviewer", "tester"];

function emptyForm() {
  return { name: "", role: "executor", system_prompt: "", skills: "" };
}

export function AgentList() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm());
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState(emptyForm());
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);

  function load() {
    setLoading(true);
    setError(null);
    api.agents.list()
      .then(setAgents)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  async function handleCreate() {
    if (!form.name.trim()) return;
    try {
      await api.agents.create({
        name: form.name.trim(),
        role: form.role,
        system_prompt: form.system_prompt.trim(),
        skills: form.skills.trim() || "",
      });
      setForm(emptyForm());
      setShowForm(false);
      load();
    } catch (e: any) { setError(e.message); }
  }

  function startEdit(a: Agent) {
    setEditingId(a.id);
    setEditForm({
      name: a.name,
      role: a.role,
      system_prompt: a.system_prompt,
      skills: a.skills,
    });
  }

  async function handleUpdate() {
    if (editingId == null || !editForm.name.trim()) return;
    try {
      await api.agents.update(editingId, {
        name: editForm.name.trim(),
        role: editForm.role,
        system_prompt: editForm.system_prompt.trim(),
        skills: editForm.skills.trim() || "",
      });
      setEditingId(null);
      load();
    } catch (e: any) { setError(e.message); }
  }

  async function handleDelete() {
    if (confirmDeleteId == null) return;
    try {
      await api.agents.delete(confirmDeleteId);
      setConfirmDeleteId(null);
      load();
    } catch (e: any) { setError(e.message); }
  }

  return (
    <>
      <div className="page-header">
        <h1>AGENTS</h1>
        <p>Registered AI agents available for workflow orchestration. Each agent has a name, role, system prompt, and optional tool set.</p>
      </div>

      <div className="page-content">
        {error && (
          <ErrorBanner message={`Error: ${error}`} />
        )}

        <div className="toolbar">
          <div />
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? "CANCEL" : "+ NEW AGENT"}
          </button>
        </div>

        {showForm && (
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-header"><h3>NEW AGENT</h3></div>
            <AgentForm
              form={form}
              onChange={setForm}
              onSave={handleCreate}
              saveLabel="CREATE"
            />
          </div>
        )}

        {loading ? (
          <div className="loading">LOADING</div>
        ) : agents.length === 0 ? (
          <div className="empty-state">
            <h3>NO AGENTS</h3>
            <p>Register agents to make them available in workflow definitions.</p>
          </div>
        ) : (
          <div className="grid-2">
            {agents.map((a) => (
              <div key={a.id} className="card">
                {editingId === a.id ? (
                  <>
                    <div className="card-header"><h3>EDIT AGENT</h3></div>
                    <AgentForm
                      form={editForm}
                      onChange={setEditForm}
                      onSave={handleUpdate}
                      saveLabel="SAVE"
                    />
                    <div style={{ marginTop: 12 }}>
                      <button className="btn btn-sm" onClick={() => setEditingId(null)}>CANCEL</button>
                    </div>
                  </>
                ) : (
                  <>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <div style={{
                          width: 32, height: 32,
                          background: "var(--accent)", color: "var(--accent-text)",
                          display: "flex", alignItems: "center", justifyContent: "center",
                          fontWeight: 700, fontSize: 14,
                        }}>
                          {a.name[0].toUpperCase()}
                        </div>
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 600 }}>{a.name}</div>
                          <div style={{ fontSize: 10, color: "var(--accent)", textTransform: "uppercase", fontWeight: 500, letterSpacing: "0.08em" }}>
                            {a.role}
                          </div>
                        </div>
                      </div>
                      <div style={{ display: "flex", gap: 6 }}>
                        <button className="btn btn-sm" onClick={() => startEdit(a)}>EDIT</button>
                        <button className="btn btn-sm btn-danger" onClick={() => setConfirmDeleteId(a.id)}>DEL</button>
                      </div>
                    </div>
                    <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.5 }}>
                      {a.system_prompt}
                    </p>
                    {a.skills && (
                      <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 8, fontStyle: "italic", lineHeight: 1.4 }}>
                        {a.skills}
                      </p>
                    )}
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <ConfirmModal
        open={confirmDeleteId != null}
        title="DELETE AGENT"
        message={`Permanently delete this agent? Workflows referencing it will not be affected.`}
        onConfirm={handleDelete}
        onCancel={() => setConfirmDeleteId(null)}
        confirmLabel="DELETE"
        danger
      />
    </>
  );
}

/* ── Shared form fragment ── */
function AgentForm({
  form, onChange, onSave, saveLabel,
}: {
  form: { name: string; role: string; system_prompt: string; skills: string };
  onChange: (f: typeof form) => void;
  onSave: () => void;
  saveLabel: string;
}) {
  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label">Name *</label>
          <input
            className="form-input"
            value={form.name}
            onChange={e => onChange({ ...form, name: e.target.value })}
            onKeyDown={e => e.key === "Enter" && onSave()}
            placeholder="e.g. researcher"
            autoFocus
          />
        </div>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label">Role</label>
          <select className="form-input" value={form.role} onChange={e => onChange({ ...form, role: e.target.value })}>
            {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">System Prompt</label>
        <textarea
          className="form-input"
          rows={3}
          value={form.system_prompt}
          onChange={e => onChange({ ...form, system_prompt: e.target.value })}
          placeholder="Instructions for the agent..."
        />
      </div>
      <div className="form-group" style={{ marginBottom: 0 }}>
        <label className="form-label">Skills</label>
        <textarea
          className="form-input"
          rows={3}
          value={form.skills}
          onChange={e => onChange({ ...form, skills: e.target.value })}
          placeholder="Natural language description of tools and skills this agent needs, e.g. read-only access to files, git operations, search..."
        />
      </div>
      <div style={{ marginTop: 16 }}>
        <button className="btn btn-primary btn-sm" onClick={onSave}>{saveLabel}</button>
      </div>
    </div>
  );
}
