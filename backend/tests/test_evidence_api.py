def test_evidence_for_project(client, seed):
    seed()
    evidence = client.get("/projects/nur_navoi_solar/evidence").json()
    assert evidence
    assert all(e["id"].startswith("nur_navoi_solar") for e in evidence)
    # Assets hang off whichever card supplies them, not off every card.
    assert any(e["supporting_assets"] for e in evidence)


def test_missing_project_404s(client):
    body = client.get("/projects/missing/evidence").json()
    assert body["error"]["code"] == "not_found"
