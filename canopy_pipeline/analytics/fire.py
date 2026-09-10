"""Fire severity — dNBR with Key & Benson (2006) bands.

dNBR = NBR_pre - NBR_post. Classified with the USGS/FIREMON severity bands
(UN-SPIDER). This is the documented post-event burn-severity method; pre-event
fire DANGER (Canadian FWI, weather-driven) is a separate ERA5-based overlay.
"""

import ee

# Key & Benson (2006) severity bands, in dNBR units.
KB_BANDS = [
    (-9.99, -0.10, "Enhanced regrowth"),
    (-0.10,  0.10, "Unburned"),
    (0.10,   0.27, "Low severity"),
    (0.27,   0.44, "Moderate-low severity"),
    (0.44,   0.66, "Moderate-high severity"),
    (0.66,   9.99, "High severity"),
]
KB_HIGH = 0.66   # high-severity threshold — used to normalise the hazard score


def dnbr_mean(nbr_before, nbr_after, aoi):
    """AOI-mean dNBR (NBR_pre - NBR_post). Positive = vegetation burned/lost."""
    d = nbr_before.subtract(nbr_after).rename("dNBR")
    val = d.reduceRegion(
        ee.Reducer.mean(), aoi, scale=20, maxPixels=1e9).get("dNBR").getInfo()
    return val if val is not None else 0.0


def severity_class(dnbr):
    for lo, hi, name in KB_BANDS:
        if lo <= dnbr < hi:
            return name
    return "Unburned"
