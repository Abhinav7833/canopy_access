"""NDWI = (B3 - B8) / (B3 + B8). High = surface water.

Used for mangroves to separate canopy from tidal water at the coastal edge.
"""


def ndwi(img):
    return img.normalizedDifference(["B3", "B8"]).rename("NDWI")
