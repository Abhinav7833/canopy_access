"""SCL-based cloud/shadow/snow masking for Sentinel-2.

The Scene Classification Layer (SCL) labels each pixel; we drop the bad classes
so only clear pixels survive into the median composite.
"""


def mask_s2(img):
    scl = img.select("SCL")
    clear = (scl.neq(3)                        # 3 = cloud shadow
             .And(scl.neq(8)).And(scl.neq(9))   # 8,9 = cloud medium/high
             .And(scl.neq(10)).And(scl.neq(11)))  # 10 cirrus, 11 snow
    return img.updateMask(clear)
