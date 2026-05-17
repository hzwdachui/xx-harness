from typing import Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from src.db.adapter import DatabaseAdapter
from src.db.repositories import TaskRepo, TaskNodeRunRepo, AgentRepo
from src.models import Task, TaskStatus
from src.web.deps import get_db, get_orchestrator
from src.web.routes._errors import not_found

router = APIRouter()

class TaskCreate(BaseModel):
    project_id: int
    title: str
    task_type: str = "development"
    description: str = ""
    complexity: str = "medium"
    workflow_id: Optional[int] = None

@router.get("/project/{project_id}")
def list_tasks(project_id: int, status: Optional[str] = None, db: DatabaseAdapter = Depends(get_db)):
    return jsonable_encoder(TaskRepo(db).list_by_project(project_id, status))

@router.post("/")
def create_task(body: TaskCreate, db: DatabaseAdapter = Depends(get_db)):
    tid = TaskRepo(db).create(Task(
        project_id=body.project_id, task_type=body.task_type,
        workflow_id=body.workflow_id, title=body.title,
        description=body.description, complexity=body.complexity,
    ))
    return {"id": tid}

@router.post("/{task_id}/start")
def start_task(task_id: int, background_tasks: BackgroundTasks,
               db: DatabaseAdapter = Depends(get_db)):
    task = TaskRepo(db).get(task_id)
    if not task:
        return not_found()
    orch = get_orchestrator()
    background_tasks.add_task(orch.run_task, task_id, trigger_source="web")
    return {"ok": True, "status": "starting"}

@router.post("/{task_id}/cancel")
def cancel_task(task_id: int, db: DatabaseAdapter = Depends(get_db)):
    task = TaskRepo(db).get(task_id)
    if not task:
        return not_found()
    TaskRepo(db).update_status(task_id, TaskStatus.CANCELLED.value)
    return {"ok": True, "status": TaskStatus.CANCELLED.value}


@router.post("/{task_id}/retry")
def retry_task(task_id: int, background_tasks: BackgroundTasks,
              db: DatabaseAdapter = Depends(get_db)):
    task = TaskRepo(db).get(task_id)
    if not task:
        return not_found()
    TaskRepo(db).update_status(task_id, TaskStatus.PENDING.value)
    orch = get_orchestrator()
    background_tasks.add_task(orch.run_task, task_id, trigger_source="web")
    return {"ok": True, "status": TaskStatus.PENDING.value}


@router.get("/{task_id}")
def get_task(task_id: int, db: DatabaseAdapter = Depends(get_db)):
    task = TaskRepo(db).get(task_id)
    if not task:
        return not_found()
    runs = TaskNodeRunRepo(db).list_by_task(task_id)
    return jsonable_encoder({"task": task, "node_runs": runs})

@router.get("/{task_id}/trace")
def get_task_trace(task_id: int, db: DatabaseAdapter = Depends(get_db)):
    runs = TaskNodeRunRepo(db).list_by_task(task_id)
    agent_ids = {r.agent_id for r in runs}
    agents = AgentRepo(db).get_by_ids(agent_ids)
    return {"task_id": task_id, "runs": [
        {"node_id": r.node_id, "agent_name": agents.get(r.agent_id, "?"),
         "status": r.status, "result": r.result_json} for r in runs
    ]}
