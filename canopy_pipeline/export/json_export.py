"""Assemble the output JSON (spec §3.1) and the error envelope (spec §6).

Emits the GEOSPATIAL fields only. `financial_relevance` and the final hosted
asset URLs are attached downstream by the backend / finance layer (spec §3.3).
"""

from datetime import datetime, timezone

from .. import config


def assemble(req: dict, r: dict) -> dict:
    """Pack computed values (dict `r`) into the §3.1 result object."""
    veg = r["has_veg"]
    change_detected = r["change_detected"]        # asset-aware (veg % or SAR build)
    human_review = (r["confidence"] < 0.5
                    or r["veg_change_pct"] > config.CHANGE_PCT_MATERIAL)

    return {
        "analysis_id": req["analysis_id"],
        "status": "completed",
        "pipeline_version": "v0.2",
        "analysis_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "summary": {
            "screening_status": r["status"],
            # Risk TO the asset (financial materiality). The harm BY the asset is
            # reported separately below — the two are never folded into one number.
            "risk_score": r["risk"]["hazard_composite"],
            "risk_band": r["risk"]["hazard_band"],
            "environmental_effect_score": r["risk"]["effect_composite"],
            "environmental_effect_band": r["risk"]["effect_band"],
            "confidence": round(r["confidence"], 2),
            "change_detected": change_detected,
            "human_review_recommended": human_review,
            "main_finding": r["main_finding"],
            "assurance_statement": r.get("assurance"),
        },
        "risk_detail": {
            "structure": "Hazard x Exposure x Vulnerability (IPCC AR6)",
            # environment -> asset
            "hazard_subscores": {
                "fire": r["risk"]["fire"], "flood": r["risk"]["flood"]},
            # asset -> environment
            "effect_subscores": {"degradation": r["risk"]["degradation"]},
            "fire_fosberg_ffwi": r["risk"]["fire_fosberg_ffwi"],
            "fire_severity_dnbr": r["risk"]["fire_severity_dnbr"],
            "fire_severity_class": r["fire_severity"],
            "flood_depth_100yr_m": r["risk"]["flood_depth_100yr_m"],
            "flood_depth_damage_frac": r["risk"]["flood_depth_damage_frac"],
            "flood_observed_frac": r["risk"]["flood_observed_frac"],
            "asset_exposure": r["risk"]["asset_exposure"],
            "community_exposure_built_up": r["risk"]["community_exposure_built_up"],
            "sources": "dNBR Key & Benson; Otsu/UN-SPIDER observed flood; "
                       "Aqueduct + JRC/Huizinga depth-damage; Fosberg FFWI (1978)",
            "socioeconomic_overlay": "Score B (INFORM / ND-GAIN) — "
                                     "not computed from satellites",
        },
        "metrics": {
            "ndvi_start": r["ndvi_start"],
            "ndvi_end": r["ndvi_end"],
            "ndvi_trend": r["ndvi_trend"],
            "vegetation_change_percent": r["veg_change_pct"],
            "carbon_estimate_tonnes": r["carbon_t"],
            "deforestation_detected": bool(
                veg and r.get("ndvi_significant")
                and (r.get("robust_trend") or 0) < -0.15
                and r["veg_change_pct"] > 5),
            "flood_risk_score": r["risk"]["flood"],
            "fire_risk_score": r["risk"]["fire"],
        },
        "evidence": [_evidence_card(req, r)],
        "map_outputs": {
            "rgb_composite_url": r["preview_url"],
            "ndvi_raster_url": r.get("ndvi_raster_url"),
            "change_map_url": r.get("change_map_url"),
            "aoi_geojson_url": r.get("aoi_geojson_url"),
            "risk_layer_url": None,
        },
        "metadata": {
            "satellite_sources": ["Sentinel-2", "Sentinel-1"],
            "date_range": {"start": req["before"][0], "end": req["after"][1]},
            "cloud_cover_threshold": req["cloud_pct"],
            "aoi_area_hectares": round(r["area_ha"], 1),
        },
    }


def _evidence_card(req: dict, r: dict) -> dict:
    """One typed evidence card — the product's central primitive (spec §3.3)."""
    conf_label = ("high" if r["confidence"] >= 0.8
                  else "medium" if r["confidence"] >= 0.5 else "low")
    if r["has_veg"]:
        return {
            "observation_type": "vegetation_change",
            "summary": "Vegetation index change inside the project boundary.",
            "metric": {"name": "ndvi_slope_per_year",
                       "value": r.get("ndvi_slope"),
                       "baseline_period": req["before"][0],
                       "comparison_period": req["after"][0]},
            "source": {"name": "Sentinel-2", "resolution": "10 m",
                       "processing": "median composite, cloud-masked"},
            "method": "annual NDVI trend (least-squares slope over yearly "
                      "composites), gated on interannual variability "
                      "(method_id: ndvi_change_v3)",
            "confidence": conf_label,
            "trend_significant": bool(r.get("ndvi_significant")),
            "interannual_std": r.get("ndvi_std"),
            "two_point_ndvi_delta": (round(r["ndvi_trend"], 3)
                                     if r["ndvi_trend"] is not None else None),
            "agb_t_ha": r.get("agb"),
            "carbon_source": "ESA CCI Biomass (IPCC 2006 factors "
                             "x0.47, x3.67); Verra/Plan Vivo aligned",
            "ndvi_timeline": r.get("ndvi_series"),
            "trend_per_year": r.get("ndvi_slope"),
            "limitations": [
                "NDVI is a proxy, not direct ecological impact",
                "seasonality / cloud masking can affect the result",
                "trend reported only when it exceeds interannual variability",
                "no ground verification in the demo",
            ],
        }
    sar_delta = r["sar"]["vv_delta"]
    return {
        "observation_type": "land_cover_change",
        "summary": "Structural change consistent with construction / operation.",
        "metric": {"name": "sar_backscatter_change_db",
                   "value": round(sar_delta, 2) if sar_delta is not None else None,
                   "baseline_period": req["before"][0],
                   "comparison_period": req["after"][0]},
        "source": {"name": "Sentinel-1 SAR", "resolution": "10 m",
                   "processing": "VV backscatter mean, before vs after"},
        "method": "SAR backscatter change (method_id: sar_build_v1)",
        "confidence": conf_label,
        "build_year_estimate": r.get("build_year"),
        "backscatter_timeline": r.get("timeline"),
        "generation_estimate": r.get("gen_est"),
        "limitations": [
            "confirms new structures appeared, not generation output",
            "solar panels are only weakly separable from desert with simple "
            "signals; build-dating is approximate (+/- 1-2 yr)",
            "robust automated detection would need a classification model",
            "no independent metering in the demo",
        ],
    }


def error(req: dict, code: str, message: str, module: str) -> dict:
    return {
        "analysis_id": req["analysis_id"], "status": "failed",
        "error": {"code": code, "message": message, "module": module},
    }
