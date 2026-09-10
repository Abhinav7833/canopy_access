from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.dossier import (
        Claim,
        Confidence,
        CrossCheck,
        Disclosure,
        Localization,
        ObservationSnapshot,
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    asset_type: Mapped[str] = mapped_column(String)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    financing_type: Mapped[str | None] = mapped_column(String, nullable=True)
    monitoring_objective: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="monitored")
    screening_status: Mapped[str | None] = mapped_column(String, nullable=True)

    boundary: Mapped["ProjectBoundary"] = relationship(back_populates="project", uselist=False)
    disclosure: Mapped["Disclosure"] = relationship(cascade="all, delete-orphan", uselist=False)
    localization: Mapped["Localization"] = relationship(cascade="all, delete-orphan", uselist=False)
    confidence_row: Mapped["Confidence"] = relationship(cascade="all, delete-orphan", uselist=False)
    claims: Mapped[list["Claim"]] = relationship(
        cascade="all, delete-orphan", order_by="Claim.ordinal"
    )
    snapshots: Mapped[list["ObservationSnapshot"]] = relationship(
        cascade="all, delete-orphan", order_by="ObservationSnapshot.ordinal"
    )
    cross_checks: Mapped[list["CrossCheck"]] = relationship(
        cascade="all, delete-orphan", order_by="CrossCheck.ordinal"
    )


class ProjectBoundary(Base):
    __tablename__ = "project_boundaries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    geom: Mapped[object] = mapped_column(Geometry("POLYGON", srid=4326))
    crs: Mapped[str] = mapped_column(String, default="EPSG:4326")
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    area_hectares: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_status: Mapped[str] = mapped_column(String, default="demo")

    project: Mapped[Project] = relationship(back_populates="boundary")
