from src.engine.dag import parse_dag, get_ready_nodes, group_parallel, topological_sort
from src.models import WorkflowNode


def _node(id, deps=None):
    return WorkflowNode(workflow_id=1, agent_id=1, depends_on=deps or [], id=id, position=0)


def test_parse_dag():
    nodes = [_node(1), _node(2, [1]), _node(3, [1])]
    dag = parse_dag(nodes)
    assert dag[1]["dependents"] == [2, 3]
    assert dag[2]["deps"] == [1]


def test_ready_nodes_sequential():
    nodes = [_node(1), _node(2, [1]), _node(3, [2])]
    dag = parse_dag(nodes)
    ready = get_ready_nodes(dag, set())
    assert len(ready) == 1
    assert ready[0].id == 1
    ready = get_ready_nodes(dag, {1})
    assert ready[0].id == 2


def test_group_parallel():
    nodes = [_node(1), _node(2, [1]), _node(3, [1])]
    batches = group_parallel(nodes)
    assert len(batches) == 2
    assert {n.id for n in batches[0]} == {2, 3}


def test_topological_sort():
    nodes = [_node(1), _node(2, [1]), _node(3, [1]), _node(4, [2, 3])]
    dag = parse_dag(nodes)
    order = topological_sort(dag)
    assert order.index(1) < order.index(2)
    assert order.index(1) < order.index(3)
    assert order.index(2) < order.index(4)
    assert order.index(3) < order.index(4)


def test_topological_sort_detects_cycle():
    nodes = [_node(1, [2]), _node(2, [1])]
    dag = parse_dag(nodes)
    try:
        topological_sort(dag)
        assert False, "should have raised"
    except ValueError as e:
        assert "cycle" in str(e)
