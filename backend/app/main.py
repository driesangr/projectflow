"""
ProjectFlow – FastAPI application entry point.

Registers all routers, configures CORS, and wires up the startup event
that creates missing tables (useful for development without running
Alembic manually).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import engine
from app.models.base import Base  # noqa: F401
import app.models  # noqa: F401 – ensure all model classes are registered

from app.routers.auth         import router as auth_router
from app.routers.project_groups import router as project_groups_router
from app.routers.projects     import router as projects_router
from app.routers.sprints      import router as sprints_router
from app.routers.topics       import router as topics_router
from app.routers.deliverables import router as deliverables_router
from app.routers.user_stories import router as user_stories_router
from app.routers.bugs         import router as bugs_router
from app.routers.tasks        import router as tasks_router
# ── New routers ──
from app.routers.memberships  import router as memberships_router
from app.routers.users        import router as users_router


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Create all tables on startup if they don't already exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.2.0",
        description="Hierarchical project management backend",
        lifespan=lifespan,
    )

    # ── CORS ────────────────────────────────────────────────────────────────
    # TODO: restrict allow_origins to your frontend domain in production
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──────────────────────────────────────────────────────────────
    application.include_router(auth_router)
    application.include_router(users_router)           # NEW
    application.include_router(project_groups_router)
    application.include_router(projects_router)
    application.include_router(memberships_router)     # NEW
    application.include_router(sprints_router)
    application.include_router(topics_router)
    application.include_router(deliverables_router)
    application.include_router(user_stories_router)
    application.include_router(bugs_router)
    application.include_router(tasks_router)

    return application


app = create_app()
