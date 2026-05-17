import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api";
import type { WorkflowItem } from "../api";
import { ConfirmModal } from "../components/ConfirmModal";
import { ErrorBanner } from "../components/ErrorBanner";

export function TaskCreate() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const projectId = Number(id);
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([]);
  const [title, setTitle] = useState("");
  const [taskType, setTaskType] = useState("development");
  const [description, setDescription] = useState("");
  const [workflowId, setWorkflowId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showStartModal, setShowStartModal] = useState(false);
  const [createdTaskId, setCreatedTaskId] = useState<number | null>(null);
  const [titleError, setTitleError] = useState(false);

  useEffect(() => {
    api.workflows.listByProject(projectId).then(setWorkflows).catch(e => setError(e.message));
  }, [projectId]);

  async function handleCreate() {
    if (!title.trim()) { setTitleError(true); return; }
    setTitleError(false);
    try {
      const res = await api.tasks.create({
        project_id: projectId,
        title: title.trim(),
        task_type: taskType,
        description: description.trim(),
        workflow_id: workflowId || null,
      });
      setCreatedTaskId(res.id);
      setShowStartModal(true);
    } catch (e: any) { setError(e.message); }
  }

  async function handleStart() {
    if (createdTaskId == null) return;
    try {
      await api.tasks.start(createdTaskId);
      navigate(`/tasks/${createdTaskId}/trace`);
    } catch (e: any) { setError(e.message); }
  }

  const matchingWorkflows = workflows.filter((w: any) => w.workflow.task_type === taskType);

  return (
    <>
      <div className="page-header">
        <h1>New Task</h1>
        <p>Create and optionally start an orchestrated agent task.</p>
      </div>

      <div className="page-content">
        {error && <ErrorBanner message={error} />}

        <div className="card">
          <div className="form-group">
            <label className="form-label">Title *</label>
            <input
              className="form-input"
              placeholder="e.g. Fix authentication bug in login flow"
              value={title}
              onChange={e => { setTitle(e.target.value); setTitleError(false); }}
              autoFocus
              style={titleError ? { borderColor: "var(--error)" } : undefined}
            />
            {titleError && <p className="form-hint" style={{ color: "var(--error)" }}>Title is required.</p>}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
            <div className="form-group">
              <label className="form-label">Type</label>
              <select className="form-input" value={taskType} onChange={e => { setTaskType(e.target.value); setWorkflowId(null); }}>
                <option value="development">Development</option>
                <option value="exploration">Exploration</option>
                <option value="testing">Testing</option>
                <option value="deployment">Deployment</option>
                <option value="custom">Custom</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Workflow</label>
              <select className="form-input" value={workflowId ?? ""} onChange={e => setWorkflowId(e.target.value ? Number(e.target.value) : null)}>
                <option value="">Auto (default)</option>
                {matchingWorkflows.map((w: any) => (
                  <option key={w.workflow.id} value={w.workflow.id}>{w.workflow.name}</option>
                ))}
              </select>
              <p className="form-hint">Leave on Auto to use the default workflow for this task type.</p>
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Description</label>
            <textarea
              className="form-input"
              rows={4}
              placeholder="Describe what this task should accomplish..."
              value={description}
              onChange={e => setDescription(e.target.value)}
            />
          </div>
        </div>

        <div style={{ marginTop: 24 }}>
          <button className="btn btn-primary" onClick={handleCreate}>
            CREATE TASK
          </button>
        </div>
      </div>

      <ConfirmModal
        open={showStartModal}
        title="START TASK?"
        message="Task created successfully. Start executing the workflow now?"
        onConfirm={handleStart}
        onCancel={() => setShowStartModal(false)}
        confirmLabel="START"
        cancelLabel="CANCEL"
      />
    </>
  );
}
