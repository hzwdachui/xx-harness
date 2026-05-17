import threading
from collections import deque

from src.db.adapter import DatabaseAdapter
from src.db.repositories import (
    ProjectRepo, TaskRepo, TaskNodeRunRepo, WorkflowRepo, WorkflowNodeRepo,
    RepositoryRepo, AgentRepo,
)
from src.engine.workspace import WorkspaceManager
from src.engine.dag import parse_dag, get_ready_nodes
from src.engine.context import ContextAssembler
from src.engine.runner import ClaudeCodeRunner
from src.models import Task, TaskNodeRun, TaskStatus, NodeRunStatus
from src.web.ws import broadcast_sync


class Orchestrator:
    def __init__(self, db: DatabaseAdapter):
        self.db = db
        self.project_repo = ProjectRepo(db)
        self.task_repo = TaskRepo(db)
        self.node_run_repo = TaskNodeRunRepo(db)
        self.workflow_repo = WorkflowRepo(db)
        self.workflow_node_repo = WorkflowNodeRepo(db)
        self.repo_repo = RepositoryRepo(db)
        self.agent_repo = AgentRepo(db)
        self.workspace = WorkspaceManager()
        self.context_assembler = ContextAssembler(db)
        self.runner = ClaudeCodeRunner(self.context_assembler)
        self._callbacks = []
        self._task_lock = threading.Lock()
        self._busy = False
        self._pending_tasks: deque[tuple[int, str]] = deque()

    def on_node_complete(self, callback):
        self._callbacks.append(callback)

    def recover_queued(self) -> None:
        """Pick up any tasks left in QUEUED status (e.g. after server restart)."""
        queued = self.task_repo.list_by_status(TaskStatus.QUEUED.value)
        if not queued:
            return
        with self._task_lock:
            for t in sorted(queued, key=lambda t: t.created_at or ""):
                self._pending_tasks.append((t.id, "recovery"))
            if not self._busy and self._pending_tasks:
                self._busy = True
                task_id, trigger_source = self._pending_tasks.popleft()
                # Run in the current thread (called from startup, not in a request)
                threading.Thread(
                    target=self._task_loop, args=(task_id, trigger_source), daemon=True,
                ).start()

    def run_task(self, task_id: int, trigger_source: str = "web") -> None:
        """Submit a task. Runs immediately if idle, otherwise queues it."""
        task = self.task_repo.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        with self._task_lock:
            if self._busy:
                self._pending_tasks.append((task_id, trigger_source))
                self.task_repo.update_status(task_id, TaskStatus.QUEUED.value)
                broadcast_sync(task_id, {"type": "task_queued", "status": TaskStatus.QUEUED.value})
                return
            self._busy = True

        self._task_loop(task_id, trigger_source)

    def _task_loop(self, task_id: int, trigger_source: str) -> None:
        """Process tasks sequentially, dequeuing the next after each completes."""
        current_id: int | None = task_id
        current_source: str = trigger_source
        while current_id is not None:
            self._execute_task(current_id, current_source)
            with self._task_lock:
                if self._pending_tasks:
                    current_id, current_source = self._pending_tasks.popleft()
                else:
                    current_id = None
                    self._busy = False

    def _execute_task(self, task_id: int, trigger_source: str) -> None:
        """Core execution logic for a single task. Does not re-raise."""
        task = self.task_repo.get(task_id)
        if not task:
            return

        self.task_repo.update_status(task_id, TaskStatus.RUNNING.value)
        broadcast_sync(task_id, {"type": "task_start", "status": TaskStatus.RUNNING.value})
        project = self.project_repo.get(task.project_id)

        workflow_id = task.workflow_id
        if not workflow_id:
            wf = self.workflow_repo.get_default_for_type(task.project_id, task.task_type)
            if not wf:
                self.task_repo.update_status(task_id, TaskStatus.FAILED.value)
                broadcast_sync(task_id, {"type": "task_failed", "status": TaskStatus.FAILED.value,
                                         "error": f"No workflow for task type {task.task_type}"})
                return
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
            broadcast_sync(task_id, {"type": "task_complete", "status": final_status})
        except Exception as e:
            self.task_repo.update_status(task_id, TaskStatus.FAILED.value)
            broadcast_sync(task_id, {"type": "task_failed", "status": TaskStatus.FAILED.value})

    def _execute_node(self, task, project_name, node, repos, task_id):
        wt_path = None
        for repo in repos:
            try:
                self.workspace.ensure_bare_clone(project_name, repo.name, repo.git_url)
                wt_path = self.workspace.create_worktree(
                    project_name, task_id, repo.name, repo.default_branch
                )
            except Exception as e:
                # Non-fatal: continue without a worktree if repo is unavailable
                print(f"[orchestrator] Repo '{repo.name}' not available: {e}")

        agent = self.agent_repo.get(node.agent_id)
        agent_skills = agent.skills if agent else ""

        run = TaskNodeRun(task_id=task.id, node_id=node.id, agent_id=node.agent_id, status=NodeRunStatus.RUNNING.value)
        run_id = self.node_run_repo.create(run)
        run.id = run_id
        broadcast_sync(task.id, {"type": "node_update", "node_id": node.id, "status": run.status})

        run = self.runner.run(task, node, wt_path, project_name, run, agent_skills)
        self.node_run_repo.update(run)
        broadcast_sync(task.id, {"type": "node_update", "node_id": node.id, "status": run.status, "result": run.result_json})

        if node.review_gate:
            run.status = NodeRunStatus.WAITING_REVIEW.value
            self.node_run_repo.update(run)
            for cb in self._callbacks:
                cb(run)

        if run.status == NodeRunStatus.FAILED.value:
            raise RuntimeError(f"Node {node.id} failed")
