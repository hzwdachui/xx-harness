import { useEffect, useState, useMemo } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import type { WorkflowItem, Agent } from "../api";
import { ErrorBanner } from "../components/ErrorBanner";
import { WorkflowDAG, workflowToGraph } from "../components/WorkflowDAG";

export function WorkflowDetail() {
  const { id, workflowId } = useParams<{ id: string; workflowId: string }>();
  const navigate = useNavigate();
  const projectId = Number(id);
  const wfId = Number(workflowId);
  const [wf, setWf] = useState<WorkflowItem | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.workflows.listByProject(projectId).then(list => {
        const found = list.find(w => w.workflow.id === wfId);
        if (found) setWf(found);
        else setError(`Workflow #${wfId} not found`);
      }),
      api.agents.list().then(setAgents),
    ]).catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [projectId, wfId]);

  const graph = useMemo(() => {
    if (!wf) return { nodes: [], edges: [] };
    const agentMap = new Map(agents.map(a => [a.id, a.name]));
    return workflowToGraph(wf.nodes, agentMap);
  }, [wf, agents]);

  if (loading) return <div className="loading">LOADING</div>;
  if (error) return (
    <>
      <div className="page-header"><h1>Workflow</h1></div>
      <div className="page-content">
        <ErrorBanner message={`Error: ${error}`} />
      </div>
    </>
  );
  if (!wf) return null;

  return (
    <>
      <div className="page-header">
        <h1>{wf.workflow.name}</h1>
        <p>
          <Link to={`/projects/${projectId}`} className="link">Project #{projectId}</Link>
          {" "}&middot; {wf.workflow.task_type} &middot; {wf.nodes.length} NODES
          {" "}&middot;{" "}
          <button className="btn btn-sm" onClick={() => navigate(`/projects/${projectId}/workflows/${wfId}/edit`)}>EDIT</button>
        </p>
      </div>

      <div className="page-content" style={{ padding: "16px 24px 48px", flex: 1, display: "flex", flexDirection: "column" }}>
        <div style={{ flex: 1, minHeight: 500, border: "1px solid var(--border)", borderRadius: 6, background: "var(--bg)", overflow: "hidden" }}>
          <WorkflowDAG
            nodes={graph.nodes}
            edges={graph.edges}
            readOnly
          />
        </div>
      </div>
    </>
  );
}
