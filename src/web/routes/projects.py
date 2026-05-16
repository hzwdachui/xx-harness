from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from src.db.adapter import DatabaseAdapter
from src.db.repositories import ProjectRepo, RepositoryRepo
from src.models import Project, Repository
from src.web.deps import get_db

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    boundary: str = ""


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    boundary: Optional[str] = None


class RepoCreate(BaseModel):
    name: str
    git_url: str
    default_branch: str = "master"


@router.get("/")
def list_projects(db: DatabaseAdapter = Depends(get_db)):
    return jsonable_encoder(ProjectRepo(db).list_all())


@router.post("/")
def create_project(body: ProjectCreate, db: DatabaseAdapter = Depends(get_db)):
    pid = ProjectRepo(db).create(Project(name=body.name, description=body.description, boundary=body.boundary))
    return {"id": pid}


@router.get("/{project_id}")
def get_project(project_id: int, db: DatabaseAdapter = Depends(get_db)):
    p = ProjectRepo(db).get(project_id)
    if not p:
        return JSONResponse({"error": "not found"}, 404)
    return jsonable_encoder(p)


@router.put("/{project_id}")
def update_project(project_id: int, body: ProjectUpdate, db: DatabaseAdapter = Depends(get_db)):
    repo = ProjectRepo(db)
    p = repo.get(project_id)
    if not p:
        return JSONResponse({"error": "not found"}, 404)
    if body.name is not None:
        p.name = body.name
    if body.description is not None:
        p.description = body.description
    if body.boundary is not None:
        p.boundary = body.boundary
    repo.update(p)
    return jsonable_encoder(p)


@router.delete("/{project_id}")
def delete_project(project_id: int, db: DatabaseAdapter = Depends(get_db)):
    ProjectRepo(db).delete(project_id)
    return {"ok": True}


@router.get("/{project_id}/repos")
def list_repos(project_id: int, db: DatabaseAdapter = Depends(get_db)):
    return jsonable_encoder(RepositoryRepo(db).list_by_project(project_id))


@router.post("/{project_id}/repos")
def add_repo(project_id: int, body: RepoCreate, db: DatabaseAdapter = Depends(get_db)):
    rid = RepositoryRepo(db).create(Repository(
        project_id=project_id, name=body.name, git_url=body.git_url,
        default_branch=body.default_branch,
    ))
    return {"id": rid}


@router.delete("/{project_id}/repos/{repo_id}")
def remove_repo(project_id: int, repo_id: int, db: DatabaseAdapter = Depends(get_db)):
    RepositoryRepo(db).delete(repo_id)
    return {"ok": True}
