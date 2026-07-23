"""initial baseline

Revision ID: 0001
Revises:
Create Date: 2026-07-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "intents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("utterance", sa.String(), nullable=False),
        sa.Column("intent", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("match_data", sa.String(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(op.f("ix_intents_id"), "intents", ["id"], unique=False)

    op.create_table(
        "wake_words",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("plugin", sa.String(), nullable=True),
        sa.Column("plugin_config", sa.String(), nullable=True),
        sa.Column("audio", sa.LargeBinary(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(op.f("ix_wake_words_id"), "wake_words", ["id"], unique=False)

    op.create_table(
        "stt",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transcript", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("plugin", sa.String(), nullable=True),
        sa.Column("plugin_config", sa.String(), nullable=True),
        sa.Column("audio", sa.LargeBinary(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(op.f("ix_stt_id"), "stt", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_stt_id"), table_name="stt")
    op.drop_table("stt")

    op.drop_index(op.f("ix_wake_words_id"), table_name="wake_words")
    op.drop_table("wake_words")

    op.drop_index(op.f("ix_intents_id"), table_name="intents")
    op.drop_table("intents")
