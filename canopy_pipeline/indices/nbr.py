"""NBR = (B8A - B12) / (B8A + B12). Vegetation moisture / burn ratio.

Low/negative NBR indicates dry or burned vegetation -> feeds fire risk.
"""


def nbr(img):
    return img.normalizedDifference(["B8A", "B12"]).rename("NBR")
