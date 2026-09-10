"""Clip rasters to the AOI."""


def clip_to_aoi(img, aoi):
    return img.clip(aoi)
