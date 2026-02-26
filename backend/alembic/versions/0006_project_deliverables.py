"""Allow deliverables to belong directly to a project (without a topic)

Revision ID: 0006
Revises: 0005
Create Date: 2026-02-26
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            -- Make topic_id nullable
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'deliverables'
                  AND column_name = 'topic_id' AND is_nullable = 'NO'
            ) THEN
                ALTER TABLE deliverables ALTER COLUMN topic_id DROP NOT NULL;
            END IF;

            -- Add project_id column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'deliverables'
                  AND column_name = 'project_id'
            ) THEN
                ALTER TABLE deliverables
                    ADD COLUMN project_id UUID REFERENCES projects(id) ON DELETE CASCADE;
                CREATE INDEX ix_deliverables_project_id ON deliverables(project_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            -- Remove project_id column
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'deliverables'
                  AND column_name = 'project_id'
            ) THEN
                ALTER TABLE deliverables DROP COLUMN project_id;
            END IF;

            -- Restore topic_id NOT NULL (only safe if all rows have topic_id set)
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'deliverables'
                  AND column_name = 'topic_id' AND is_nullable = 'YES'
            ) THEN
                ALTER TABLE deliverables ALTER COLUMN topic_id SET NOT NULL;
            END IF;
        END $$;
    """)
