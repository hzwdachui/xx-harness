import json
from fastapi import APIRouter, Depends
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
    from fastapi.encoders import jsonable_encoder

    wf_repo = WorkflowRepo(db)
    wf_id = wf_repo.create(Workflow(
        project_id=body.project_id, name=body.name, task_type=body.task_type,
    ))

    node_repo = WorkflowNodeRepo(db)
    agent_repo = AgentRepo(db)
    for i, nd in enumerate(body.nodes):
        agent = agent_repo.get_by_name(nd.agent_name)
        if not agent:
            from fastapi.responses import JSONResponse
            return JSONResponse({"error": f"agent {nd.agent_name} not found"}, 400)
        node_repo.create(WorkflowNode(
            workflow_id=wf_id, agent_id=agent.id,
            depends_on=nd.depends_on, review_gate=nd.review_gate,
            skill=nd.skill, skill_args=nd.skill_args,
            context_json=nd.context_json, position=i,
        ))

    nodes = node_repo.list_by_workflow(wf_id)
    return jsonable_encoder({"id": wf_id, "nodes": nodes})

@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: int, db: DatabaseAdapter = Depends(get_db)):
    WorkflowRepo(db).delete(workflow_id)
    return {"ok": True}
