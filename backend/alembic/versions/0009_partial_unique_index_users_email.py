"""Partial unique index on users.email (excludes soft-deleted rows)

Problem: the full unique index on users.email blocks re-creation of a user
with the same email after soft-delete (is_deleted=True records still hold
the slot in the index).

Fix: replace the full unique index with a partial unique index that only
considers non-deleted rows.

Revision ID: 0009
Revises: 0008
Create Date: 2026-02-28
"""

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old full unique index (created by SQLAlchemy unique=True)
    op.drop_index("ix_users_email", table_name="users")

    # Create partial unique index – only active (non-deleted) rows are unique
    op.execute(
        """
        CREATE UNIQUE INDEX ix_users_email
        ON users (email)
        WHERE is_deleted = false
        """
    )


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")

    # Restore full unique index (may fail if duplicates exist)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
