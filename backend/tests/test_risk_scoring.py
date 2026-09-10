"""Double materiality: the two directions must never contaminate each other.

`canopy_pipeline.analytics.risk_scoring` used to return `max(fire, flood, degradation)`
as one composite. That number rose both when the environment endangered the asset and
when the asset harmed the environment — opposite findings calling for opposite actions
(harden/insure vs remediate). These tests pin the separation.
"""

from canopy_pipeline.analytics.risk_scoring import band_for, score

# score(dnbr, observed_flood_frac, pct_loss, flood_depth_m, ffwi, fuel_ndvi, community_exposure)
_CALM = dict(
    dnbr=0.0,
    observed_flood_frac=0.0,
    flood_depth_m=0.0,
    ffwi=0.0,
    fuel_ndvi=0.0,
    community_exposure=0.0,
)


def test_harm_by_the_asset_never_raises_the_risk_to_the_asset():
    r = score(pct_loss=80, **_CALM)

    assert r["degradation"] == 80
    assert r["effect_composite"] == 80
    assert r["effect_band"] == "Critical"
    # The site is destroying vegetation, but nothing threatens the site itself.
    assert r["hazard_composite"] == 0
    assert r["hazard_band"] == "Low"


def test_danger_to_the_asset_never_raises_the_harm_it_causes():
    r = score(pct_loss=0, **{**_CALM, "ffwi": 90.0, "fuel_ndvi": 0.3})

    assert r["fire"] > 50
    assert r["hazard_composite"] == r["fire"]
    # The site is fire-exposed, but it is not itself harming anything.
    assert r["effect_composite"] == 0
    assert r["effect_band"] == "Low"


def test_hazard_composite_is_the_worst_hazard_only():
    r = score(pct_loss=99, **{**_CALM, "flood_depth_m": 3.0, "ffwi": 10.0, "fuel_ndvi": 0.1})

    assert r["hazard_composite"] == max(r["fire"], r["flood"])
    assert r["hazard_composite"] < r["degradation"]  # the effect score is excluded


def test_both_directions_are_banded_on_the_same_scale():
    assert [band_for(s) for s in (0, 24, 25, 49, 50, 74, 75, 100)] == [
        "Low",
        "Low",
        "Medium",
        "Medium",
        "High",
        "High",
        "Critical",
        "Critical",
    ]
