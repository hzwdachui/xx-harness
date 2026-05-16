import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api } from "../api";

export function WorkflowEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const projectId = Number(id);
  const [agents, setAgents] = useState<any[]>([]);
  const [name, setName] = useState("");
  const [taskType, setTaskType] = useState("development");
  const [nodes, setNodes] = useState<{ agent_name: string; depends_on: number[]; review_gate: boolean; skill: string }[]>([{ agent_name: "researcher", depends_on: [], review_gate: false, skill: "" }]);

  useEffect(() => { api.agents.list().then(setAgents); }, []);

  function addNode() { setNodes([...nodes, { agent_name: "executor", depends_on: [], review_gate: false, skill: "" }]); }

  async function handleSave() {
    await api.workflows.create({ name, task_type: taskType, project_id: projectId, nodes });
    navigate(`/projects/${projectId}`);
  }

  const agentNames = agents.map(a => a.name);

  return (
    <div>
      <h1>New Workflow</h1>
      <Link to={`/projects/${projectId}`}>&larr; Back</Link>
      <div style={{ marginTop: 16 }}>
        <label>Name: <input value={name} onChange={e => setName(e.target.value)} /></label>
        <label style={{ marginLeft: 16 }}>Type:
          <select value={taskType} onChange={e => setTaskType(e.target.value)}>
            <option value="development">development</option>
            <option value="exploration">exploration</option>
            <option value="testing">testing</option>
            <option value="deployment">deployment</option>
            <option value="custom">custom</option>
          </select>
        </label>
      </div>
      <h2 style={{ marginTop: 24 }}>Nodes ({nodes.length})</h2>
      {nodes.map((n, i) => (
        <div key={i} style={{ border: "1px solid #ddd", padding: 12, marginBottom: 8, borderRadius: 4 }}>
          <strong>Node {i + 1}</strong>
          <div>Agent: <select value={n.agent_name} onChange={e => { const next = [...nodes]; next[i] = { ...next[i], agent_name: e.target.value }; setNodes(next); }}>{agentNames.map(a => <option key={a} value={a}>{a}</option>)}</select></div>
          <div>Depends on (comma-separated indices): <input value={n.depends_on.join(",")} onChange={e => { const next = [...nodes]; next[i] = { ...next[i], depends_on: e.target.value.split(",").map(Number).filter(x => x > 0) }; setNodes(next); }} /></div>
          <div>Skill: <input value={n.skill} onChange={e => { const next = [...nodes]; next[i] = { ...next[i], skill: e.target.value }; setNodes(next); }} placeholder="e.g. superpowers:brainstorming" /></div>
          <label><input type="checkbox" checked={n.review_gate} onChange={e => { const next = [...nodes]; next[i] = { ...next[i], review_gate: e.target.checked }; setNodes(next); }} /> Review Gate</label>
        </div>
      ))}
      <button onClick={addNode} style={{ marginRight: 8 }}>+ Add Node</button>
      <button onClick={handleSave}>Save</button>
    </div>
  );
}
