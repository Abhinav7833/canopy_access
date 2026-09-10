"""Reference datasets — the published, open layers our scores are grounded in.

  - JRC Global Surface Water (Pekel 2016)  -> permanent water, to isolate NEW flooding
  - JRC GHSL built-up (2023)               -> exposure context
  - ESA CCI Biomass                        -> documented above-ground biomass (AGB)

All are open, peer-reviewed / standards-body datasets (see Scoring Methodology).
"""

import ee


def permanent_water(aoi, occurrence_pct=50):
    """JRC GSW: 1 where water is present >= occurrence_pct of the time (1984-)."""
    gsw = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence")
    return gsw.gte(occurrence_pct).unmask(0).clip(aoi).rename("permanent")


def built_up_fraction(aoi):
    """GHSL built-surface fraction of the AOI (0-1) — exposure proxy."""
    ghsl = (ee.ImageCollection("JRC/GHSL/P2023A/GHS_BUILT_S")
            .filterDate("2020-01-01", "2021-01-01").first())
    if ghsl is None:
        return 0.0
    # built_surface = m^2 built per 100 m pixel (pixel = 10,000 m^2)
    frac = ghsl.select("built_surface").divide(10000).clamp(0, 1)
    val = frac.reduceRegion(
        ee.Reducer.mean(), aoi, scale=100, maxPixels=1e9).get("built_surface")
    return val.getInfo() if val is not None else 0.0


def agb_mean(aoi):
    """Mean above-ground biomass (t/ha) over the AOI from ESA CCI Biomass."""
    cci = (ee.ImageCollection("projects/sat-io/open-datasets/ESA/ESA_CCI_AGB")
           .select("AGB").sort("system:time_start", False).first())
    if cci is None:
        return None
    val = cci.reduceRegion(
        ee.Reducer.mean(), aoi, scale=100, maxPixels=1e9).get("AGB")
    return val.getInfo() if val is not None else None


def annual_ghi(aoi, year):
    """Annual global horizontal irradiation (kWh/m²/yr) over the AOI, from ERA5."""
    col = (ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
           .filterDate(f"{year}-01-01", f"{year + 1}-01-01")
           .select("surface_solar_radiation_downwards_sum"))
    jm2 = col.sum().reduceRegion(
        ee.Reducer.mean(), aoi, scale=5000, maxPixels=1e9
    ).get("surface_solar_radiation_downwards_sum")
    v = jm2.getInfo() if jm2 is not None else None
    return round(v / 3.6e6, 0) if v is not None else None   # J/m² -> kWh/m²


def pv_generation_estimate(capacity_mw, ghi_kwh, pr=0.80, tracking=1.0):
    """PVWatts (NREL) simple model: annual generation (GWh) from installed
    capacity and solar resource. E ≈ capacity × peak-sun-hours × performance
    ratio; peak-sun-hours ≈ annual GHI. A documented estimate, not a measurement.
    """
    if capacity_mw is None or ghi_kwh is None:
        return None
    return round(capacity_mw * ghi_kwh * pr * tracking / 1000, 1)


def aqueduct_flood_depth(aoi, return_period=100):
    """Forward-looking flood hazard: mean 100-yr inundation depth (m) over the
    AOI from WRI Aqueduct (worst of riverine / coastal). Documented flood-risk
    context per the methodology."""
    aq = (ee.ImageCollection("WRI/Aqueduct_Flood_Hazard_Maps/V2")
          .filter(ee.Filter.eq("returnperiod", return_period))
          .filter(ee.Filter.eq("climatescenario", "historical")))
    depth = aq.max().reduceRegion(
        ee.Reducer.mean(), aoi, scale=1000, maxPixels=1e9).get("inundation_depth")
    v = depth.getInfo() if depth is not None else None
    return v if v is not None else 0.0


def fosberg_ffwi(aoi, window):
    """Fosberg Fire Weather Index (Fosberg 1978) — a documented, peer-reviewed
    fire-weather index from temperature, relative humidity and wind. One-shot
    (no moisture-code recursion), so computable in Earth Engine. Returns 0-100.
    """
    import math
    era = (ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
           .filterDate(*window).mean())
    s = era.reduceRegion(
        ee.Reducer.mean(), aoi, scale=5000, maxPixels=1e9).getInfo()
    t = s.get("temperature_2m_max")             # daytime peak temp (K)
    td = s.get("dewpoint_temperature_2m")       # dewpoint (K)
    u = s.get("u_component_of_wind_10m")
    v = s.get("v_component_of_wind_10m")
    if None in (t, td, u, v):
        return 0.0
    tc, tdc = t - 273.15, td - 273.15
    rh = 100 * math.exp((17.625 * tdc) / (243.04 + tdc)) \
        / math.exp((17.625 * tc) / (243.04 + tc))          # Magnus RH (%)
    rh = max(1.0, min(100.0, rh))
    tf = tc * 9 / 5 + 32                                    # C -> F (Fosberg uses F)
    wind_mph = math.hypot(u, v) * 2.23694                  # m/s -> mph
    # Fosberg equilibrium fuel moisture m (%), piecewise in RH:
    if rh < 10:
        m = 0.03229 + 0.281073 * rh - 0.000578 * rh * tf
    elif rh <= 50:
        m = 2.22749 + 0.160107 * rh - 0.014784 * tf
    else:
        m = 21.0606 + 0.005565 * rh * rh - 0.00035 * rh * tf - 0.483199 * rh
    eta = 1 - 2 * (m / 30) + 1.5 * (m / 30) ** 2 - 0.5 * (m / 30) ** 3
    ffwi = eta * math.sqrt(1 + wind_mph ** 2) / 0.3002
    return round(min(100.0, max(0.0, ffwi)), 1)

