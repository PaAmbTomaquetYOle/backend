"""add review processes

Revision ID: d5e6f8a1c3b7
Revises: c4a9e3f7b2d1
Create Date: 2026-07-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e6f8a1c3b7'
down_revision: Union[str, Sequence[str], None] = 'c4a9e3f7b2d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('ck_processes_type', 'processes', type_='check')
    op.create_check_constraint(
        'ck_processes_type', 'processes', "type IN ('offboarding','monthly_review','annual_review')"
    )
    op.create_table('monthly_review_processes',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('state', sa.String(), nullable=False),
    sa.CheckConstraint("state IN ('not_started','in_progress','finished','cancelled')", name='ck_monthly_review_processes_state'),
    sa.ForeignKeyConstraint(['id'], ['processes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('annual_review_processes',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('state', sa.String(), nullable=False),
    sa.CheckConstraint("state IN ('not_started','in_progress','pending_revision','finished','cancelled')", name='ck_annual_review_processes_state'),
    sa.ForeignKeyConstraint(['id'], ['processes.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('annual_review_processes')
    op.drop_table('monthly_review_processes')
    op.drop_constraint('ck_processes_type', 'processes', type_='check')
    op.create_check_constraint('ck_processes_type', 'processes', "type IN ('offboarding')")
