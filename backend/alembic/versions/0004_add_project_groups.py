"""Add project_groups table and project_group_id to projects

Revision ID: 0004
Revises: 0003
Create Date: 2026-02-25
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'project_groups'
            ) THEN
                CREATE TABLE project_groups (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                    deleted_at TIMESTAMPTZ
                );
                CREATE INDEX ix_project_groups_is_deleted ON project_groups (is_deleted);
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'projects'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name  = 'projects'
                      AND column_name = 'project_group_id'
                ) THEN
                    ALTER TABLE projects
                        ADD COLUMN project_group_id UUID REFERENCES project_groups(id);
                    CREATE INDEX ix_projects_project_group_id ON projects (project_group_id);
                END IF;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name   = 'projects'
                  AND column_name  = 'project_group_id'
            ) THEN
                ALTER TABLE projects DROP COLUMN project_group_id;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'project_groups'
            ) THEN
                DROP TABLE project_groups;
            END IF;
        END $$;
    """)
