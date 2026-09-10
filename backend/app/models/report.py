from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    report_type: Mapped[str] = mapped_column(String)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    evidence_ids_json: Mapped[list] = mapped_column(JSONB, default=list)
    content: Mapped[str | None] = mapped_column(String, nullable=True)
    report_uri: Mapped[str | None] = mapped_column(String, nullable=True)


class QaLog(Base):
    __tablename__ = "qa_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    question: Mapped[str] = mapped_column(String)
    answer: Mapped[str | None] = mapped_column(String, nullable=True)
    evidence_ids_json: Mapped[list] = mapped_column(JSONB, default=list)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
