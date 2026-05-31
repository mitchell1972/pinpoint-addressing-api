"""Geocoding business logic: scoring and result shaping.

Services return plain result dicts (the domain view); controllers wrap them with
transport concerns (request_id, units, job_id).
"""
from app.repositories import geocode as repo
from app.schemas.geocode import BatchGeocodeRequest, GeocodeRequest, ReverseRequest


def _shape_forward(r: dict) -> dict:
    return {
        "code": r["code"],
        "olc": r["olc"],
        "lat": r["lat"],
        "lng": r["lng"],
        "confidence": round(float(r["sim"]), 2),
        "landmark": r["landmark"],
        "verified": r["status"] == "verified",
    }


def _shape_reverse(r: dict, radius_m: int) -> dict:
    return {
        "code": r["code"],
        "olc": r["olc"],
        "lat": r["lat"],
        "lng": r["lng"],
        # Confidence decays with distance across the search radius.
        "confidence": round(max(0.0, 1.0 - (float(r["dist_m"]) / radius_m)), 2),
        "landmark": r["landmark"],
        "verified": r["status"] == "verified",
    }


async def forward(conn, req: GeocodeRequest) -> list[dict]:
    state = req.area.state if req.area else None
    lga = req.area.lga if req.area else None
    rows = await repo.forward_geocode(conn, req.query, state, lga, req.limit)
    return [_shape_forward(r) for r in rows]


async def reverse(conn, req: ReverseRequest) -> list[dict]:
    rows = await repo.reverse_geocode(conn, req.lat, req.lng, req.limit, req.radius_m)
    return [_shape_reverse(r, req.radius_m) for r in rows]


async def batch(conn, req: BatchGeocodeRequest) -> list[list[dict]]:
    # MVP runs synchronously; a real async queue with backpressure is V1 (spec §10).
    return [await forward(conn, q) for q in req.queries]
