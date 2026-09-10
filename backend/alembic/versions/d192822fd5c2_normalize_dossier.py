"""normalize dossier

Revision ID: d192822fd5c2
Revises: 9892b45283a0
Create Date: 2026-07-17 15:13:09.968936

Normalize the dossier into typed relational tables (single source of truth):
drop the old observations/metrics/risk_scores model, re-parent evidence_items to
projects, and add the eight dossier tables. Data is reseeded, so tables whose
shape changes are dropped and recreated rather than altered in place.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "d192822fd5c2"
down_revision: Union[str, Sequence[str], None] = "9892b45283a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def _trace_cols() -> list[sa.Column]:
    """Fresh trace value-object columns (a Column can belong to only one table)."""
    return [
        sa.Column("trace_source", sa.String(), nullable=True),
        sa.Column("trace_date", sa.Date(), nullable=True),
        sa.Column("trace_method", sa.String(), nullable=True),
        sa.Column("trace_confidence", sa.String(), nullable=True),
        sa.Column("trace_traces_to", sa.String(), nullable=True),
    ]


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


def upgrade() -> None:
    # 1. Drop the old evidence/observation/risk model (superseded; reseeded).
    op.drop_table("metrics")
    op.drop_table("evidence_items")
    op.drop_table("observations")
    op.drop_table("risk_scores")

    # 2. projects: drop the duplicated scalars (now live only in `confidences`).
    op.drop_column("projects", "risk_score")
    op.drop_column("projects", "risk_band")
    op.drop_column("projects", "confidence")
    op.drop_column("projects", "main_finding")

    # 3. project_boundaries: FK gains ON DELETE CASCADE.
    op.drop_constraint(op.f("project_boundaries_project_id_fkey"), "project_boundaries", type_="foreignkey")
    op.create_foreign_key(
        "project_boundaries_project_id_fkey", "project_boundaries", "projects",
        ["project_id"], ["id"], ondelete="CASCADE",
    )

    # 4. methodologies: JSONB list columns -> ARRAY(String). Emptied (reseeded) so the
    #    NOT NULL columns can be re-added without a server default.
    op.execute("DELETE FROM methodologies")
    for col in ("data_sources", "assumptions", "limitations"):
        op.drop_column("methodologies", col)
        op.add_column("methodologies", sa.Column(col, postgresql.ARRAY(sa.String()), nullable=False))

    # 5. evidence_items, re-parented to projects with typed columns.
    op.create_table(
        "evidence_items",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("source_name", sa.String(), nullable=False),
        sa.Column("source_date", sa.Date(), nullable=True),
        sa.Column("method_id", sa.String(), nullable=True),
        sa.Column("confidence", sa.String(), nullable=True),
        sa.Column("limitations", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("financial_relevance", sa.String(), nullable=True),
        sa.Column("supporting_assets", postgresql.ARRAY(sa.String()), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["method_id"], ["methodologies.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 6. The dossier sections.
    op.create_table(
        "disclosures",
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("issuer", sa.String(), nullable=True),
        sa.Column("instrument", sa.String(), nullable=True),
        sa.Column("financing_date", sa.Date(), nullable=True),
        sa.Column("doc_ref", sa.String(), nullable=True),
        sa.Column("region_hint", sa.String(), nullable=True),
        sa.Column("summary", sa.String(), nullable=True),
        _created_at(),
        *_trace_cols(),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id"),
    )
    op.create_table(
        "claims",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("promised_num", sa.Numeric(), nullable=True),
        sa.Column("promised_text", sa.String(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("source_span", sa.String(), nullable=True),
        _created_at(),
        *_trace_cols(),
        sa.CheckConstraint("(promised_num IS NULL) <> (promised_text IS NULL)", name="ck_claim_promised_one_of"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "localizations",
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("region_hint", sa.String(), nullable=True),
        sa.Column("centroid_lon", sa.Float(), nullable=False),
        sa.Column("centroid_lat", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("method", sa.String(), nullable=True),
        _created_at(),
        *_trace_cols(),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id"),
    )
    op.create_table(
        "localization_alternatives",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["localizations.project_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "observation_snapshots",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("image_key", sa.String(), nullable=False),
        sa.Column("footprint_ha", sa.Float(), nullable=True),
        sa.Column("ndvi", sa.Float(), nullable=True),
        sa.Column("note", sa.String(), nullable=True),
        _created_at(),
        *_trace_cols(),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cross_checks",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("claim_id", sa.String(), nullable=False),
        sa.Column("observed_num", sa.Numeric(), nullable=True),
        sa.Column("observed_text", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("variance", sa.String(), nullable=True),
        _created_at(),
        *_trace_cols(),
        sa.CheckConstraint("(observed_num IS NULL) <> (observed_text IS NULL)", name="ck_crosscheck_observed_one_of"),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cross_check_evidence",
        sa.Column("cross_check_id", sa.String(), nullable=False),
        sa.Column("evidence_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["cross_check_id"], ["cross_checks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("cross_check_id", "evidence_id"),
    )
    op.create_table(
        "confidences",
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("on_track_pct", sa.Integer(), nullable=False),
        sa.Column("rationale", sa.String(), nullable=True),
        sa.Column("drivers", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("risk_band", sa.String(), nullable=True),
        _created_at(),
        *_trace_cols(),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id"),
    )


def downgrade() -> None:
    # Reverse to the init schema (recreate the old model, drop the dossier tables).
    op.drop_table("confidences")
    op.drop_table("cross_check_evidence")
    op.drop_table("cross_checks")
    op.drop_table("observation_snapshots")
    op.drop_table("localization_alternatives")
    op.drop_table("localizations")
    op.drop_table("claims")
    op.drop_table("disclosures")
    op.drop_table("evidence_items")

    op.execute("DELETE FROM methodologies")
    for col in ("data_sources", "assumptions", "limitations"):
        op.drop_column("methodologies", col)
        op.add_column("methodologies", sa.Column(col, postgresql.JSONB(astext_type=sa.Text()), nullable=False))

    op.drop_constraint("project_boundaries_project_id_fkey", "project_boundaries", type_="foreignkey")
    op.create_foreign_key(
        op.f("project_boundaries_project_id_fkey"), "project_boundaries", "projects", ["project_id"], ["id"]
    )

    op.add_column("projects", sa.Column("main_finding", sa.String(), nullable=True))
    op.add_column("projects", sa.Column("confidence", sa.Float(), nullable=True))
    op.add_column("projects", sa.Column("risk_band", sa.String(), nullable=True))
    op.add_column("projects", sa.Column("risk_score", sa.Integer(), nullable=True))

    op.create_table(
        "observations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("observation_type", sa.String(), nullable=False),
        sa.Column("period_start", sa.String(), nullable=True),
        sa.Column("period_end", sa.String(), nullable=True),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "risk_scores",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("score_type", sa.String(), nullable=False),
        sa.Column("score_value", sa.Integer(), nullable=True),
        sa.Column("score_band", sa.String(), nullable=True),
        sa.Column("drivers_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "evidence_items",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("observation_id", sa.String(), nullable=False),
        sa.Column("source_name", sa.String(), nullable=False),
        sa.Column("source_date", sa.String(), nullable=True),
        sa.Column("method_id", sa.String(), nullable=True),
        sa.Column("confidence", sa.String(), nullable=True),
        sa.Column("limitations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("financial_relevance", sa.String(), nullable=True),
        sa.Column("supporting_assets", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["observation_id"], ["observations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "metrics",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("observation_id", sa.String(), nullable=False),
        sa.Column("metric_name", sa.String(), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("baseline_value", sa.Float(), nullable=True),
        sa.Column("comparison_value", sa.Float(), nullable=True),
        sa.Column("method_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["observation_id"], ["observations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
