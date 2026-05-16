from src.models import WorkflowNode


def parse_dag(nodes: list[WorkflowNode]) -> dict:
    """Parse workflow nodes into DAG structure.
    Returns: {node_id: {"node": WorkflowNode, "deps": [...], "dependents": [...]}}
    """
    dag = {}
    for n in nodes:
        dag[n.id] = {"node": n, "deps": list(n.depends_on), "dependents": []}
    for n in nodes:
        for dep_id in n.depends_on:
            if dep_id in dag:
                dag[dep_id]["dependents"].append(n.id)
    return dag


def get_ready_nodes(dag: dict, completed_node_ids: set[int]) -> list[WorkflowNode]:
    """Get nodes whose dependencies are all satisfied."""
    ready = []
    for nid, info in dag.items():
        if nid in completed_node_ids:
            continue
        if all(dep in completed_node_ids for dep in info["deps"]):
            ready.append(info["node"])
    return ready


def group_parallel(nodes: list[WorkflowNode]) -> list[list[WorkflowNode]]:
    """Group independent nodes into parallel batches.
    Nodes with no dependencies between them run in the same batch."""
    if not nodes:
        return []
    node_map = {n.id: n for n in nodes}
    # Build dependents map (who depends on me)
    dependents: dict[int, list[int]] = {n.id: [] for n in nodes}
    for n in nodes:
        for dep_id in n.depends_on:
            if dep_id in dependents:
                dependents[dep_id].append(n.id)
    remaining_ids = set(node_map.keys())
    batches = []
    while remaining_ids:
        batch_ids: list[int] = []
        for nid in list(remaining_ids):
            # A node is ready for this batch if none of its dependents are still remaining
            if not any(dep in remaining_ids for dep in dependents[nid]):
                batch_ids.append(nid)
        if batch_ids:
            for nid in batch_ids:
                remaining_ids.remove(nid)
            batches.append([node_map[nid] for nid in batch_ids])
        else:
            # Cycle or complex dependency: just add remaining one at a time
            batches.append([node_map[nid] for nid in remaining_ids])
            break
    return batches


def topological_sort(dag: dict) -> list[int]:
    """Topological sort of DAG node IDs. Raises ValueError on cycle."""
    in_degree = {nid: len(info["deps"]) for nid, info in dag.items()}
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    result = []
    while queue:
        nid = queue.pop(0)
        result.append(nid)
        for dep_id in dag[nid]["dependents"]:
            in_degree[dep_id] -= 1
            if in_degree[dep_id] == 0:
                queue.append(dep_id)
    if len(result) != len(dag):
        raise ValueError("DAG contains a cycle")
    return result
