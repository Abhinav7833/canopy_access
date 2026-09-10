"""legal checks

Revision ID: b6d40e17ca92
Revises: f2a71c93d5e8
Create Date: 2026-07-23 14:50:00.000000

Adds the legal and regulatory cross-reference: permits, sanctions screening,
litigation and ownership of record.

Constrained to the same verdict vocabulary as a claim cross-check, because that is
what it is — an unreachable register records `insufficient_data`, never a reassuring
`consistent`. `authority` and `as_of` are stored alongside the verdict since "no hits"
is unreadable without naming the register and the date it reflects.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6d40e17ca92'
down_revision: Union[str, Sequence[str], None] = 'f2a71c93d5e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Spelled out rather than imported: a migration is a snapshot of history.
_VERDICTS = ("consistent", "partially_consistent", "inconsistent", "insufficient_data")
_TYPES = ("permit", "sanction", "litigation", "ownership")


def upgrade() -> None:
    op.create_table(
        'legal_checks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('ordinal', sa.Integer(), nullable=False),
        sa.Column('check_type', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('verdict', sa.String(), nullable=False),
        sa.Column('detail', sa.String(), nullable=True),
        sa.Column('authority', sa.String(), nullable=True),
        sa.Column('as_of', sa.Date(), nullable=True),
        sa.Column('reference', sa.String(), nullable=True),
        sa.Column('trace_source', sa.String(), nullable=True),
        sa.Column('trace_date', sa.Date(), nullable=True),
        sa.Column('trace_method', sa.String(), nullable=True),
        sa.Column('trace_confidence', sa.String(), nullable=True),
        sa.Column('trace_traces_to', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "verdict IN ({})".format(", ".join(f"'{v}'" for v in _VERDICTS)),
            name='ck_legalcheck_verdict_vocabulary',
        ),
        sa.CheckConstraint(
            "check_type IN ({})".format(", ".join(f"'{t}'" for t in _TYPES)),
            name='ck_legalcheck_type_vocabulary',
        ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_legal_checks_project_id'), 'legal_checks', ['project_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_legal_checks_project_id'), table_name='legal_checks')
    op.drop_table('legal_checks')
