"""Shared configuration — project ID and the tunable dials.

Per-example inputs (AOI, dates) live in examples.py, not here.
"""

# Your Google Earth Engine Cloud project (reuse your existing one).
# Override at runtime with:  EE_PROJECT=other-id python run_demo.py
EE_PROJECT = "daring-hash-484514-q6"

# --- Analytics thresholds (starter values — tune to region) -----------------
CHANGE_NDVI_THRESHOLD = 0.1     # |dNDVI| above this counts as changed
CHANGE_PCT_MATERIAL   = 25.0    # % of AOI changed that flags human review
MIN_SCENES            = 3       # below this -> Insufficient data

# Carbon (AR-ACM0003 principle: biomass -> carbon -> CO2e, scaled by area)
BIOMASS_FACTOR        = 200.0   # toy NDVI->biomass allometric factor
CARBON_FRACTION       = 0.47    # IPCC carbon fraction of biomass
CO2_RATIO             = 3.67    # C -> CO2e (44/12)

# Risk
SAR_WATER_DB          = -17.0   # Sentinel-1 VV backscatter below this ~ water

# Structural build detection (Sentinel-1)
SAR_BUILD_DB          = 1.0     # VV backscatter RISE (dB) that flags new structures
SAR_BUILD_DATE_DB     = 0.7     # gentler rise used to DATE construction in the timeline

# Generation -> avoided emissions: grid emission factor (tCO2e per MWh displaced),
# PER GRID. A new renewable's avoided emissions depend on the local grid it feeds,
# so a single global constant is wrong (Spain's grid is ~4x cleaner than
# Uzbekistan's). Each value is documented.
GRID_EMISSION_FACTORS = {   # extensible: add a country as its factor is sourced
    # UNFCCC CDM standardized baseline, combined margin, solar/wind (0.75*OM 0.569
    # + 0.25*BM 0.499 = 0.551).  cdm.unfccc.int
    "Uzbekistan": 0.551,
    # Red Electrica de Espana, peninsular grid average 2020 = 0.123 tCO2/MWh
    # (0.165 in 2019). Grid-average is a conservative floor for a new renewable.
    "Spain": 0.123,
}
# Fallback for a grid NOT in the table above: a documented GLOBAL AVERAGE, clearly
# flagged. IEA/Ember global power-sector CO2 intensity ~2022 ~= 0.45 tCO2/MWh.
# Grid factors vary ~5x across countries, so this is a rough screening value only.
GRID_EMISSION_FACTOR_DEFAULT = 0.45


def grid_factor_for(country):
    """(factor tCO2e/MWh, source_label). Unknown grids fall back to a *flagged*
    global average — the avoided-emissions estimate is still produced, but its low
    confidence is explicit downstream (cross-check / evidence graph). Supply the
    asset's country to get a grid-specific factor."""
    if country in GRID_EMISSION_FACTORS:
        return GRID_EMISSION_FACTORS[country], f"{country} grid factor (documented)"
    return (GRID_EMISSION_FACTOR_DEFAULT,
            "global-average fallback (IEA/Ember ~2022) — grid unknown, approximate")

# Carbon saturation — NDVI above this adds no more biomass (dense-canopy limit)
CARBON_NDVI_CAP       = 0.7
