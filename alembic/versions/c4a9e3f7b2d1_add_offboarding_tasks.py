"""add offboarding_tasks

Revision ID: c4a9e3f7b2d1
Revises: b3f4a2c1d6e8
Create Date: 2026-07-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'c4a9e3f7b2d1'
down_revision: Union[str, Sequence[str], None] = 'b3f4a2c1d6e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('offboarding_tasks',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('process_id', sa.Uuid(), nullable=False),
    sa.Column('task_id', sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('source', sqlmodel.sql.sqltypes.AutoString(length=16), nullable=False),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
    sa.Column('url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.CheckConstraint("source IN ('jira','trello')", name='ck_offboarding_tasks_source'),
    sa.ForeignKeyConstraint(['process_id'], ['offboarding_processes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('process_id', 'task_id', 'source', name='uq_offboarding_tasks_process_task_source')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('offboarding_tasks')
