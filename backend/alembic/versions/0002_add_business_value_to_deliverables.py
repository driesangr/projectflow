"""Add business_value column to deliverables

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-24
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'deliverables'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name  = 'deliverables'
                      AND column_name = 'business_value'
                ) THEN
                    ALTER TABLE deliverables ADD COLUMN business_value INTEGER;
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
                  AND table_name  = 'deliverables'
                  AND column_name = 'business_value'
            ) THEN
                ALTER TABLE deliverables DROP COLUMN business_value;
            END IF;
        END $$;
    """)
