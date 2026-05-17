import { useCallback } from "react";
import {
  ReactFlow, Controls, Background, MiniMap,
  type Node, type Edge, type Connection,
  Handle, Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

/* ── AgentNode data ── */

export interface AgentNodeData {
  label: string;
  agent_name: string;
  skill: string;
  reviewGate: boolean;
  [key: string]: unknown;
}

/* ── Orphan detection ── */

/** Find nodes that are disconnected from the main graph component.
 *  Uses weakly-connected-components (ignores edge direction).
 *  When there are >1 nodes, any node not in the largest component is an orphan.
 *  Nodes with literally zero edges are always orphans (unless it's the only node). */
export function findOrphanNodes(nodes: Node[], edges: Edge[]): Set<string> {
  if (nodes.length <= 1) return new Set();

  // Build adjacency (undirected — weakly connected)
  const adj = new Map<string, Set<string>>();
  for (const n of nodes) adj.set(n.id, new Set());
  for (const e of edges) {
    const s = adj.get(e.source);
    const t = adj.get(e.target);
    if (s && t) {
      s.add(e.target);
      t.add(e.source);
    }
  }

  // Find connected components via BFS
  const visited = new Set<string>();
  const components: string[][] = [];

  for (const n of nodes) {
    if (visited.has(n.id)) continue;
    const comp: string[] = [];
    const queue = [n.id];
    visited.add(n.id);
    while (queue.length > 0) {
      const cur = queue.shift()!;
      comp.push(cur);
      for (const neighbor of adj.get(cur) || []) {
        if (!visited.has(neighbor)) {
          visited.add(neighbor);
          queue.push(neighbor);
        }
      }
    }
    components.push(comp);
  }

  // If only one component, no orphans
  if (components.length <= 1) return new Set();

  // Nodes not in the largest component are orphans
  const largest = components.reduce((a, b) => (a.length >= b.length ? a : b));
  const largestSet = new Set(largest);
  return new Set(nodes.filter(n => !largestSet.has(n.id)).map(n => n.id));
}

/* ── Custom node component ── */

function AgentNode({ data, selected }: { data: AgentNodeData; selected: boolean }) {
  const isOrphan = data.isOrphan === true;
  const orphanStyle = isOrphan ? {
    border: "2px dashed var(--warning)",
    background: "var(--warning-bg, #fff3cd)",
  } : {};

  return (
    <div style={{
      padding: "10px 16px",
      border: selected ? "2px solid var(--accent)" : "1px solid var(--border)",
      borderRadius: 6,
      background: "var(--card-bg)",
      boxShadow: "var(--shadow)",
      minWidth: 170,
      fontSize: 11,
      ...orphanStyle,
    }}>
      <Handle type="target" position={Position.Top} />
      <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 2 }}>
        {data.label}
      </div>
      <div style={{ fontSize: 10, color: "var(--accent)", fontWeight: 600, textTransform: "uppercase" }}>
        {data.agent_name || "(no agent)"}
      </div>
      {data.skill && (
        <div style={{ fontSize: 9, color: "var(--text-muted)", fontFamily: "var(--font-mono)", marginTop: 2 }}>
          {data.skill}
        </div>
      )}
      {data.reviewGate && (
        <div style={{ fontSize: 9, fontWeight: 700, color: "var(--warning)", textTransform: "uppercase", marginTop: 4 }}>
          REVIEW GATE
        </div>
      )}
      {isOrphan && (
        <div style={{ fontSize: 9, fontWeight: 700, color: "var(--danger)", textTransform: "uppercase", marginTop: 4 }}>
          ⚠ ORPHAN
        </div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

export const agentNodeType = { agentNode: AgentNode };

/* ── Props ── */

export interface WorkflowDAGProps {
  nodes: Node[];
  edges: Edge[];
  readOnly?: boolean;
  orphanNodeIds?: Set<string>;
  onNodesChange?: any;
  onEdgesChange?: any;
  onConnect?: (conn: Connection) => void;
  onNodeClick?: (event: React.MouseEvent, node: Node) => void;
  onPaneClick?: () => void;
}

/* ── DAG canvas ── */

export function WorkflowDAG({
  nodes, edges, readOnly, orphanNodeIds,
  onNodesChange, onEdgesChange, onConnect,
  onNodeClick, onPaneClick,
}: WorkflowDAGProps) {
  const handleConnect = useCallback(
    (conn: Connection) => {
      if (readOnly) return;
      onConnect?.(conn);
    },
    [readOnly, onConnect],
  );

  const orphanSet = orphanNodeIds ?? new Set<string>();

  // Augment nodes with orphan flag for the custom node renderer
  const augmentedNodes = nodes.map(n => ({
    ...n,
    data: { ...n.data, isOrphan: orphanSet.has(n.id) },
  }));

  return (
    <ReactFlow
      nodes={augmentedNodes}
      edges={edges}
      onNodesChange={readOnly ? undefined : onNodesChange}
      onEdgesChange={readOnly ? undefined : onEdgesChange}
      onConnect={handleConnect}
      onNodeClick={onNodeClick}
      onPaneClick={onPaneClick}
      nodeTypes={agentNodeType as any}
      fitView
      nodesDraggable={!readOnly}
      nodesConnectable={!readOnly}
      elementsSelectable={!readOnly}
      colorMode="system"
      defaultEdgeOptions={{ style: { stroke: "var(--accent)", strokeWidth: 2 } }}
      deleteKeyCode={readOnly ? null : "Delete"}
    >
      <Background color="var(--border)" gap={20} />
      <Controls showZoom={true} showFitView={true} showInteractive={!readOnly} />
      <MiniMap
        nodeColor="var(--accent)"
        maskColor="var(--hover-overlay)"
        style={{ border: "1px solid var(--border)" }}
      />
    </ReactFlow>
  );
}

/* ── Helpers for converting between workflow API <-> graph ── */

export function getNodeData(n: Node): AgentNodeData {
  return (n.data as unknown as AgentNodeData) || { label: "", agent_name: "", skill: "", reviewGate: false };
}

export function workflowToGraph(
  wfNodes: { id: number; agent_id: number; depends_on: number[]; review_gate: boolean; skill: string }[],
  agentMap: Map<number, string>,
): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = wfNodes.map((n, i) => ({
    id: `node-${n.id}`,
    type: "agentNode",
    position: { x: 100 + (i % 3) * 280, y: 50 + Math.floor(i / 3) * 160 },
    data: {
      label: agentMap.get(n.agent_id) || `Node ${i}`,
      agent_name: agentMap.get(n.agent_id) || "",
      skill: n.skill || "",
      reviewGate: n.review_gate || false,
    },
  }));

  const nodeMap = new Map(wfNodes.map(n => [n.id, n]));
  const edges: Edge[] = [];
  wfNodes.forEach((n) => {
    (n.depends_on || []).forEach(depRef => {
      // depRef can be a node ID (after backend mapping) or a position index (legacy)
      const srcNode = nodeMap.get(depRef) || wfNodes[depRef];
      if (srcNode) {
        edges.push({
          id: `edge-${srcNode.id}-${n.id}`,
          source: `node-${srcNode.id}`,
          target: `node-${n.id}`,
          style: { stroke: "var(--accent)", strokeWidth: 2 },
        });
      }
    });
  });

  return { nodes, edges };
}

export function graphToWorkflow(nodes: Node[], edges: Edge[]): {
  agent_name: string; depends_on: number[]; review_gate: boolean; skill: string;
}[] {
  return nodes.map((n, i) => {
    const d = getNodeData(n);
    const incoming = edges.filter(e => e.target === n.id);
    const deps = incoming.map(e => nodes.findIndex(n2 => n2.id === e.source)).filter(idx => idx >= 0);
    return {
      agent_name: d.agent_name || "",
      depends_on: deps,
      review_gate: d.reviewGate || false,
      skill: d.skill || "",
    };
  });
}
