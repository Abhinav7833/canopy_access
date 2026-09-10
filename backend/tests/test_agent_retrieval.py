from app.agent.retrieval import build_context


def test_context_includes_evidence_and_crosscheck(db_session, seed):
    seed()
    ctx = build_context(db_session, "nur_navoi_solar")
    assert ctx.evidence_ids
    assert ctx.evidence_ids[0] in ctx.text
    assert "CROSS-CHECK" in ctx.text
    assert "partially_consistent" in ctx.text


def test_allowed_evidence_ids_filters_context(db_session, seed):
    seed()
    full = build_context(db_session, "nur_navoi_solar")
    scoped = build_context(db_session, "nur_navoi_solar", allowed_evidence_ids=[])
    assert full.evidence_ids
    assert scoped.evidence_ids == []


def test_context_grounds_the_model_in_every_dossier_section(db_session, seed):
    """Regression guard: a dossier section the model never sees is a section the memo
    silently omits. Adding a section to the product means adding it here."""
    seed()
    text = build_context(db_session, "nur_navoi_solar").text

    for marker in (
        "DISCLOSURE:",  # who issued it, and under what instrument
        "LOCALIZATION:",  # where it is and how sure the match is
        "OBSERVATION ",
        "CROSS-CHECK ",
        "RISK-TO-ASSET",  # environment -> asset
        "IMPACT-ON-ENVIRONMENT",  # asset -> environment
        "IMPACT-DELIVERED",
        "LEGAL-CHECK ",
        "EVIDENCE ",
    ):
        assert marker in text, f"context is missing {marker!r}"


def test_context_labels_the_two_materiality_directions_distinctly(db_session, seed):
    seed()
    text = build_context(db_session, "nur_navoi_solar").text

    assert "environment -> asset" in text
    assert "asset -> environment" in text
    # An uncomputed hazard must not read as a safe one.
    assert "null means not yet computed, not zero risk" in text


def test_context_carries_the_unchecked_registers_verbatim(db_session, seed):
    """The model can only refuse to imply a clean result if it is told the check was
    never made — the verdict and the register both have to reach it."""
    seed()
    text = build_context(db_session, "nur_navoi_solar").text

    assert "verdict=insufficient_data" in text
    assert "no independent check has been performed" in text
    assert "OFAC SDN" in text
