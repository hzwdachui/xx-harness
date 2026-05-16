import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api } from "../api";

export function TaskCreate() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const projectId = Number(id);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [title, setTitle] = useState("");
  const [taskType, setTaskType] = useState("development");
  const [description, setDescription] = useState("");
  const [workflowId, setWorkflowId] = useState<number | null>(null);

  useEffect(() => { api.workflows.listByProject(projectId).then(setWorkflows); }, [projectId]);

  async function handleCreate() {
    const res = await api.tasks.create({
      project_id: projectId, title, task_type: taskType,
      description, workflow_id: workflowId || null,
    });
    if (confirm("Task created. Start now?")) {
      await api.tasks.start(res.id);
      navigate(`/tasks/${res.id}/trace`);
    } else {
      navigate(`/projects/${projectId}`);
    }
  }

  const matchingWorkflows = workflows.filter((w: any) => w.workflow.task_type === taskType);

  return (
    <div>
      <h1>New Task</h1>
      <Link to={`/projects/${projectId}`}>&larr; Back</Link>
      <div style={{ marginTop: 16 }}>
        <label>Title: <input value={title} onChange={e => setTitle(e.target.value)} /></label>
      </div>
      <div style={{ marginTop: 8 }}>
        <label>Type:
          <select value={taskType} onChange={e => { setTaskType(e.target.value); setWorkflowId(null); }}>
            <option value="development">Development</option>
            <option value="exploration">Exploration</option>
            <option value="testing">Testing</option>
          </select>
        </label>
      </div>
      <div style={{ marginTop: 8 }}>
        <label>Workflow:
          <select value={workflowId ?? ""} onChange={e => setWorkflowId(e.target.value ? Number(e.target.value) : null)}>
            <option value="">Auto</option>
            {matchingWorkflows.map((w: any) => (<option key={w.workflow.id} value={w.workflow.id}>{w.workflow.name}</option>))}
          </select>
        </label>
      </div>
      <div style={{ marginTop: 8 }}>
        <label>Description:<br /><textarea rows={4} style={{ width: "100%", maxWidth: 500 }} value={description} onChange={e => setDescription(e.target.value)} /></label>
      </div>
      <button onClick={handleCreate} style={{ marginTop: 16 }}>Create & Start</button>
    </div>
  );
}
