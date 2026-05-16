import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";

export function ProjectList() {
  const [projects, setProjects] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  useEffect(() => { api.projects.list().then(setProjects); }, []);

  async function handleCreate() {
    await api.projects.create({ name, description });
    setName(""); setDescription("");
    setShowForm(false);
    api.projects.list().then(setProjects);
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this project?")) return;
    await api.projects.delete(id);
    api.projects.list().then(setProjects);
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Projects</h1>
        <button onClick={() => setShowForm(!showForm)}>+ New Project</button>
      </div>
      {showForm && (
        <div style={{ border: "1px solid #ccc", padding: 16, marginBottom: 16, borderRadius: 4 }}>
          <input placeholder="Project name" value={name} onChange={e => setName(e.target.value)} />
          <input placeholder="Description" value={description} onChange={e => setDescription(e.target.value)} style={{ marginLeft: 8 }} />
          <button onClick={handleCreate} style={{ marginLeft: 8 }}>Create</button>
        </div>
      )}
      <table width="100%" style={{ borderCollapse: "collapse" }}>
        <thead><tr style={{ textAlign: "left", borderBottom: "2px solid #ddd" }}><th>ID</th><th>Name</th><th>Description</th><th>Actions</th></tr></thead>
        <tbody>
          {projects.map((p: any) => (
            <tr key={p.id} style={{ borderBottom: "1px solid #eee" }}>
              <td>{p.id}</td>
              <td><Link to={`/projects/${p.id}`}>{p.name}</Link></td>
              <td>{p.description}</td>
              <td>
                <Link to={`/projects/${p.id}/tasks/new`}><button style={{ marginRight: 8 }}>New Task</button></Link>
                <button onClick={() => handleDelete(p.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
