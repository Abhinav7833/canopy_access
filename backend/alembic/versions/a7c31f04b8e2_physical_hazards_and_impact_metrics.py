"""physical hazards and impact metrics

Revision ID: a7c31f04b8e2
Revises: 155076e65424
Create Date: 2026-07-22 13:35:00.000000

Catch-up migration for the two dossier tables added with the metrics feature
(`physical_hazards`, `impact_metrics`). They were created on the development
database out-of-band, so `alembic upgrade head` on a fresh database stopped
producing a schema the seeder could write to. Both are per-project extensions
keyed on `projects.id`, all measures nullable so one `impact_metrics` row fits
either asset type (solar carries generation, mangrove carries carbon stock).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c31f04b8e2'
down_revision: Union[str, Sequence[str], None] = '155076e65424'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'physical_hazards',
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('fire_score', sa.Integer(), nullable=True),
        sa.Column('fire_band', sa.String(), nullable=True),
        sa.Column('flood_score', sa.Integer(), nullable=True),
        sa.Column('flood_band', sa.String(), nullable=True),
        sa.Column('degradation_score', sa.Integer(), nullable=True),
        sa.Column('degradation_band', sa.String(), nullable=True),
        sa.Column('composite_score', sa.Integer(), nullable=True),
        sa.Column('composite_band', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('project_id'),
    )
    op.create_table(
        'impact_metrics',
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('generation_gwh', sa.Float(), nullable=True),
        sa.Column('avoided_emissions_tco2', sa.Float(), nullable=True),
        sa.Column('carbon_stock_tco2', sa.Float(), nullable=True),
        sa.Column('carbon_band', sa.String(), nullable=True),
        sa.Column('assurance', sa.String(), nullable=True),
        sa.Column('co2_intensity_value', sa.Float(), nullable=True),
        sa.Column('co2_intensity_unit', sa.String(), nullable=True),
        sa.Column('build_year', sa.Integer(), nullable=True),
        sa.Column('financing_year', sa.Integer(), nullable=True),
        sa.Column('additionality_verdict', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('project_id'),
    )


def downgrade() -> None:
    op.drop_table('impact_metrics')
    op.drop_table('physical_hazards')
