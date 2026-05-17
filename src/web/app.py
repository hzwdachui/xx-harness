import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.web.routes import projects, workflows, agents, tasks, issues
from src.web.ws import ws_router


_git_info_cache: dict | None = None

def get_git_info():
    global _git_info_cache
    if _git_info_cache is not None:
        return _git_info_cache
    try:
        output = subprocess.check_output(
            ["git", "log", "-1", "--format=%H%x00%h%x00%s%x00%ci"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
        hash_, short, subject, date = output.split("\0")
        _git_info_cache = {"hash": hash_, "short": short, "subject": subject, "date": date}
    except Exception:
        _git_info_cache = {"hash": "unknown", "short": "unknown", "subject": "unknown", "date": "unknown"}
    return _git_info_cache


def create_app() -> FastAPI:
    app = FastAPI(title="xx-harness", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
    app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
    app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
    app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
    app.include_router(issues.router, prefix="/api/issues", tags=["issues"])
    app.include_router(ws_router)

    @app.on_event("startup")
    def startup_recover_queued():
        """Recover tasks stuck in QUEUED status after server restart."""
        from src.web.deps import get_orchestrator
        orch = get_orchestrator()
        orch.recover_queued()

    @app.get("/api/version")
    def version():
        return {"version": "0.1.0", "commit": get_git_info()}

    return app


app = create_app()
