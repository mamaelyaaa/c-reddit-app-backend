"""add comments count ot posts

Revision ID: e6fda714449b
Revises: 98c3ad6669a9
Create Date: 2025-07-30 03:37:10.517337

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e6fda714449b"
down_revision: Union[str, Sequence[str], None] = "98c3ad6669a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "posts",
        sa.Column("comments_count", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("posts", "comments_count")
