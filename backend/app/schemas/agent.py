from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    question: str
    allowed_evidence_ids: list[str] | None = None


class AskResponse(BaseModel):
    answer: str
    evidence_used: list[str] = []
    confidence: str = "low"
    limitations: list[str] = []
    unsupported_claims_refused: list[str] = []


class ReportRequest(BaseModel):
    report_type: str = "investment_monitoring"


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    report_type: str
    content: str | None = None
    evidence_ids: list[str] = Field(default=[], validation_alias="evidence_ids_json")
    generated_at: datetime
