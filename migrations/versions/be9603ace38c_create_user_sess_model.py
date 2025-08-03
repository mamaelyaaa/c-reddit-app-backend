"""create user sess model

Revision ID: be9603ace38c
Revises: e6fda714449b
Create Date: 2025-07-30 17:20:11.872155

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "be9603ace38c"
down_revision: Union[str, Sequence[str], None] = "e6fda714449b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_token", sa.String(), nullable=False),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_users_sessions_id"), "users_sessions", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_users_sessions_refresh_token"),
        "users_sessions",
        ["refresh_token"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_users_sessions_refresh_token"), table_name="users_sessions"
    )
    op.drop_index(op.f("ix_users_sessions_id"), table_name="users_sessions")
    op.drop_table("users_sessions")
