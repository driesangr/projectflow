"""Add bugs table and related columns

Revision ID: 0005
Revises: 0004
Create Date: 2026-02-25
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            -- Create bugstatus enum if it doesn't exist
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'bugstatus') THEN
                CREATE TYPE bugstatus AS ENUM ('todo', 'in_progress', 'done', 'on_hold');
            END IF;

            -- Create bugs table
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'bugs'
            ) THEN
                CREATE TABLE bugs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    acceptance_criteria TEXT,
                    story_points INTEGER,
                    business_value INTEGER,
                    sprint_value INTEGER,
                    position INTEGER NOT NULL DEFAULT 0,
                    status bugstatus NOT NULL DEFAULT 'todo',
                    owner_name VARCHAR(255),
                    deliverable_id UUID NOT NULL REFERENCES deliverables(id) ON DELETE CASCADE,
                    sprint_id UUID REFERENCES sprints(id) ON DELETE SET NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                    deleted_at TIMESTAMPTZ
                );
                CREATE INDEX ix_bugs_deliverable_id ON bugs (deliverable_id);
                CREATE INDEX ix_bugs_sprint_id ON bugs (sprint_id);
                CREATE INDEX ix_bugs_status ON bugs (status);
                CREATE INDEX ix_bugs_is_deleted ON bugs (is_deleted);
            END IF;

            -- Add bug_id to tasks
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'tasks' AND column_name = 'bug_id'
            ) THEN
                ALTER TABLE tasks ADD COLUMN bug_id UUID REFERENCES bugs(id) ON DELETE SET NULL;
                CREATE INDEX ix_tasks_bug_id ON tasks (bug_id);
            END IF;

            -- Make tasks.user_story_id nullable
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'tasks'
                  AND column_name = 'user_story_id' AND is_nullable = 'NO'
            ) THEN
                ALTER TABLE tasks ALTER COLUMN user_story_id DROP NOT NULL;
            END IF;

            -- Add bug_id to comments
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'comments' AND column_name = 'bug_id'
            ) THEN
                ALTER TABLE comments ADD COLUMN bug_id UUID REFERENCES bugs(id) ON DELETE CASCADE;
                CREATE INDEX ix_comments_bug_id ON comments (bug_id);
            END IF;

            -- Add bug_id to links
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'links' AND column_name = 'bug_id'
            ) THEN
                ALTER TABLE links ADD COLUMN bug_id UUID REFERENCES bugs(id) ON DELETE CASCADE;
                CREATE INDEX ix_links_bug_id ON links (bug_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            -- Remove bug_id from links
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'links' AND column_name = 'bug_id'
            ) THEN
                ALTER TABLE links DROP COLUMN bug_id;
            END IF;

            -- Remove bug_id from comments
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'comments' AND column_name = 'bug_id'
            ) THEN
                ALTER TABLE comments DROP COLUMN bug_id;
            END IF;

            -- Remove bug_id from tasks
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'tasks' AND column_name = 'bug_id'
            ) THEN
                ALTER TABLE tasks DROP COLUMN bug_id;
            END IF;

            -- Drop bugs table
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'bugs'
            ) THEN
                DROP TABLE bugs;
            END IF;

            -- Drop bugstatus enum
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'bugstatus') THEN
                DROP TYPE bugstatus;
            END IF;
        END $$;
    """)
