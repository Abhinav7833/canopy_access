import json
import re

from sqlalchemy.orm import Session

from app.agent.client import LLMClient
from app.agent.prompts import SYSTEM_PROMPT, ask_user_message, memo_user_message
from app.agent.retrieval import build_context
from app.schemas.agent import AskResponse


def _as_list(value: object) -> list[str]:
    return [str(v) for v in value] if isinstance(value, list) else []


def _parse_json_object(raw: object) -> dict | None:
    """Parse the model's reply into an object, tolerating the two things models reliably do
    even when asked for bare JSON: wrap it in a ```json fence, or add prose around it."""
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            data = json.loads(text[start : end + 1])
        except (json.JSONDecodeError, TypeError):
            return None
    return data if isinstance(data, dict) else None


def answer_question(
    db: Session,
    client: LLMClient,
    project_id: str,
    question: str,
    allowed_evidence_ids: list[str] | None = None,
) -> AskResponse:
    ctx = build_context(db, project_id, allowed_evidence_ids)
    raw = client.complete(SYSTEM_PROMPT, ask_user_message(question, ctx.text), json_object=True)
    data = _parse_json_object(raw)
    if data is None:
        return AskResponse(
            answer=raw if isinstance(raw, str) else str(raw),
            confidence="low",
            limitations=["The assistant response was not structured; treat with caution."],
        )
    confidence = data.get("confidence", "low")
    return AskResponse(
        answer=str(data.get("answer", "")),
        evidence_used=[e for e in _as_list(data.get("evidence_used")) if e in ctx.evidence_ids],
        confidence=confidence if isinstance(confidence, str) else "low",
        limitations=_as_list(data.get("limitations")),
        unsupported_claims_refused=_as_list(data.get("unsupported_claims_refused")),
    )


def generate_memo(
    db: Session, client: LLMClient, project_id: str, report_type: str
) -> tuple[str, list[str]]:
    ctx = build_context(db, project_id)
    content = client.complete(SYSTEM_PROMPT, memo_user_message(report_type, ctx.text))
    return content, ctx.evidence_ids
