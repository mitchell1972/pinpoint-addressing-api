"""Minimal geohash encoder (standard base-32 algorithm).

Hand-rolled (~25 lines, stable spec) to avoid an extra dependency. We store the
geohash for cheap prefix-bucketing/analytics; spatial queries use PostGIS geom.
"""

_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"


def encode(lat: float, lng: float, precision: int = 9) -> str:
    lat_lo, lat_hi = -90.0, 90.0
    lng_lo, lng_hi = -180.0, 180.0
    bits = [16, 8, 4, 2, 1]
    out: list[str] = []
    bit = 0
    ch = 0
    even = True  # start with longitude

    while len(out) < precision:
        if even:
            mid = (lng_lo + lng_hi) / 2
            if lng > mid:
                ch |= bits[bit]
                lng_lo = mid
            else:
                lng_hi = mid
        else:
            mid = (lat_lo + lat_hi) / 2
            if lat > mid:
                ch |= bits[bit]
                lat_lo = mid
            else:
                lat_hi = mid
        even = not even

        if bit < 4:
            bit += 1
        else:
            out.append(_BASE32[ch])
            bit = 0
            ch = 0

    return "".join(out)
