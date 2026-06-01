"""Address verification (spec §6.3 / §10).

Always returns existence + a freshness-adjusted confidence + a stale flag. In
`kyc` mode it also appends an entry to the tamper-evident audit ledger (capturing
device/agent/IP evidence) and records the re-verification against the address
(updating its freshness, count, and running confidence — the feedback loop).
"""

from datetime import UTC, datetime

from app.lib import scoring
from app.repositories import addresses as addresses_repo
from app.repositories import geocode as geocode_repo
from app.repositories import verify as verify_repo
from app.schemas.verify import VerifyRequest

# Within this many metres a coordinate is treated as resolving to a known address.
_COORD_MATCH_RADIUS_M = 100


async def _resolve(conn, req: VerifyRequest) -> dict | None:
    if req.code:
        return await addresses_repo.get_by_code(conn, req.code)
    rows = await geocode_repo.reverse_geocode(conn, req.lat, req.lng, 1, _COORD_MATCH_RADIUS_M)
    return await addresses_repo.get_by_code(conn, rows[0]["code"]) if rows else None


async def verify(conn, req: VerifyRequest, evidence: dict | None = None) -> dict:
    addr = await _resolve(conn, req)
    if addr is None:
        return {
            "exists": False,
            "confidence": 0.0,
            "freshness": 0.0,
            "stale": True,
            "mode": req.mode,
            "code": None,
            "evidence_ref": None,
            "verification_id": None,
        }

    now = datetime.now(UTC)
    reference = addr["last_verified_at"] or addr["created_at"]
    fresh = round(scoring.freshness(reference, now), 3)
    stale = scoring.is_stale(reference, now)
    score = scoring.combined_score(float(addr["confidence"]), fresh, addr["verification_count"])

    result = {
        "exists": True,
        "confidence": score,
        "freshness": fresh,
        "stale": stale,
        "mode": req.mode,
        "code": addr["code"],
        "evidence_ref": None,
        "verification_id": None,
    }

    if req.mode == "kyc":
        record = {**(evidence or {}), "captured_at": now.isoformat()}
        entry = await verify_repo.append(
            conn, addr["id"], "kyc", score, fresh, record, "system", now
        )
        await addresses_repo.touch_verification(conn, addr["code"], score, now)
        result["verification_id"] = str(entry["id"])
        result["evidence_ref"] = entry["entry_hash"]  # tamper-evident ledger hash

    return result
