"""Orchestrator (spec §4.2) — calls the modules in order, handles errors.

Branches on asset type:
  - vegetation assets (forest/mangrove): full veg chain (NDVI, NDWI, carbon).
  - non-vegetation assets (solar/wind): skip NDVI/carbon; lead with change+risk.
Risk (fire from NBR, flood from SAR) is computed for every asset.
"""

import ee

from . import config
from .input.request_validator import validate
from .input.aoi_handler import build_aoi, area_hectares
from .data.sentinel2_loader import build_composite
from .data.sentinel1_loader import (
    backscatter_change, backscatter_timeline, detect_build_year)
from .data.reference import (
    built_up_fraction, aqueduct_flood_depth, fosberg_ffwi,
    annual_ghi, pv_generation_estimate)
from .indices.ndvi import ndvi
from .indices.ndwi import ndwi
from .indices.nbr import nbr
from .analytics.change_detection import detect
from .analytics.carbon_model import estimate as carbon_estimate
from .analytics.timeseries import ndvi_timeline, slope_per_year, series_std
from .analytics.fire import dnbr_mean, severity_class
from .analytics.flood import observed_flood_fraction
from .analytics.risk_scoring import score as risk_score
from .analytics import screening
from .export.json_export import assemble, error
from .export.raster_export import rgb_preview_url, geotiff_url


def _mean(img, aoi, band):
    """AOI-mean of one band as a Python float (0.0 if fully masked)."""
    val = img.reduceRegion(
        ee.Reducer.mean(), aoi, scale=10, maxPixels=1e9).get(band).getInfo()
    return val if val is not None else 0.0


