"""NDVI = (B8 - B4) / (B8 + B4). High = vigorous vegetation."""


def ndvi(img):
    return img.normalizedDifference(["B8", "B4"]).rename("NDVI")
