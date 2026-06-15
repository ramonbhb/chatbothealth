from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, cleaning, projects
from app.core.config import get_settings
from app.seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api")
    app.include_router(admin.router, prefix="/api")
    app.include_router(projects.router, prefix="/api")
    app.include_router(cleaning.router, prefix="/api")

    @app.get("/api/health")
    async def health():
        return {"status": "ok", "app": settings.app_name}

    @app.get("/api/settings/public")
    async def public_settings():
        return {
            "institution_name": settings.institution_name,
            "max_active_datasets": settings.max_active_datasets,
        }

    return app


app = create_app()
