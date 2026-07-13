"""add sop title

Revision ID: d2f5a6c9e4b3
Revises: c4a9e3f7b2d1
Create Date: 2026-07-11 00:00:00.000001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

from app.infrastructure.persistence.models.sop import SOPS_CONTENT_FTS_INDEX_SQL


# revision identifiers, used by Alembic.
revision: str = 'd2f5a6c9e4b3'
down_revision: Union[str, Sequence[str], None] = 'c4a9e3f7b2d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OLD_FTS_INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS ix_sops_content_fts "
    "ON sops USING gin (to_tsvector('english', content))"
)


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'sops',
        sa.Column(
            'title',
            sqlmodel.sql.sqltypes.AutoString(length=200),
            nullable=False,
            server_default='',
        ),
    )
    op.alter_column('sops', 'title', server_default=None)

    op.execute("DROP INDEX IF EXISTS ix_sops_content_fts")
    op.execute(SOPS_CONTENT_FTS_INDEX_SQL)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_sops_content_fts")
    op.execute(_OLD_FTS_INDEX_SQL)
    op.drop_column('sops', 'title')
