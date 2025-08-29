"""add user_verf_token model

Revision ID: fe3c566e9375
Revises: c6feb14a58ba
Create Date: 2025-08-29 15:05:30.625864

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fe3c566e9375"
down_revision: Union[str, Sequence[str], None] = "c6feb14a58ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users_verification_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("hashed_token", sa.String(), nullable=False),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_users_verification_tokens_id"),
        "users_verification_tokens",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_users_verification_tokens_id"),
        table_name="users_verification_tokens",
    )
    op.drop_table("users_verification_tokens")
