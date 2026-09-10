"""nullable snapshot image key

Revision ID: c4e9d2b71a35
Revises: a7c31f04b8e2
Create Date: 2026-07-22 13:40:00.000000

A dated observation and a stored image are separate facts. Until a dated capture
backs a snapshot there is no honest key to put here, and the previous NOT NULL
forced every snapshot to point at whatever frame happened to be on disk. The
imagery a project does hold is served from `/imagery`, with its provenance taken
from the evidence card that supplies it.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e9d2b71a35'
down_revision: Union[str, Sequence[str], None] = 'a7c31f04b8e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('observation_snapshots', 'image_key', existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    op.execute("DELETE FROM observation_snapshots WHERE image_key IS NULL")
    op.alter_column('observation_snapshots', 'image_key', existing_type=sa.String(), nullable=False)
