import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api";

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const [project, setProject] = useState<any>(null);
  const [tasks, setTasks] = useState<any[]>([]);
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [issues, setIssues] = useState<any[]>([]);

  useEffect(() => {
    api.projects.get(projectId).then(setProject);
    api.tasks.listByProject(projectId).then(setTasks);
    api.workflows.listByProject(projectId).then(setWorkflows);
    api.issues.listByProject(projectId).then(setIssues);
  }, [projectId]);

  if (!project) return <div>Loading...</div>;

  return (
    <div>
      <Link to="/">&larr; Back</Link>
      <h1>{project.name}</h1>
      <p>{project.description}</p>

      <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
        <Link to={`/projects/${projectId}/workflows/new`}><button>+ New Workflow</button></Link>
        <Link to={`/projects/${projectId}/tasks/new`}><button>+ New Task</button></Link>
      </div>

      <h2 style={{ marginTop: 32 }}>Tasks ({tasks.length})</h2>
      <table width="100%" style={{ borderCollapse: "collapse" }}>
        <thead><tr style={{ textAlign: "left", borderBottom: "2px solid #ddd" }}><th>ID</th><th>Title</th><th>Type</th><th>Status</th><th>Actions</th></tr></thead>
        <tbody>
          {tasks.map((t: any) => (
            <tr key={t.id} style={{ borderBottom: "1px solid #eee" }}>
              <td>{t.id}</td>
              <td>{t.title}</td>
              <td>{t.task_type}</td>
              <td>{t.status}</td>
              <td><Link to={`/tasks/${t.id}/trace`}>View Trace</Link></td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Workflows ({workflows.length})</h2>
      {workflows.map((w: any) => (
        <div key={w.workflow.id} style={{ border: "1px solid #ddd", padding: 12, marginBottom: 8, borderRadius: 4 }}>
          <strong>{w.workflow.name}</strong> ({w.workflow.task_type}) — {w.nodes.length} nodes
        </div>
      ))}

      <h2>Known Issues ({issues.length})</h2>
      {issues.map((i: any) => (
        <div key={i.id} style={{ border: "1px solid #ddd", padding: 12, marginBottom: 8, borderRadius: 4 }}>
          <strong>{i.error_pattern}</strong>: {i.root_cause}
        </div>
      ))}
    </div>
  );
}
