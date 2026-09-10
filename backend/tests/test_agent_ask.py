import json

from app.agent.agent import answer_question
from tests.fakes import FakeLLMClient


def test_answer_question_parses_and_passes_guardrails(db_session, seed):
    seed()
    payload = json.dumps(
        {
            "answer": "Site build-out is visible.",
            "evidence_used": ["nur_navoi_solar_ev_0"],
            "confidence": "medium",
            "limitations": ["no ground truth"],
            "unsupported_claims_refused": [],
        }
    )
    fake = FakeLLMClient(response=payload)
    result = answer_question(db_session, fake, "nur_navoi_solar", "What changed?")
    assert result.answer.startswith("Site build-out")
    assert result.evidence_used == ["nur_navoi_solar_ev_0"]
    assert "Canopy" in (fake.last_system or "")
    assert "nur_navoi_solar_ev_0" in (fake.last_user or "")


def test_answer_question_falls_back_on_unparseable_output(db_session, seed):
    seed()
    fake = FakeLLMClient(response="not json at all")
    result = answer_question(db_session, fake, "nur_navoi_solar", "What changed?")
    assert result.answer == "not json at all"
    assert result.confidence == "low"
    assert result.evidence_used == []


def test_answer_question_drops_hallucinated_evidence_ids(db_session, seed):
    seed()
    payload = json.dumps({"answer": "x", "evidence_used": ["made_up_id"], "confidence": "low"})
    fake = FakeLLMClient(response=payload)
    result = answer_question(db_session, fake, "nur_navoi_solar", "q")
    assert result.evidence_used == []  # id not in retrieved context -> dropped


def test_answer_question_handles_non_object_json(db_session, seed):
    seed()
    fake = FakeLLMClient(response="[]")  # valid JSON, but a list not an object
    result = answer_question(db_session, fake, "nur_navoi_solar", "q")
    assert result.confidence == "low"
    assert result.evidence_used == []


def test_answer_question_coerces_non_list_fields(db_session, seed):
    seed()
    fake = FakeLLMClient(response=json.dumps({"answer": "x", "limitations": "none"}))
    result = answer_question(db_session, fake, "nur_navoi_solar", "q")
    assert result.answer == "x"
    assert result.limitations == []  # non-list value coerced, no ValidationError


def test_ask_requests_guaranteed_json_from_the_provider(db_session, seed):
    seed()
    client = FakeLLMClient(json.dumps({"answer": "ok", "confidence": "high"}))

    answer_question(db_session, client, "nur_navoi_solar", "is it built?")

    assert client.last_json_object is True


def test_ask_survives_the_wrappers_models_add_around_json(db_session, seed):
    """Even in JSON mode, providers fence or preface the object. A wrapper must not
    collapse a good answer into the unstructured fallback."""
    seed()
    body = {"answer": "Built to 238 ha.", "confidence": "high", "evidence_used": []}
    for raw in (
        json.dumps(body),
        f"```json\n{json.dumps(body)}\n```",
        f"```\n{json.dumps(body)}\n```",
        f"Here is the result:\n{json.dumps(body)}\nLet me know if you need more.",
    ):
        got = answer_question(db_session, FakeLLMClient(raw), "nur_navoi_solar", "q")
        assert got.answer == "Built to 238 ha.", raw[:40]
        assert got.confidence == "high"


def test_ask_falls_back_safely_when_the_reply_is_not_json(db_session, seed):
    seed()
    got = answer_question(
        db_session, FakeLLMClient("I cannot answer that."), "nur_navoi_solar", "q"
    )

    assert got.answer == "I cannot answer that."
    assert got.confidence == "low"
    assert got.limitations
