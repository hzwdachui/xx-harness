from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from src.db.adapter import DatabaseAdapter
from src.db.repositories import WorkflowRepo, WorkflowNodeRepo, AgentRepo
from src.models import Workflow, WorkflowNode
from src.web.deps import get_db

router = APIRouter()

class NodeDef(BaseModel):
    agent_name: str
    depends_on: list[int] = []
    review_gate: bool = False
    skill: str = ""
    skill_args: str = ""
    context_json: dict = {}

class WorkflowCreate(BaseModel):
    name: str
    task_type: str = "custom"
    project_id: int
    nodes: list[NodeDef] = []

@router.get("/project/{project_id}")
def list_workflows(project_id: int, db: DatabaseAdapter = Depends(get_db)):
    workflows = WorkflowRepo(db).list_by_project(project_id)
    result = []
    node_repo = WorkflowNodeRepo(db)
    for wf in workflows:
        nodes = node_repo.list_by_workflow(wf.id)
        result.append({"workflow": wf, "nodes": nodes})
    return result

@router.post("/")
def create_workflow(body: WorkflowCreate, db: DatabaseAdapter = Depends(get_db)):
    wf_repo = WorkflowRepo(db)
    wf_id = wf_repo.create(Workflow(
        project_id=body.project_id, name=body.name, task_type=body.task_type,
    ))

    node_repo = WorkflowNodeRepo(db)
    agent_repo = AgentRepo(db)
    node_ids: list[int] = []
    for i, nd in enumerate(body.nodes):
        agent = agent_repo.get_by_name(nd.agent_name)
        if not agent:
            return JSONResponse({"error": f"agent {nd.agent_name} not found"}, 400)
        nid = node_repo.create(WorkflowNode(
            workflow_id=wf_id, agent_id=agent.id,
            depends_on=[], review_gate=nd.review_gate,
            skill=nd.skill, skill_args=nd.skill_args,
            context_json=nd.context_json, position=i,
        ))
        node_ids.append(nid)

    # Map position-index deps to actual node IDs
    for i, nd in enumerate(body.nodes):
        if nd.depends_on:
            mapped = [node_ids[idx] for idx in nd.depends_on if idx < len(node_ids)]
            node_repo.update_node_deps(node_ids[i], mapped)

    nodes = node_repo.list_by_workflow(wf_id)
    return jsonable_encoder({"id": wf_id, "nodes": nodes})

@router.put("/{workflow_id}")
def update_workflow(workflow_id: int, body: WorkflowCreate, db: DatabaseAdapter = Depends(get_db)):
    wf_repo = WorkflowRepo(db)
    wf = wf_repo.get(workflow_id)
    if not wf:
        from src.web.routes._errors import not_found
        return not_found()

    wf.name = body.name
    wf.task_type = body.task_type
    wf_repo.update(wf)

    node_repo = WorkflowNodeRepo(db)
    agent_repo = AgentRepo(db)
    existing = node_repo.list_by_workflow(workflow_id)
    node_ids: list[int] = []

    for i, nd in enumerate(body.nodes):
        agent = agent_repo.get_by_name(nd.agent_name)
        if not agent:
            return JSONResponse({"error": f"agent {nd.agent_name} not found"}, 400)
        if i < len(existing):
            # Update existing node in place (preserves FK references from task_node_runs)
            node_repo.update_node(
                existing[i].id, agent.id, [],
                nd.review_gate, nd.skill, i,
            )
            node_ids.append(existing[i].id)
        else:
            # Create new node
            nid = node_repo.create(WorkflowNode(
                workflow_id=workflow_id, agent_id=agent.id,
                depends_on=[], review_gate=nd.review_gate,
                skill=nd.skill, skill_args=nd.skill_args,
                context_json=nd.context_json, position=i,
            ))
            node_ids.append(nid)

    # Map position-index deps to actual node IDs
    for i, nd in enumerate(body.nodes):
        if nd.depends_on:
            mapped = [node_ids[idx] for idx in nd.depends_on if idx < len(node_ids)]
            node_repo.update_node_deps(node_ids[i], mapped)

    # Try removing extra nodes (FK will block if runs exist — safe)
    for extra in existing[len(body.nodes):]:
        try:
            db.execute("DELETE FROM workflow_node WHERE id = ?", [extra.id])
        except Exception:
            pass

    nodes = node_repo.list_by_workflow(workflow_id)
    return jsonable_encoder({"id": workflow_id, "nodes": nodes})


@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: int, db: DatabaseAdapter = Depends(get_db)):
    WorkflowRepo(db).delete(workflow_id)
    return {"ok": True}
