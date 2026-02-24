"""Add position column to topics, deliverables, user_stories, tasks

Revision ID: 0001
Revises:
Create Date: 2026-02-24
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use DO blocks so the migration is safe on both an existing DB
    # (tables already created via SQLAlchemy create_all) and a fresh DB
    # (tables not yet created – create_all runs afterwards and will include
    # the position column from the updated model definition).
    for table, parent_col in [
        ("topics", "project_id"),
        ("deliverables", "topic_id"),
        ("user_stories", "deliverable_id"),
        ("tasks", "user_story_id"),
    ]:
        op.execute(
            f"""
            DO $$
            BEGIN
                -- Only proceed if the table already exists
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = '{table}'
                ) THEN
                    -- Add column only if it is missing
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND table_name  = '{table}'
                          AND column_name = 'position'
                    ) THEN
                        ALTER TABLE {table}
                            ADD COLUMN position INTEGER NOT NULL DEFAULT 0;
                    END IF;

                    -- Assign sequential positions (0-based) within each
                    -- parent group ordered by creation date
                    UPDATE {table} t
                    SET position = sub.rn
                    FROM (
                        SELECT id,
                               ROW_NUMBER() OVER (
                                   PARTITION BY {parent_col}
                                   ORDER BY created_at
                               ) - 1 AS rn
                        FROM {table}
                        WHERE is_deleted = false
                    ) sub
                    WHERE t.id = sub.id;
                END IF;
            END $$;
            """
        )


def downgrade() -> None:
    for table in ("topics", "deliverables", "user_stories", "tasks"):
        op.execute(
            f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name  = '{table}'
                      AND column_name = 'position'
                ) THEN
                    ALTER TABLE {table} DROP COLUMN position;
                END IF;
            END $$;
            """
        )
