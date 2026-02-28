"""Partial unique index on users.username (excludes soft-deleted rows)

Same fix as 0009 for email: replace the full unique index with a partial
one so that soft-deleted usernames can be reused without constraint errors.

Revision ID: 0010
Revises: 0009
Create Date: 2026-02-28
"""

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.execute(
        """
        CREATE UNIQUE INDEX ix_users_username
        ON users (username)
        WHERE is_deleted = false
        """
    )


def downgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.create_index("ix_users_username", "users", ["username"], unique=True)
