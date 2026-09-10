"""cascade delete for reports and qa_logs

Revision ID: aa1f77c2e3b9
Revises: c93f5a2e08b1
Create Date: 2026-07-24 02:30:00.000000

`reports` and `qa_logs` are the only children of `projects` whose FK was created without
ON DELETE CASCADE. Once a memo or an Ask has run, a leftover row blocks deleting the project,
which breaks the idempotent reseed (`scripts/seed.py` deletes the project and relies on the
children cascading). Bring these two in line with every other child table.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "aa1f77c2e3b9"
down_revision: Union[str, Sequence[str], None] = "c93f5a2e08b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ("reports", "qa_logs")


def upgrade() -> None:
    for table in _TABLES:
        name = f"{table}_project_id_fkey"
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(
            name, table, "projects", ["project_id"], ["id"], ondelete="CASCADE"
        )


def downgrade() -> None:
    for table in _TABLES:
        name = f"{table}_project_id_fkey"
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(name, table, "projects", ["project_id"], ["id"])
