"""Add role_permissions table with ArtifactType enum

Revision ID: 0008
Revises: 0007
Create Date: 2026-02-27

What this migration does
------------------------
1. Creates the ``artifacttype`` PostgreSQL enum type.
2. Creates the ``role_permissions`` table with all permission columns
   incl. is_explicit (A-2.1: true = admin-set, false = propagated).
3. Adds a unique index on (project_role, artifact_type).
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN

        -- ──────────────────────────────────────────────────────────
        -- 1. artifacttype enum
        -- ──────────────────────────────────────────────────────────
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'artifacttype') THEN
            CREATE TYPE artifacttype AS ENUM (
                'project_group',
                'project',
                'topic',
                'deliverable',
                'user_story',
                'task'
            );
        END IF;

        -- ──────────────────────────────────────────────────────────
        -- 2. role_permissions table
        -- ──────────────────────────────────────────────────────────
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'role_permissions'
        ) THEN
            CREATE TABLE role_permissions (
                id                  UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
                created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
                project_role        projectrole NOT NULL,
                artifact_type       artifacttype NOT NULL,
                can_read            BOOLEAN     NOT NULL DEFAULT true,
                can_write           BOOLEAN     NOT NULL DEFAULT false,
                can_create          BOOLEAN     NOT NULL DEFAULT false,
                can_delete          BOOLEAN     NOT NULL DEFAULT false,
                inherit_to_children BOOLEAN     NOT NULL DEFAULT false,
                is_explicit         BOOLEAN     NOT NULL DEFAULT true,
                CONSTRAINT uq_role_artifact UNIQUE (project_role, artifact_type)
            );

            CREATE INDEX ix_role_permissions_project_role  ON role_permissions(project_role);
            CREATE INDEX ix_role_permissions_artifact_type ON role_permissions(artifact_type);
        END IF;

        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN

        DROP TABLE IF EXISTS role_permissions;
        DROP TYPE IF EXISTS artifacttype;

        END $$;
    """)
