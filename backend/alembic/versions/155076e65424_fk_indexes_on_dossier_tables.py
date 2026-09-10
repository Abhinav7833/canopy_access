"""fk indexes on dossier tables

Revision ID: 155076e65424
Revises: d192822fd5c2
Create Date: 2026-07-19 21:45:07.070551

Index the foreign-key columns the dossier assembly filters on. Each section is
fetched with `WHERE <fk> = <project/claim id>`; without these indexes every
dossier read seq-scans the child tables. `cross_check_evidence` already has a PK
on `(cross_check_id, evidence_id)` (covering `cross_check_id`), so only the
`evidence_id` leg needs its own index.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '155076e65424'
down_revision: Union[str, Sequence[str], None] = 'd192822fd5c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f('ix_claims_project_id'), 'claims', ['project_id'], unique=False)
    op.create_index(op.f('ix_cross_check_evidence_evidence_id'), 'cross_check_evidence', ['evidence_id'], unique=False)
    op.create_index(op.f('ix_cross_checks_claim_id'), 'cross_checks', ['claim_id'], unique=False)
    op.create_index(op.f('ix_cross_checks_project_id'), 'cross_checks', ['project_id'], unique=False)
    op.create_index(op.f('ix_evidence_items_project_id'), 'evidence_items', ['project_id'], unique=False)
    op.create_index(op.f('ix_localization_alternatives_project_id'), 'localization_alternatives', ['project_id'], unique=False)
    op.create_index(op.f('ix_observation_snapshots_project_id'), 'observation_snapshots', ['project_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_observation_snapshots_project_id'), table_name='observation_snapshots')
    op.drop_index(op.f('ix_localization_alternatives_project_id'), table_name='localization_alternatives')
    op.drop_index(op.f('ix_evidence_items_project_id'), table_name='evidence_items')
    op.drop_index(op.f('ix_cross_checks_project_id'), table_name='cross_checks')
    op.drop_index(op.f('ix_cross_checks_claim_id'), table_name='cross_checks')
    op.drop_index(op.f('ix_cross_check_evidence_evidence_id'), table_name='cross_check_evidence')
    op.drop_index(op.f('ix_claims_project_id'), table_name='claims')
