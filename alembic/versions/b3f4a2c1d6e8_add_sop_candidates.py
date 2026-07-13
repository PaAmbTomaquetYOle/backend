"""add sop_candidates

Revision ID: b3f4a2c1d6e8
Revises: e9b11d28972f
Create Date: 2026-07-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b3f4a2c1d6e8'
down_revision: Union[str, Sequence[str], None] = 'e9b11d28972f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('sop_candidates',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('channel_id', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
    sa.Column('author_id', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
    sa.Column('message_ts', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
    sa.Column('content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=16), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint("status IN ('offered','accepted','rejected')", name='ck_sop_candidates_status'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('channel_id', 'message_ts', name='uq_sop_candidates_channel_message_ts')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('sop_candidates')
