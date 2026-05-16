from fastapi import APIRouter, Depends
from src.db.adapter import DatabaseAdapter
from src.db.repositories import AgentRepo
from src.web.deps import get_db

router = APIRouter()

@router.get("/")
def list_agents(db: DatabaseAdapter = Depends(get_db)):
    return AgentRepo(db).list_all()
