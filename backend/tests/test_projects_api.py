def test_list_and_detail(client, seed):
    seed()
    assert client.get("/projects").json()[0]["id"] == "nur_navoi_solar"
    detail = client.get("/projects/nur_navoi_solar").json()
    assert detail["risk_band"] == "Low"


def test_detail_404(client):
    body = client.get("/projects/missing").json()
    assert body["error"]["code"] == "not_found"


def test_boundary_is_geojson(client, seed):
    seed()
    feat = client.get("/projects/nur_navoi_solar/boundary").json()
    assert feat["type"] == "Feature"
    assert feat["geometry"]["type"] == "Polygon"


def test_boundary_404_names_the_project(client):
    body = client.get("/projects/missing/boundary").json()
    assert body["error"]["code"] == "not_found"
    assert "project" in body["error"]["message"]


def test_imagery_layers(client, seed):
    seed()
    layers = client.get("/projects/nur_navoi_solar/imagery").json()["layers"]
    assert any(layer["kind"] == "rgb" for layer in layers)


def test_legal_checks_name_their_register_and_never_imply_a_clean_result(client, seed):
    """An unrun check must read `insufficient_data`, not a reassuring `consistent`."""
    seed()
    checks = client.get("/projects/nur_navoi_solar/dossier").json()["legal_checks"]

    assert {c["check_type"] for c in checks} == {"permit", "sanction", "litigation", "ownership"}
    for c in checks:
        assert c["authority"], f"{c['check_type']} states a verdict without naming a register"
        # Nothing claims a clean external result: no register is connected yet.
        assert c["verdict"] != "consistent"


def test_dossier_keeps_the_two_materiality_directions_apart(client, seed):
    """The wire contract offers no field in which the two directions could be merged."""
    seed()
    d = client.get("/projects/nur_navoi_solar/dossier").json()

    hazards, effects = d["physical_risk"], d["environmental_effect"]
    assert set(hazards) & {"degradation", "vegetation_loss"} == set()
    assert effects["vegetation_loss"]["score"] is not None
    # The risk-to-asset composite is the worst hazard, never the harm the asset causes.
    assert hazards["composite"]["score"] == max(hazards["fire"]["score"], hazards["flood"]["score"])
    assert effects["composite"]["score"] == effects["vegetation_loss"]["score"]


def test_imagery_layer_carries_the_provenance_of_the_evidence_supplying_it(client, seed):
    seed()
    layers = client.get("/projects/nur_navoi_solar/imagery").json()["layers"]
    (reference,) = [layer for layer in layers if layer["key"] == "aoi_reference_rgb.png"]
    assert reference["source"] == "Esri World Imagery"
    assert reference["date"] is None  # an undated reference frame, not a dated capture


def test_every_snapshot_capture_resolves_to_a_served_layer(client, seed):
    """A snapshot may hold no capture, but one it names must be an image the API serves."""
    seed()
    layers = client.get("/projects/nur_navoi_solar/imagery").json()["layers"]
    served = {layer["key"] for layer in layers}
    series = client.get("/projects/nur_navoi_solar/dossier").json()["observation_series"]
    assert series
    unresolved = [s["image_key"] for s in series if s["image_key"] and s["image_key"] not in served]
    assert unresolved == []


def test_dossier_assembled_from_tables(client, seed):
    seed()  # nur_navoi_solar
    d = client.get("/projects/nur_navoi_solar/dossier").json()
    assert d["project_id"] == "nur_navoi_solar"
    assert d["disclosure"]["issuer"]
    assert [c["kind"] for c in d["claims"]] == [
        "capacity_mw",
        "generation_gwh",
        "co2_avoided_tpy",
        "area_ha",
        "cod_date",
    ]
    assert d["claims"][0]["promised"] == 100  # reconstructed from promised_num
    assert d["cross_check"][0]["evidence_ids"]  # reconstructed from the join table
    assert isinstance(d["confidence"]["drivers"], list)
    assert d["confidence"]["risk_band"] == "Low"
    assert d["memo_ready"] is True


def test_dossier_404_for_unknown_project(client):
    body = client.get("/projects/missing/dossier").json()
    assert body["error"]["code"] == "not_found"


def test_projects_risk_comes_from_confidence(client, seed):
    """risk_score/risk_band are derived from the single `confidences` home, not stored twice.

    And that home is itself fed by the hazard composite, so the portfolio badge cannot
    disagree with the "Risk to the asset" card on the project's own Confidence screen.
    """
    seed()  # nur_navoi_solar
    row = client.get("/projects").json()[0]
    assert row["id"] == "nur_navoi_solar"

    composite = client.get("/projects/nur_navoi_solar/dossier").json()["physical_risk"]["composite"]
    assert (row["risk_score"], row["risk_band"]) == (composite["score"], composite["band"])


def test_wayback_frames_served_as_dated_rgb_layers(client, seed):
    """The imagery endpoint serves the Wayback timelapse as several dated RGB frames, each
    dated from its own asset key even though the supplying evidence card is undated."""
    seed()
    layers = client.get("/projects/nur_navoi_solar/imagery").json()["layers"]
    dated_rgb = [layer for layer in layers if layer["kind"] == "rgb" and layer["date"]]
    assert len(dated_rgb) >= 2
    # Each frame is labelled by the ISO date embedded in its key.
    assert all(layer["date"] in layer["key"] for layer in dated_rgb)
