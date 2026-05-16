from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.web.routes import projects, workflows, agents, tasks, issues
from src.web.ws import ws_router


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
    return app


app = create_app()