def run_pipeline(req: dict, export: bool = False) -> dict:
    validate(req)
    asset = req.get("asset_type", "forest_restoration")
    has_veg = screening.is_vegetation(asset)
    aoi = build_aoi(req)
    area_ha = area_hectares(aoi)
    print(f"AOI area (ha): {area_ha:.1f}  | asset: {asset}")

    # --- data: two Sentinel-2 composites ---
    before_img, n_before = build_composite(aoi, req["before"], req["cloud_pct"])
    after_img, n_after = build_composite(aoi, req["after"], req["cloud_pct"])
    n_scenes = min(n_before, n_after)
    if n_scenes < config.MIN_SCENES:
        return error(
            req, "INSUFFICIENT_SCENES",
            f"Only {n_scenes} valid Sentinel-2 scenes found "
            f"(minimum: {config.MIN_SCENES}). Try extending the date range.",
            "data/sentinel2_loader.py")

    # --- change detection (always — veg loss OR build/land-cover change) ---
    nd_before, nd_after = ndvi(before_img), ndvi(after_img)
    diff, change, veg_change_pct, pct_gain, pct_loss = detect(
        nd_before, nd_after, aoi)

    # After-window mean NDVI is always needed (fire fuel factor + coverage);
    # only REPORTED as a metric for vegetation assets.
    ndvi_after_mean = _mean(nd_after, aoi, "NDVI")

    # yearly sampling window (same season each year) + the year range
    years = list(range(int(req["before"][0][:4]), int(req["after"][1][:4]) + 1))
    season = (req["after"][0][4:], req["after"][1][4:])

    if has_veg:
        ndvi_start = _mean(nd_before, aoi, "NDVI")
        ndvi_end = ndvi_after_mean
        ndvi_trend = ndvi_end - ndvi_start
        ndwi_end = _mean(ndwi(after_img), aoi, "NDWI")
        carbon_t, agb = carbon_estimate(aoi, area_ha)   # documented ESA CCI AGB
        # treat NDVI as a trajectory, not just endpoints
        ndvi_series = ndvi_timeline(aoi, years, season, req["cloud_pct"])
        ndvi_slope = slope_per_year(ndvi_series, "ndvi")
        ndvi_std = series_std(ndvi_series, "ndvi")
        span_years = (years[-1] - years[0]) or 1
        # Robust trend = fitted slope over the whole window (not endpoint delta).
        robust_trend = (ndvi_slope * span_years
                        if ndvi_slope is not None else (ndvi_trend or 0))
        # Only a real signal if it clears the series' interannual noise floor.
        ndvi_significant = (ndvi_std is not None and ndvi_slope is not None
                            and abs(robust_trend) > ndvi_std)
        print(f"  NDVI timeline: "
              f"{[(s['year'], s['ndvi']) for s in ndvi_series]}"
              f" | slope/yr: {ndvi_slope} | robust_trend: {round(robust_trend, 3)}"
              f" | std: {ndvi_std} | significant: {ndvi_significant}")
    else:
        ndvi_start = ndvi_end = ndvi_trend = ndwi_end = carbon_t = agb = None
        ndvi_series = ndvi_slope = ndvi_std = None
        robust_trend = 0
        ndvi_significant = False

    # --- hazards (documented) ---
    # fire: dNBR severity (Key & Benson) ; flood: new water vs JRC permanent ;
    # degradation: % of AOI that lost vegetation.
    dnbr = dnbr_mean(nbr(before_img), nbr(after_img), aoi)
    fire_severity = severity_class(dnbr)
    exposure = built_up_fraction(aoi)       # Score B context (GHSL community)
    # observed flood (Otsu, UN-SPIDER) — "did it flood?"
    obs_flood = observed_flood_fraction(aoi, req["after"], optical_img=after_img)
    # forward-looking hazards: Aqueduct 100-yr flood depth, Fosberg fire index
    flood_depth = aqueduct_flood_depth(aoi)
    ffwi = fosberg_ffwi(aoi, req["after"])
    print(f"  dNBR={dnbr:.3f} ({fire_severity}) | obs_flood={obs_flood:.3f} "
          f"| flood_depth_100yr={flood_depth:.3f}m | FFWI={ffwi} "
          f"| community_exp={exposure:.3f}")
    risk = risk_score(dnbr, obs_flood, pct_loss,
                      flood_depth, ffwi, ndvi_after_mean, exposure)

    # --- structural (build) change + multi-year timeline (Sentinel-1) ---
    # Panels/structures raise radar backscatter — a build signal NDVI can't see.
    sar = backscatter_change(aoi, req["before"], req["after"])
    # Build detection is only meaningful for physical assets (solar/wind). On a
    # vegetation asset, tidal/seasonal backscatter can trip the threshold (a
    # false "structure") — so the flag is not applicable there.
    # Magnitude, not sign: panels raise backscatter over desert but lower it over
    # farmland, so a large change in EITHER direction is a structural signal.
    build_detected = (not has_veg and sar["vv_delta"] is not None
                      and abs(sar["vv_delta"]) >= config.SAR_BUILD_DB)
    timeline = build_year = None
    if not has_veg:   # build dating matters for physical assets (solar/wind)
        timeline = backscatter_timeline(aoi, years)
        build_year = detect_build_year(timeline, config.SAR_BUILD_DATE_DB)
    print(f"  S1 backscatter delta: {sar['vv_delta']} dB "
          f"| build_detected: {build_detected} | build_year: {build_year}")

    # change_detected is asset-aware: vegetation % for veg, SAR build for others
    change_detected = (veg_change_pct > 5) if has_veg else build_detected

    # --- generation estimate (solar/energy assets) — PVWatts + ERA5 GHI ---
    gen_est = None
    if req.get("capacity_mw"):
        ghi = annual_ghi(aoi, int(req["after"][1][:4]) - 1)   # last full year
        gwh_fixed = pv_generation_estimate(req["capacity_mw"], ghi, pr=0.80, tracking=1.0)
        gwh_track = pv_generation_estimate(req["capacity_mw"], ghi, pr=0.80, tracking=1.30)
        # grid emission factor is per-grid: resolve from the request's country
        # (explicit override wins), so a Spanish asset isn't scored on Uzbekistan's.
        gef, gef_src = config.grid_factor_for(req.get("country"))
        if req.get("grid_emission_factor"):
            gef, gef_src = req["grid_emission_factor"], "request override"
        gen_est = {
            "method": "PVWatts (NREL) simple model + ERA5 GHI (estimate, "
                      "not a measurement)",
            "annual_ghi_kwh_m2": ghi,
            "capacity_mw": req["capacity_mw"],
            "est_gwh_fixed_tilt": gwh_fixed,
            "est_gwh_tracking": gwh_track,
            "reported_gwh_yr": req.get("reported_gwh_yr"),
            # avoided emissions = generation (MWh) x grid emission factor.
            # Documented ESTIMATE derived from the generation estimate above.
            "grid_emission_factor_tco2_per_mwh": gef,
            "grid_emission_factor_source": gef_src,
            "est_tco2_avoided_fixed": (round(gwh_fixed * 1000 * gef)
                                       if gwh_fixed is not None else None),
            "est_tco2_avoided_tracking": (round(gwh_track * 1000 * gef)
                                          if gwh_track is not None else None),
            "reported_tco2_avoided_yr": req.get("reported_tco2_avoided_yr"),
        }
        print(f"  generation est: {gwh_fixed}-{gwh_track} GWh vs reported "
              f"{gen_est['reported_gwh_yr']} | avoided est: "
              f"{gen_est['est_tco2_avoided_fixed']}-"
              f"{gen_est['est_tco2_avoided_tracking']} tCO2/yr vs reported "
              f"{gen_est['reported_tco2_avoided_yr']}")

    # --- verdict (confidence tempered by valid-data coverage) ---
    coverage = _mean(nd_after.mask(), aoi, "NDVI")
    status = screening.status(asset, robust_trend, pct_gain, pct_loss,
                              n_scenes, ndvi_significant)
    conf = screening.confidence(n_scenes, coverage)
    assurance = screening.assurance_statement(status)
    finding = screening.main_finding(
        asset, ndvi_slope, ndvi_significant, pct_gain, pct_loss,
        sar["vv_delta"], build_detected, build_year)

    # --- outputs: instant RGB preview + downloadable GeoTIFFs ---
    preview = rgb_preview_url(after_img, aoi)
    ndvi_url = geotiff_url(nd_after, aoi)
    change_url = geotiff_url(change, aoi)

    return assemble(req, dict(
        area_ha=area_ha, n_scenes=n_scenes, has_veg=has_veg,
        ndvi_start=ndvi_start, ndvi_end=ndvi_end, ndvi_trend=ndvi_trend,
        ndwi_end=ndwi_end, veg_change_pct=veg_change_pct,
        pct_gain=pct_gain, pct_loss=pct_loss, carbon_t=carbon_t, agb=agb,
        dnbr=dnbr, fire_severity=fire_severity, obs_flood=obs_flood,
        exposure=exposure,
        sar=sar, build_detected=build_detected, change_detected=change_detected,
        gen_est=gen_est, timeline=timeline, build_year=build_year,
        ndvi_series=ndvi_series, ndvi_slope=ndvi_slope, ndvi_std=ndvi_std,
        robust_trend=robust_trend, ndvi_significant=ndvi_significant,
        status=status, confidence=conf, assurance=assurance,
        main_finding=finding, risk=risk,
        preview_url=preview, ndvi_raster_url=ndvi_url,
        change_map_url=change_url,
    ))
