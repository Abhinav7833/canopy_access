"""split double materiality

Revision ID: f2a71c93d5e8
Revises: e8b3c05a91d4
Create Date: 2026-07-23 14:30:00.000000

Separates the two directions of materiality, which `physical_hazards` had merged.

`fire` and `flood` measure what the environment does to the asset (financial
materiality). `degradation` measures what the asset does to the environment (impact
materiality). Scoring them together — and taking the worst of all three as one
composite — produced a number that rises in both cases, so a reader could not tell an
endangered asset from a harmful one.

Vegetation loss therefore moves to a new `environmental_effects` table, taking its
score and band with it, and each side keeps its own composite. `physical_hazards`
gains heat and water-stress slots (named in the product but not yet computed) plus the
derivation columns from `risk_scoring.score()`, so a hazard score can be interrogated.
Existing composites are recomputed as the worst remaining hazard.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2a71c93d5e8'
down_revision: Union[str, Sequence[str], None] = 'e8b3c05a91d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_BAND = (
    "CASE WHEN {c} IS NULL THEN NULL WHEN {c} < 25 THEN 'Low' WHEN {c} < 50 THEN 'Medium' "
    "WHEN {c} < 75 THEN 'High' ELSE 'Critical' END"
)


def upgrade() -> None:
    op.create_table(
        'environmental_effects',
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('vegetation_loss_score', sa.Integer(), nullable=True),
        sa.Column('vegetation_loss_band', sa.String(), nullable=True),
        sa.Column('vegetation_change_pct', sa.Float(), nullable=True),
        sa.Column('deforestation_detected', sa.Boolean(), nullable=True),
        sa.Column('water_change_pct', sa.Float(), nullable=True),
        sa.Column('land_disturbance_ha', sa.Float(), nullable=True),
        sa.Column('community_exposure_built_up', sa.Float(), nullable=True),
        sa.Column('composite_score', sa.Integer(), nullable=True),
        sa.Column('composite_band', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('project_id'),
    )
    # Carry vegetation loss across rather than dropping it: it is a real measurement,
    # only filed under the wrong direction.
    op.execute(
        """
        INSERT INTO environmental_effects
            (project_id, vegetation_loss_score, vegetation_loss_band,
             vegetation_change_pct, composite_score, composite_band)
        SELECT project_id, degradation_score, degradation_band,
               degradation_score, degradation_score, degradation_band
        FROM physical_hazards
        """
    )

    for col, type_ in (
        ('heat_score', sa.Integer()), ('water_stress_score', sa.Integer()),
        ('fire_ffwi', sa.Float()), ('fire_dnbr', sa.Float()),
        ('flood_depth_100yr_m', sa.Float()), ('flood_damage_frac', sa.Float()),
        ('flood_observed_frac', sa.Float()), ('asset_exposure', sa.Float()),
    ):
        op.add_column('physical_hazards', sa.Column(col, type_, nullable=True))
    for col in ('heat_band', 'water_stress_band', 'fire_severity_class'):
        op.add_column('physical_hazards', sa.Column(col, sa.String(), nullable=True))

    op.drop_column('physical_hazards', 'degradation_score')
    op.drop_column('physical_hazards', 'degradation_band')

    # The composite may have been driven by the score that just left; recompute it as the
    # worst remaining hazard so it means "danger to the asset" and nothing else.
    op.execute(
        "UPDATE physical_hazards SET composite_score = GREATEST("
        "COALESCE(fire_score, 0), COALESCE(flood_score, 0))"
    )
    op.execute(f"UPDATE physical_hazards SET composite_band = {_BAND.format(c='composite_score')}")


def downgrade() -> None:
    op.add_column('physical_hazards', sa.Column('degradation_score', sa.Integer(), nullable=True))
    op.add_column('physical_hazards', sa.Column('degradation_band', sa.String(), nullable=True))
    op.execute(
        """
        UPDATE physical_hazards h
        SET degradation_score = e.vegetation_loss_score,
            degradation_band  = e.vegetation_loss_band
        FROM environmental_effects e
        WHERE e.project_id = h.project_id
        """
    )
    op.execute(
        "UPDATE physical_hazards SET composite_score = GREATEST("
        "COALESCE(fire_score, 0), COALESCE(flood_score, 0), COALESCE(degradation_score, 0))"
    )
    op.execute(f"UPDATE physical_hazards SET composite_band = {_BAND.format(c='composite_score')}")

    for col in ('heat_score', 'heat_band', 'water_stress_score', 'water_stress_band',
                'fire_ffwi', 'fire_dnbr', 'fire_severity_class', 'flood_depth_100yr_m',
                'flood_damage_frac', 'flood_observed_frac', 'asset_exposure'):
        op.drop_column('physical_hazards', col)
    op.drop_table('environmental_effects')
