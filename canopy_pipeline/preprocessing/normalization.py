"""Radiometric normalisation — Sentinel-2 DN -> surface reflectance (0-1).

Sentinel-2 stores reflectance x10000, so dividing by 10000 returns it to the
0-1 range the vis params and thresholds expect.
"""


def to_reflectance(img):
    return img.divide(10000)
