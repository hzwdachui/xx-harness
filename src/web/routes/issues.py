from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.db.adapter import DatabaseAdapter
from src.db.repositories import KnownIssueRepo, ConstraintRuleRepo
from src.models import KnownIssue, ConstraintRule
from src.web.deps import get_db

router = APIRouter()

class IssueCreate(BaseModel):
    project_id: Optional[int] = None
    error_pattern: str
    root_cause: str = ""
    rule_update: str = ""
    level: str = "project"

class RuleCreate(BaseModel):
    project_id: Optional[int] = None
    rule_type: str
    content: str
    level: str = "project"

@router.get("/project/{project_id}")
def list_issues(project_id: int, db: DatabaseAdapter = Depends(get_db)):
    return KnownIssueRepo(db).list_by_project(project_id)

@router.post("/")
def create_issue(body: IssueCreate, db: DatabaseAdapter = Depends(get_db)):
    rid = KnownIssueRepo(db).create(KnownIssue(
        project_id=body.project_id, error_pattern=body.error_pattern,
        root_cause=body.root_cause, rule_update=body.rule_update,
        level=body.level,
    ))
    return {"id": rid}

@router.get("/rules/project/{project_id}")
def list_rules(project_id: int, db: DatabaseAdapter = Depends(get_db)):
    return ConstraintRuleRepo(db).list_by_project(project_id)

@router.post("/rules")
def create_rule(body: RuleCreate, db: DatabaseAdapter = Depends(get_db)):
    rid = ConstraintRuleRepo(db).create(ConstraintRule(
        project_id=body.project_id, rule_type=body.rule_type,
        content=body.content, level=body.level,
    ))
    return {"id": rid}
