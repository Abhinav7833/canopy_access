"""Carbon — documented AGB -> carbon -> CO2e chain.

Above-ground biomass (AGB) comes from a published EO source (ESA CCI Biomass,
IPCC Tier-1), NOT an invented NDVI factor. Then IPCC 2006 factors convert it:
    Carbon (tC)  = AGB x 0.47        # IPCC carbon fraction
    CO2e (tCO2e) = Carbon x 44/12    # = x 3.67
    Total        = CO2e/ha x AOI_area_ha
Screening-grade estimate, aligned to Verra VCS / Plan Vivo — not full MRV.
"""

from .. import config
from ..data.reference import agb_mean


def estimate(aoi, area_ha):
    """Return (carbon tCO2e, AGB t/ha). None if no biomass data over the AOI."""
    agb = agb_mean(aoi)              # t/ha, ESA CCI Biomass
    if agb is None or agb <= 0:
        return None, agb
    co2e_per_ha = agb * config.CARBON_FRACTION * config.CO2_RATIO
    return round(co2e_per_ha * area_ha, 1), round(agb, 1)
