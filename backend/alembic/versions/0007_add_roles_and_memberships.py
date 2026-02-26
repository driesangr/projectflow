"""Add global_role to users and project_memberships table

Revision ID: 0007
Revises: 0006
Create Date: 2026-02-26

What this migration does
------------------------
1. Adds the ``globalrole`` enum type and a ``global_role`` column on ``users``
   (default: 'user'). Existing admins (is_admin = true) are promoted to 'admin'.
2. Adds the ``projectrole`` enum type.
3. Creates the ``project_memberships`` table.
4. Adds ``owner_id`` (FK → users.id) to ``projects``.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN

        -- ──────────────────────────────────────────────────────────
        -- 1. globalrole enum + column on users
        -- ──────────────────────────────────────────────────────────
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'globalrole') THEN
            CREATE TYPE globalrole AS ENUM ('superuser', 'admin', 'user');
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users'
              AND column_name = 'global_role'
        ) THEN
            ALTER TABLE users
                ADD COLUMN global_role globalrole NOT NULL DEFAULT 'user';

            -- Promote existing admins
            UPDATE users SET global_role = 'admin' WHERE is_admin = true;

            CREATE INDEX ix_users_global_role ON users(global_role);
        END IF;

        -- ──────────────────────────────────────────────────────────
        -- 2. projectrole enum
        -- ──────────────────────────────────────────────────────────
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'projectrole') THEN
            CREATE TYPE projectrole AS ENUM ('owner', 'manager', 'member', 'viewer');
        END IF;

        -- ──────────────────────────────────────────────────────────
        -- 3. project_memberships table
        -- ──────────────────────────────────────────────────────────
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'project_memberships'
        ) THEN
            CREATE TABLE project_memberships (
                id         UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                user_id    UUID        NOT NULL REFERENCES users(id)    ON DELETE CASCADE,
                project_id UUID        NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                role       projectrole NOT NULL DEFAULT 'member',
                CONSTRAINT uq_membership_user_project UNIQUE (user_id, project_id)
            );

            CREATE INDEX ix_project_memberships_user_id    ON project_memberships(user_id);
            CREATE INDEX ix_project_memberships_project_id ON project_memberships(project_id);
        END IF;

        -- ──────────────────────────────────────────────────────────
        -- 4. owner_id on projects
        -- ──────────────────────────────────────────────────────────
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'projects'
              AND column_name = 'owner_id'
        ) THEN
            ALTER TABLE projects
                ADD COLUMN owner_id UUID REFERENCES users(id) ON DELETE SET NULL;

            CREATE INDEX ix_projects_owner_id ON projects(owner_id);
        END IF;

        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN

        -- Remove owner_id from projects
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'projects'
              AND column_name = 'owner_id'
        ) THEN
            ALTER TABLE projects DROP COLUMN owner_id;
        END IF;

        -- Drop project_memberships
        DROP TABLE IF EXISTS project_memberships;

        -- Drop projectrole enum
        DROP TYPE IF EXISTS projectrole;

        -- Remove global_role from users
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users'
              AND column_name = 'global_role'
        ) THEN
            ALTER TABLE users DROP COLUMN global_role;
        END IF;

        -- Drop globalrole enum
        DROP TYPE IF EXISTS globalrole;

        END $$;
    """)
