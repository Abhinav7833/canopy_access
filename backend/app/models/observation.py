from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    source_name: Mapped[str] = mapped_column(String)
    source_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    method_id: Mapped[str | None] = mapped_column(
        ForeignKey("methodologies.id", ondelete="RESTRICT"), nullable=True
    )
    confidence: Mapped[str | None] = mapped_column(String, nullable=True)
    limitations: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    financial_relevance: Mapped[str | None] = mapped_column(String, nullable=True)
    supporting_assets: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
