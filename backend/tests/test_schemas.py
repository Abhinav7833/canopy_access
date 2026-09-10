import pytest
from pydantic import ValidationError

from app.schemas.project import Dossier, ProjectSummary


def _valid_dossier_payload() -> dict:
    """A minimal well-formed dossier, mirroring what `get_dossier` assembles."""
    trace = {
        "source": "doc.pdf",
        "date": "2021-03-15",
        "method": "stub",
        "confidence": "high",
        "traces_to": "disclosure",
    }
    return {
        "project_id": "demo",
        "disclosure": {"title": "Demo disclosure", "trace": trace},
        "claims": [{"id": "demo__c1", "kind": "capacity_mw", "promised": 590.0, "trace": trace}],
        "localization": {"located_centroid": [-5.6875, 39.5], "trace": trace},
        # No image_key: a dated observation the pipeline holds no capture for.
        "observation_series": [{"date": "2020-06-15", "trace": trace}],
        "cross_check": [
            {"claim_id": "demo__c1", "observed": "matches", "status": "consistent", "trace": trace}
        ],
        "confidence": {"on_track_pct": 87, "trace": trace},
        "memo_ready": True,
    }


def test_dossier_accepts_well_formed_payload():
    """The typed contract round-trips the assembled shape and reconstructs the unions."""
    d = Dossier.model_validate(_valid_dossier_payload())
    assert d.claims[0].promised == 590.0
    assert d.localization.located_centroid == (-5.6875, 39.5)
    assert d.confidence.on_track_pct == 87


def test_dossier_rejects_wrongly_typed_field():
    """Validation now bites: a non-numeric on_track_pct is rejected (was pass-through before)."""
    payload = _valid_dossier_payload()
    payload["confidence"]["on_track_pct"] = "not-a-number"
    with pytest.raises(ValidationError):
        Dossier.model_validate(payload)


def test_dossier_rejects_malformed_centroid():
    """located_centroid is a typed 2-tuple of floats, not a free-form value."""
    payload = _valid_dossier_payload()
    payload["localization"]["located_centroid"] = "somewhere"
    with pytest.raises(ValidationError):
        Dossier.model_validate(payload)


def test_project_summary_from_derived_dict():
    """The projects service builds summaries from dicts with risk derived from `confidences`."""
    out = ProjectSummary.model_validate(
        {
            "id": "p1",
            "name": "Demo",
            "asset_type": "solar",
            "status": "monitored",
            "risk_score": 61,
            "risk_band": "High",
        }
    )
    assert out.id == "p1"
    assert out.risk_score == 61
    assert out.risk_band == "High"
