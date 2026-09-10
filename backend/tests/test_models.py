from app.models import Claim, Confidence, EvidenceItem, Project


def test_project_dossier_roundtrip(db_session):
    db_session.add(Project(id="p1", name="Demo", asset_type="solar"))
    db_session.flush()  # project must exist before its FK-linked rows
    db_session.add(
        Claim(id="p1__area", project_id="p1", ordinal=0, kind="area_ha", promised_num=100)
    )
    db_session.add(
        Confidence(
            project_id="p1",
            on_track_pct=80,
            drivers=["footprint match", "on schedule"],
            risk_band="Low",
        )
    )
    db_session.add(
        EvidenceItem(
            id="p1_ev_0",
            project_id="p1",
            source_name="Sentinel-2",
            limitations=["proxy"],
            supporting_assets=["aoi_reference_rgb.png"],
        )
    )
    db_session.flush()

    assert db_session.get(Confidence, "p1").drivers == ["footprint match", "on schedule"]
    ev = db_session.get(EvidenceItem, "p1_ev_0")
    assert ev.project_id == "p1"
    assert ev.supporting_assets == ["aoi_reference_rgb.png"]
