from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import agent as agent_routes
from app.api.routes import evidence as evidence_routes
from app.api.routes import projects as projects_routes
from app.core.config import get_settings
from app.core.errors import install_error_handlers


def create_app() -> FastAPI:
    app = FastAPI(title="Canopy API", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    settings = get_settings()
    settings.assets_dir.mkdir(parents=True, exist_ok=True)
    app.mount(settings.static_mount, StaticFiles(directory=settings.assets_dir), name="static")

    install_error_handlers(app)
    app.include_router(projects_routes.router)
    app.include_router(evidence_routes.router)
    app.include_router(agent_routes.router)

    return app


app = create_app()
