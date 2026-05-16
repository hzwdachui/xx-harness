from src.db.adapter import DatabaseAdapter
from src.db.repositories import (
    ProjectRepo, TaskRepo, TaskNodeRunRepo, WorkflowRepo, WorkflowNodeRepo,
    RepositoryRepo,
)
from src.engine.workspace import WorkspaceManager
from src.engine.dag import parse_dag, get_ready_nodes
from src.engine.context import ContextAssembler
from src.engine.runner import ClaudeCodeRunner
from src.models import Task, TaskNodeRun, TaskStatus, NodeRunStatus


class Orchestrator:
    def __init__(self, db: DatabaseAdapter):
        self.db = db
        self.project_repo = ProjectRepo(db)
        self.task_repo = TaskRepo(db)
        self.node_run_repo = TaskNodeRunRepo(db)
        self.workflow_repo = WorkflowRepo(db)
        self.workflow_node_repo = WorkflowNodeRepo(db)
        self.repo_repo = RepositoryRepo(db)
        self.workspace = WorkspaceManager()
        self.context_assembler = ContextAssembler(db)
        self.runner = ClaudeCodeRunner(self.context_assembler)
        self._callbacks = []

    def on_node_complete(self, callback):
        self._callbacks.append(callback)

    def run_task(self, task_id: int, trigger_source: str = "web") -> None:
        task = self.task_repo.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        self.task_repo.update_status(task_id, TaskStatus.RUNNING.value)
        project = self.project_repo.get(task.project_id)

        workflow_id = task.workflow_id
        if not workflow_id:
            wf = self.workflow_repo.get_default_for_type(task.project_id, task.task_type)
            if not wf:
                raise ValueError(
                    f"No workflow for task type {task.task_type} in project {task.project_id}"
                )
            workflow_id = wf.id
            task.workflow_id = workflow_id
            self.task_repo.update(task)

        nodes = self.workflow_node_repo.list_by_workflow(workflow_id)
        dag = parse_dag(nodes)
        completed: set[int] = set()

        repos = self.repo_repo.list_by_project(task.project_id)

        try:
            while True:
                ready = get_ready_nodes(dag, completed)
                if not ready:
                    break

                for node in ready:
                    self._execute_node(task, project.name, node, repos, task_id)
                    completed.add(node.id)

            final_status = TaskStatus.COMPLETED.value if trigger_source == "web" else TaskStatus.PLAN_READY.value
            self.task_repo.update_status(task_id, final_status)
        except Exception:
            self.task_repo.update_status(task_id, TaskStatus.FAILED.value)
            raise

    def _execute_node(self, task, project_name, node, repos, task_id):
        wt_path = None
        for repo in repos:
            self.workspace.ensure_bare_clone(project_name, repo.name, repo.git_url)
            wt_path = self.workspace.create_worktree(
                project_name, task_id, repo.name, repo.default_branch
            )

        run = TaskNodeRun(task_id=task.id, node_id=node.id, agent_id=node.agent_id)
        run_id = self.node_run_repo.create(run)
        run.id = run_id

        run = self.runner.run(task, node, wt_path, project_name)
        self.node_run_repo.update(run)

        if node.review_gate:
            run.status = NodeRunStatus.WAITING_REVIEW.value
            self.node_run_repo.update(run)
            for cb in self._callbacks:
                cb(run)

        if run.status == NodeRunStatus.FAILED.value:
            raise RuntimeError(f"Node {node.id} failed")
