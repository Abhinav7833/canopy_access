from datetime import date

from pydantic import BaseModel, ConfigDict


class EvidenceItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    source_name: str
    source_date: date | None = None
    method_id: str | None = None
    confidence: str | None = None
    limitations: list[str] = []
    financial_relevance: str | None = None
    supporting_assets: list[str] = []
