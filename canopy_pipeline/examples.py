"""The two curated demo projects (from the Source Pack, 2 Jul 2026).

Coordinates are approximate CENTRE points -> a starter box. Confirm the exact
AOI polygon from the imagery before relying on it (Source Pack: "confirm exact
AOI polygons before pulling imagery").
"""

from .input.aoi_handler import box_from_center

# Project 1 — Nur Navoi Solar, Uzbekistan (the self-reporting gap).
# Solar = physical-risk asset: NDVI/carbon N/A; lead with change + risk (§7.3).
NUR_NAVOI = {
    "analysis_id":   "nur_navoi_solar",
    "project_name":  "Nur Navoi Solar (100 MW), Uzbekistan",
    "analysis_type": "risk_only",
    "asset_type":    "solar",
    "country":       "Uzbekistan",   # selects the Uzbekistan grid emission factor
    # Panel field confirmed from imagery at ~64.985E, 40.112N.
    "aoi_coords":    box_from_center(lon=64.985, lat=40.112, half_deg=0.012),
    "before":        ("2019-05-01", "2019-09-30"),   # pre-construction desert
    "after":         ("2024-05-01", "2024-09-30"),   # fully operational
    "cloud_pct":     20,
    "capacity_mw":   100,        # stated nameplate capacity
    "reported_gwh_yr": 270,      # reported annual generation (to benchmark)
    "reported_tco2_avoided_yr": 156000,   # reported avoided emissions (Masdar/IFC; to benchmark)
    "requested_outputs": ["risk_score", "screening_status",
                          "change_detection", "maps"],
}

# Project 2 — Mikoko Pamoja mangrove, Gazi Bay, Kenya (capital unlocked by data).
# Mangrove = full veg chain: NDVI + NDWI (canopy vs tidal water) + carbon (§7.2).
MIKOKO = {
    "analysis_id":   "mikoko_pamoja_mangrove",
    "project_name":  "Mikoko Pamoja Mangrove, Gazi Bay, Kenya",
    "analysis_type": "full_analysis",
    "asset_type":    "mangrove",
    "aoi_coords":    box_from_center(lon=39.5039, lat=-4.4198, half_deg=0.006),
    "before":        ("2019-01-01", "2019-04-30"),   # S2 surface-reflectance
    "after":         ("2024-01-01", "2024-04-30"),   # starts ~2017; dry season
    "cloud_pct":     40,                             # coastal Kenya is cloudier
    "requested_outputs": ["risk_score", "screening_status", "ndvi_trend",
                          "change_detection", "carbon_estimate", "maps"],
}

EXAMPLES = {"nur_navoi": NUR_NAVOI, "mikoko": MIKOKO}
