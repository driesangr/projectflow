"""Add business_value and sprint_value to user_stories, sprint_value to tasks

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-24
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'user_stories'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name  = 'user_stories'
                      AND column_name = 'business_value'
                ) THEN
                    ALTER TABLE user_stories ADD COLUMN business_value INTEGER;
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name  = 'user_stories'
                      AND column_name = 'sprint_value'
                ) THEN
                    ALTER TABLE user_stories ADD COLUMN sprint_value INTEGER;
                END IF;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'tasks'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name  = 'tasks'
                      AND column_name = 'sprint_value'
                ) THEN
                    ALTER TABLE tasks ADD COLUMN sprint_value INTEGER;
                END IF;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='user_stories' AND column_name='business_value') THEN
                ALTER TABLE user_stories DROP COLUMN business_value;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='user_stories' AND column_name='sprint_value') THEN
                ALTER TABLE user_stories DROP COLUMN sprint_value;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='tasks' AND column_name='sprint_value') THEN
                ALTER TABLE tasks DROP COLUMN sprint_value;
            END IF;
        END $$;
    """)
