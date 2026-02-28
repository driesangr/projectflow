#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
# Project Flow – Backend entrypoint
#
# Handles two cases:
#   Fresh database  → create all tables from SQLAlchemy models, then stamp
#                     Alembic at head (so incremental migrations are skipped)
#   Existing database → run incremental Alembic migrations as normal
#
# After database setup, uvicorn is started. Any extra args (e.g. --reload)
# are forwarded to uvicorn.
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo "[entrypoint] Checking database state..."

# Detect whether the alembic_version table already exists.
# Returns "yes" for an existing install, "no" for a fresh database.
HAS_ALEMBIC=$(python3 - << 'PYEOF'
import asyncio, os, sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check():
    engine = create_async_engine(os.environ["DATABASE_URL"])
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT to_regclass('public.alembic_version')")
            )
            return result.scalar() is not None
    finally:
        await engine.dispose()

print("yes" if asyncio.run(check()) else "no")
PYEOF
)

if [ "$HAS_ALEMBIC" = "no" ]; then
    echo "[entrypoint] Fresh database – creating schema from models..."
    python3 - << 'PYEOF'
import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine
from app.models import Base
import app.models  # side-effect: registers all mapped classes with Base.metadata

async def create_all():
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

asyncio.run(create_all())
PYEOF
    echo "[entrypoint] Stamping database at migration head..."
    alembic stamp head
else
    echo "[entrypoint] Existing database – running incremental migrations..."
    alembic upgrade head
fi

echo "[entrypoint] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
