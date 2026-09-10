"""cross check verdict vocabulary

Revision ID: e8b3c05a91d4
Revises: c4e9d2b71a35
Create Date: 2026-07-22 14:05:00.000000

Adopts the pipeline spec's verdict vocabulary (`consistent`, `partially_consistent`,
`inconsistent`, `insufficient_data`) in place of the earlier `met` / `on_track` wording,
and constrains the column to it. Existing rows are translated rather than dropped: `met`
became `consistent`, and `on_track` described a check whose proxy agreed while the claim
itself stayed unverified, which is `partially_consistent`.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8b3c05a91d4'
down_revision: Union[str, Sequence[str], None] = 'c4e9d2b71a35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Spelled out rather than imported from app.core.vocabulary: a migration is a snapshot of
# history, and must keep doing what it did even after the live vocabulary moves on.
_ALLOWED = ("consistent", "partially_consistent", "inconsistent", "insufficient_data")
_TRANSLATION = {"met": "consistent", "on_track": "partially_consistent"}
_CONSTRAINT = "ck_crosscheck_status_vocabulary"


def upgrade() -> None:
    for old, new in _TRANSLATION.items():
        op.execute(
            sa.text("UPDATE cross_checks SET status = :new WHERE status = :old").bindparams(
                old=old, new=new
            )
        )
    allowed = ", ".join(f"'{s}'" for s in _ALLOWED)
    op.create_check_constraint(_CONSTRAINT, "cross_checks", f"status IN ({allowed})")


def downgrade() -> None:
    # Lossy by nature: a verdict written as `consistent` after this migration cannot be told
    # apart from one translated up from `met`, so both go back as `met`.
    op.drop_constraint(_CONSTRAINT, "cross_checks", type_="check")
    for old, new in _TRANSLATION.items():
        op.execute(
            sa.text("UPDATE cross_checks SET status = :old WHERE status = :new").bindparams(
                old=old, new=new
            )
        )
