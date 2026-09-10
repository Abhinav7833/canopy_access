from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Methodology(Base):
    __tablename__ = "methodologies"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    method_id: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    data_sources: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    assumptions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    limitations: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    version: Mapped[str] = mapped_column(String, default="v1")
