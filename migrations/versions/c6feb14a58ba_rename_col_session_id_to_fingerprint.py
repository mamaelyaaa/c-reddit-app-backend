"""rename col session_id to fingerprint

Revision ID: c6feb14a58ba
Revises: be9603ace38c
Create Date: 2025-08-26 16:40:36.905220

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c6feb14a58ba"
down_revision: Union[str, Sequence[str], None] = "be9603ace38c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("users_sessions", "session_id", new_column_name="fingerprint")


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("users_sessions", "fingerprint", new_column_name="session_id")
