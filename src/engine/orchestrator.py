from datetime import datetime
from src.db.adapter import DatabaseAdapter
from src.db.repositories import (
    ProjectRepo, TaskRepo, TaskNodeRunRepo, WorkflowRepo, WorkflowNodeRepo,
    AgentRepo, KnownIssueRepo, ConstraintRuleRepo, SkillMappingRepo,
    RepositoryRepo,
)
from src.engine.workspace import WorkspaceManager
from src.engine.dag import parse_dag, get_ready_nodes
from src.engine.context import ContextAssembler
from src.engine.runner import ClaudeCodeRunner
from src.models import Task, TaskNodeRun


class Orchestrator:
    def __init__(self, db: DatabaseAdapter):
        self.db = db
        self.project_repo = ProjectRepo(db)
        self.task_repo = TaskRepo(db)
        self.node_run_repo = TaskNodeRunRepo(db)
        self.workflow_repo = WorkflowRepo(db)
        self.workflow_node_repo = WorkflowNodeRepo(db)
        self.agent_repo = AgentRepo(db)
        self.known_issue_repo = KnownIssueRepo(db)
        self.constraint_rule_repo = ConstraintRuleRepo(db)
        self.skill_repo = SkillMappingRepo(db)
        self.repo_repo = RepositoryRepo(db)
        self.workspace = WorkspaceManager()
        self.context_assembler = ContextAssembler(
            db, self.project_repo, self.task_repo, self.node_run_repo,
            self.workflow_node_repo, self.known_issue_repo,
            self.constraint_rule_repo, self.skill_repo,
        )
        self.runner = ClaudeCodeRunner(self.context_assembler)
        self._callbacks = []

    def on_node_complete(self, callback):
        self._callbacks.append(callback)

    def run_task(self, task_id: int, trigger_source: str = "web") -> None:
        task = self.task_repo.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        self.task_repo.update_status(task_id, "running")
        project = self.project_repo.get(task.project_id)

        # Resolve workflow
        workflow_id = task.workflow_id
        if not workflow_id:
            wf = self.workflow_repo.get_default_for_type(task.project_id, task.task_type)
            if not wf:
                raise ValueError(f"No workflow for task type {task.task_type} in project {task.project_id}")
            workflow_id = wf.id
            task.workflow_id = workflow_id
            self.task_repo.update(task)

        nodes = self.workflow_node_repo.list_by_workflow(workflow_id)
        dag = parse_dag(nodes)
        completed: set[int] = set()

        try:
            while True:
                ready = get_ready_nodes(dag, completed)
                if not ready:
                    break

                for node in ready:
                    # Prepare worktree
                    repos = self.repo_repo.list_by_project(task.project_id)
                    wt_path = None
                    for repo in repos:
                        self.workspace.ensure_bare_clone(project.name, repo.name, repo.git_url)
                        wt_path = self.workspace.create_worktree(project.name, task_id, repo.name, repo.default_branch)

                    # Create run record
                    run = TaskNodeRun(task_id=task.id, node_id=node.id, agent_id=node.agent_id)
                    run_id = self.node_run_repo.create(run)
                    run.id = run_id

                    # Execute
                    run = self.runner.run(task, node, wt_path, project.name)
                    self.node_run_repo.update(run)

                    # Review gate
                    if node.review_gate:
                        run.status = "waiting_review"
                        self.node_run_repo.update(run)
                        for cb in self._callbacks:
                            cb(run)

                    if run.status == "failed":
                        raise RuntimeError(f"Node {node.id} failed")

                    completed.add(node.id)

            self.task_repo.update_status(task_id, "completed" if trigger_source == "web" else "plan_ready")
        except Exception:
            self.task_repo.update_status(task_id, "failed")
            raise
