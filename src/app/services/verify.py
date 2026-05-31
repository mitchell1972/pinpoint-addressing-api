"""Address verification (spec §6.3).

MVP returns existence + confidence. In `kyc` mode it writes a minimal verification
record and returns its reference. The full evidence trail (timestamped capture,
device, agent attestation, immutable store) is V1.
"""

from app.repositories import addresses as addresses_repo
from app.repositories import geocode as geocode_repo
from app.repositories import verify as verify_repo
from app.schemas.verify import VerifyRequest

# Within this many metres a coordinate is treated as resolving to a known address.
_COORD_MATCH_RADIUS_M = 100


async def verify(conn, req: VerifyRequest) -> dict:
    if req.code:
        addr = await addresses_repo.get_by_code(conn, req.code)
    else:
        rows = await geocode_repo.reverse_geocode(conn, req.lat, req.lng, 1, _COORD_MATCH_RADIUS_M)
        addr = rows[0] if rows else None

    if addr is None:
        return {
            "exists": False,
            "confidence": 0.0,
            "mode": req.mode,
            "code": None,
            "evidence_ref": None,
            "verification_id": None,
        }

    confidence = round(float(addr["confidence"]), 2)
    result = {
        "exists": True,
        "confidence": confidence,
        "mode": req.mode,
        "code": addr["code"],
        "evidence_ref": None,
        "verification_id": None,
    }

    if req.mode == "kyc":
        verification_id = await verify_repo.create_verification(
            conn, addr["code"], "basic-mvp", confidence, "system"
        )
        result["verification_id"] = str(verification_id)
        result["evidence_ref"] = f"ver_{verification_id}"

    return result
