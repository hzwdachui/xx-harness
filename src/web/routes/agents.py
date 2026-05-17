from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.db.adapter import DatabaseAdapter
from src.db.repositories import AgentRepo
from src.models import AgentTemplate
from src.web.deps import get_db
from src.web.routes._errors import not_found

router = APIRouter()


class AgentCreate(BaseModel):
    name: str
    role: str
    system_prompt: str = ""
    skills: str = ""


class AgentUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    system_prompt: str | None = None
    skills: str | None = None


@router.get("/")
def list_agents(db: DatabaseAdapter = Depends(get_db)):
    return AgentRepo(db).list_all()


@router.post("/")
def create_agent(body: AgentCreate, db: DatabaseAdapter = Depends(get_db)):
    repo = AgentRepo(db)
    existing = repo.get_by_name(body.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Agent '{body.name}' already exists")
    a = AgentTemplate(
        name=body.name, role=body.role,
        system_prompt=body.system_prompt, skills=body.skills,
    )
    a.id = repo.create(a)
    return a


@router.put("/{agent_id}")
def update_agent(agent_id: int, body: AgentUpdate, db: DatabaseAdapter = Depends(get_db)):
    repo = AgentRepo(db)
    a = repo.get(agent_id)
    if not a:
        return not_found()
    if body.name is not None:
        a.name = body.name
    if body.role is not None:
        a.role = body.role
    if body.system_prompt is not None:
        a.system_prompt = body.system_prompt
    if body.skills is not None:
        a.skills = body.skills
    repo.update(a)
    return a


@router.delete("/{agent_id}")
def delete_agent(agent_id: int, db: DatabaseAdapter = Depends(get_db)):
    repo = AgentRepo(db)
    a = repo.get(agent_id)
    if not a:
        return not_found()
    repo.delete(agent_id)
    return {"ok": True}
