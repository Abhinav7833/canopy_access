from app.agent.prompts import SYSTEM_PROMPT, ask_user_message, memo_user_message


def test_system_prompt_encodes_guardrails():
    for phrase in ["only from", "cite the evidence", "human review", "investment advice"]:
        assert phrase.lower() in SYSTEM_PROMPT.lower()


def test_ask_message_embeds_question_and_context():
    msg = ask_user_message("What changed?", "EVIDENCE: ev_1 ...")
    assert "What changed?" in msg
    assert "ev_1" in msg
    assert "json" in msg.lower()


def test_memo_message_embeds_report_type_and_context():
    msg = memo_user_message("investment_monitoring", "EVIDENCE: ev_1 ...")
    assert "investment_monitoring" in msg
    assert "Executive Summary" in msg
