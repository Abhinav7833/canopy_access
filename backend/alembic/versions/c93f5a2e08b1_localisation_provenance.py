"""localisation provenance

Revision ID: c93f5a2e08b1
Revises: b6d40e17ca92
Create Date: 2026-07-23 15:10:00.000000

Records why a match won and how trustworthy the resulting AOI is.

`confidence` already held the match score; `margin` is the gap to the runner-up, which
is the sharper signal — a wide margin means an unambiguous match, a thin one means
look-alikes and a human should look. `matched_fields`, `gem_location_id` and
`reference_source` say which reference row won and on what.

`aoi_assurance` / `has_footprint` record whether the boundary is a digitised footprint
or a box drawn round a point. Every area figure downstream inherits that distinction,
so it belongs with the localisation rather than being implied by a polygon's existence.

Landing zone for `verify_disclosure()`'s `resolution` and `aoi` blocks.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c93f5a2e08b1'
down_revision: Union[str, Sequence[str], None] = 'b6d40e17ca92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('localizations', sa.Column('margin', sa.Float(), nullable=True))
    # NOT NULL with an empty-array default, matching the other list columns (drivers,
    # limitations): "no fields recorded" is an empty list, not an absent one.
    op.add_column(
        'localizations',
        sa.Column(
            'matched_fields',
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default='{}',
        ),
    )
    op.add_column('localizations', sa.Column('gem_location_id', sa.String(), nullable=True))
    op.add_column('localizations', sa.Column('reference_source', sa.String(), nullable=True))
    op.add_column('localizations', sa.Column('aoi_assurance', sa.String(), nullable=True))
    op.add_column('localizations', sa.Column('has_footprint', sa.Boolean(), nullable=True))


def downgrade() -> None:
    for col in ('has_footprint', 'aoi_assurance', 'reference_source', 'gem_location_id',
                'matched_fields', 'margin'):
        op.drop_column('localizations', col)
