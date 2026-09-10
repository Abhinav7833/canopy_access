import json
from pathlib import Path

import pytest
from scripts import seed as seed_module
from scripts.seed import _seed_methodologies, seed_project

from app.core.storage import LocalStorage
from app.models import Claim, Confidence, CrossCheck, EvidenceItem, Project

FIXTURE = Path(__file__).resolve().parents[2] / "seed_data" / "projects" / "nur_navoi_solar.json"

DATED_CAPTURE = "dated_2021_09_rgb.png"


@pytest.fixture
def asset_fixture(tmp_path, monkeypatch):
    """A fixture referencing the AOI reference frame plus one asset only a real pipeline
    could deliver, over a throwaway asset store."""
    monkeypatch.setattr(seed_module, "get_storage", lambda: LocalStorage(tmp_path, "/static"))
    return {
        "id": "p1",
        "aoi_coords": [[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [0.0, 0.0]],
        "evidence": [{"supporting_assets": [seed_module.AOI_REFERENCE_ASSET, DATED_CAPTURE]}],
    }


def test_seed_populates_normalized_dossier(db_session):
    _seed_methodologies(db_session)
    pid = seed_project(db_session, json.loads(FIXTURE.read_text()))
    assert db_session.get(Project, pid) is not None
    assert db_session.query(Claim).filter_by(project_id=pid).count() == 5
    assert db_session.query(CrossCheck).filter_by(project_id=pid).count() >= 1
    assert db_session.get(Confidence, pid).on_track_pct > 0
    assert db_session.query(EvidenceItem).filter_by(project_id=pid).count() >= 1


def test_seed_rejects_a_verdict_outside_the_spec_vocabulary(db_session):
    """The seeder is the ingestion gate: an off-vocabulary verdict never reaches the DB."""
    _seed_methodologies(db_session)
    fx = json.loads(FIXTURE.read_text())
    fx["cross_check"][0]["status"] = "met"  # the pre-spec wording

    with pytest.raises(ValueError, match="not one of"):
        seed_project(db_session, fx)


def test_seed_rejects_a_hazard_composite_that_absorbs_an_effect_score(db_session):
    """The ingestion gate refuses a fixture that quietly undoes the materiality split."""
    _seed_methodologies(db_session)
    fx = json.loads(FIXTURE.read_text())
    # Worst hazard is fire=15; claim a composite driven by something else entirely.
    fx["metrics"]["physical_risk"]["composite"] = {"score": 80, "band": "Critical"}

    with pytest.raises(ValueError, match="must be the worst hazard"):
        seed_project(db_session, fx)


def test_headline_risk_is_the_hazard_composite_not_a_second_authored_number(db_session):
    _seed_methodologies(db_session)
    fx = json.loads(FIXTURE.read_text())
    pid = seed_project(db_session, fx)

    conf = db_session.get(Confidence, pid)
    composite = fx["metrics"]["physical_risk"]["composite"]
    assert (conf.risk_score, conf.risk_band) == (composite["score"], composite["band"])


def test_seed_rejects_an_unknown_legal_check_type(db_session):
    _seed_methodologies(db_session)
    fx = json.loads(FIXTURE.read_text())
    fx["legal_checks"][0]["check_type"] = "vibes"

    with pytest.raises(ValueError, match="not one of"):
        seed_project(db_session, fx)


def test_ensure_assets_stores_the_fetched_frame_only_under_the_reference_key(
    tmp_path, monkeypatch, asset_fixture
):
    """Regression guard: one AOI fetch must never be written under a second asset name.

    Copying a single frame to `before_rgb.png` and `after_rgb.png` is what let the product
    present two byte-identical images as an observed change.
    """
    monkeypatch.setattr(seed_module, "fetch_aoi_imagery", lambda coords: b"\x89PNG-real-bytes")

    missing = seed_module.ensure_assets(asset_fixture)

    assert missing == [DATED_CAPTURE]
    stored = sorted(p.name for p in (tmp_path / "p1").iterdir())
    assert stored == [seed_module.AOI_REFERENCE_ASSET]


def test_ensure_assets_fabricates_nothing_when_the_fetch_fails(
    tmp_path, monkeypatch, asset_fixture
):
    monkeypatch.setattr(seed_module, "fetch_aoi_imagery", lambda coords: None)

    missing = seed_module.ensure_assets(asset_fixture)

    assert missing == [seed_module.AOI_REFERENCE_ASSET, DATED_CAPTURE]
    assert list(tmp_path.rglob("*.png")) == []
