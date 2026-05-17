import { useCallback, useEffect, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  useNodesState, useEdgesState, addEdge,
  type Node, type Edge, type Connection,
} from "@xyflow/react";
import { api } from "../api";
import type { Agent, WorkflowItem } from "../api";
import {
  WorkflowDAG, getNodeData, workflowToGraph, graphToWorkflow, findOrphanNodes,
} from "../components/WorkflowDAG";
import { ErrorBanner } from "../components/ErrorBanner";

export function WorkflowEditor() {
  const { id, workflowId } = useParams<{ id: string; workflowId?: string }>();
  const navigate = useNavigate();
  const projectId = Number(id);
  const isEdit = Boolean(workflowId);
  const wfId = isEdit ? Number(workflowId) : null;

  const [agents, setAgents] = useState<Agent[]>([]);
  const [name, setName] = useState("");
  const [taskType, setTaskType] = useState("development");
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [loading, setLoading] = useState(isEdit);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    api.agents.list().then(setAgents).catch(e => setError(e.message));
  }, []);

  // Load existing workflow in edit mode
  useEffect(() => {
    if (!isEdit || !wfId || agents.length === 0) return;
    setLoading(true);
    api.workflows.listByProject(projectId)
      .then(list => {
        const wf = list.find(w => w.workflow.id === wfId);
        if (!wf) { setError(`Workflow #${wfId} not found`); return; }
        setName(wf.workflow.name);
        setTaskType(wf.workflow.task_type);
        const agentMap = new Map(agents.map(a => [a.id, a.name]));
        const graph = workflowToGraph(wf.nodes, agentMap);
        setNodes(graph.nodes);
        setEdges(graph.edges);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [isEdit, wfId, projectId, agents.length]);

  const orphanNodeIds = useMemo(() => findOrphanNodes(nodes, edges), [nodes, edges]);

  const selectedForm = useMemo(() => {
    if (!selectedNode) return null;
    const n = nodes.find(n => n.id === selectedNode);
    if (!n) return null;
    const d = getNodeData(n);
    return { id: n.id, agent_name: d.agent_name || "", skill: d.skill || "", review_gate: d.reviewGate || false };
  }, [nodes, selectedNode]);

  const onConnect = useCallback(
    (conn: Connection) => setEdges(eds => addEdge({ ...conn, animated: false }, eds)),
    [setEdges],
  );

  function addNode() {
    const idx = nodes.length;
    const newNode: Node = {
      id: `node-new-${Date.now()}`,
      type: "agentNode",
      position: { x: 100 + (idx % 3) * 280, y: 50 + Math.floor(idx / 3) * 160 },
      data: { label: `Node ${idx}`, agent_name: "", skill: "", reviewGate: false },
    };
    setNodes(nds => [...nds, newNode]);
    setSelectedNode(newNode.id);
  }

  function deleteSelected() {
    if (!selectedNode) return;
    setNodes(nds => nds.filter(n => n.id !== selectedNode));
    setEdges(eds => eds.filter(e => e.source !== selectedNode && e.target !== selectedNode));
    setSelectedNode(null);
  }

  function updateNodeData(nodeId: string, patch: Record<string, unknown>) {
    setNodes(nds =>
      nds.map(n => {
        if (n.id !== nodeId) return n;
        const newData = { ...n.data, ...patch };
        if ("agent_name" in patch) {
          newData.label = patch.agent_name as string || `Node ${nds.indexOf(n)}`;
        }
        return { ...n, data: newData };
      }),
    );
  }

  function onNodeClick(_: React.MouseEvent, node: Node) { setSelectedNode(node.id); }
  function onPaneClick() { setSelectedNode(null); }

  async function handleSave() {
    if (!name.trim()) { setError("Workflow name is required."); return; }
    if (nodes.length === 0) { setError("At least one node is required."); return; }

    // Detect orphan nodes — nodes disconnected from the main graph
    const orphans = findOrphanNodes(nodes, edges);
    if (orphans.size > 0) {
      const labels = Array.from(orphans)
        .map(id => {
          const n = nodes.find(nd => nd.id === id);
          return n ? (getNodeData(n).label || id) : id;
        })
        .join(", ");
      setError(`Orphan node(s) detected: ${labels}. All nodes must be connected in a single workflow DAG.`);
      return;
    }

    const wfNodes = graphToWorkflow(nodes, edges);
    const payload = { name: name.trim(), task_type: taskType, project_id: projectId, nodes: wfNodes };

    try {
      if (isEdit && wfId) {
        await api.workflows.update(wfId, payload);
      } else {
        await api.workflows.create(payload);
      }
      navigate(`/projects/${projectId}`);
    } catch (e: any) { setError(e.message); }
  }

  const agentNames = agents.map(a => a.name);

  if (loading) return <div className="loading">LOADING WORKFLOW</div>;

  return (
    <>
      <div className="page-header">
        <h1>{isEdit ? "EDIT WORKFLOW" : "NEW WORKFLOW"}</h1>
        <p>{isEdit ? name : "Drag nodes, connect them to define dependencies. Click a node to edit its agent and settings."}</p>
      </div>

      <div className="page-content" style={{ padding: "16px 24px 48px", flex: 1, display: "flex", flexDirection: "column" }}>
        {error && (
          <ErrorBanner message={error} />
        )}

        <div style={{ display: "flex", gap: 12, marginBottom: 16, alignItems: "center", flexWrap: "wrap" }}>
          <input className="form-input" placeholder="Workflow name" value={name}
            onChange={e => setName(e.target.value)} style={{ maxWidth: 240 }} />
          <select className="form-input" value={taskType} onChange={e => setTaskType(e.target.value)} style={{ maxWidth: 180 }}>
            <option value="development">Development</option>
            <option value="exploration">Exploration</option>
            <option value="testing">Testing</option>
            <option value="deployment">Deployment</option>
            <option value="custom">Custom</option>
          </select>
          <div style={{ flex: 1 }} />
          <button className="btn btn-sm" onClick={addNode}>+ ADD NODE</button>
          {selectedNode && <button className="btn btn-sm btn-danger" onClick={deleteSelected}>DELETE NODE</button>}
          <button className="btn btn-primary btn-sm" onClick={handleSave}>
            {isEdit ? "UPDATE" : "SAVE"}
          </button>
        </div>

        <div style={{ display: "flex", gap: 16, flex: 1, minHeight: 500 }}>
          <div style={{ flex: 1, border: "1px solid var(--border)", borderRadius: 6, background: "var(--bg)", overflow: "hidden" }}>
            <WorkflowDAG
              nodes={nodes} edges={edges}
              orphanNodeIds={orphanNodeIds}
              onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
              onConnect={onConnect} onNodeClick={onNodeClick} onPaneClick={onPaneClick}
            />
          </div>

          {selectedForm && (
            <div className="card" style={{ width: 260, flexShrink: 0, overflowY: "auto" }}>
              <div className="card-header"><h3>EDIT NODE</h3></div>
              <div className="form-group">
                <label className="form-label">Agent</label>
                <select className="form-input" value={selectedForm.agent_name}
                  onChange={e => updateNodeData(selectedForm.id, { agent_name: e.target.value })}>
                  <option value="">(select)</option>
                  {agentNames.map(a => <option key={a} value={a}>{a}</option>)}
                </select>
              </div>
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-checkbox">
                  <input type="checkbox" checked={selectedForm.review_gate}
                    onChange={e => updateNodeData(selectedForm.id, { reviewGate: e.target.checked })} />
                  REVIEW GATE
                </label>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
