"""intent pipeline metadata

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("intents", sa.Column("pipeline", sa.String(), nullable=True))
    op.add_column("intents", sa.Column("core_version", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("intents", "core_version")
    op.drop_column("intents", "pipeline")
