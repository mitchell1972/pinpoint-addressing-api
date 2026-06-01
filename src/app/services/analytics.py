"""Delivery-success analytics (spec §6.5, §11).

Records delivery outcomes and computes failed-drop rate, time-to-locate, and
hotspots. A successful delivery nudges the address's confidence up — the loop
that makes coverage improve with use.
"""

from app.core.errors import NotFoundError
from app.repositories import addresses as addresses_repo
from app.repositories import analytics as repo

_DELIVERY_CONFIDENCE_BUMP = 0.02


async def record(conn, code: str, account_id: str, status: str, reason, ttl) -> dict:
    addr = await addresses_repo.get_by_code(conn, code)
    if addr is None:
        raise NotFoundError("Address not found.")
    delivery_id = await repo.record_delivery(conn, addr["id"], account_id, status, reason, ttl)
    if status == "delivered":
        await addresses_repo.bump_confidence(conn, addr["id"], _DELIVERY_CONFIDENCE_BUMP)
    return {"id": str(delivery_id), "status": status}


async def summary(conn, account_id: str) -> dict:
    row = await repo.summary(conn, account_id)
    total = row["total"] or 0
    failed = row["failed"] or 0
    return {
        "total": total,
        "delivered": row["delivered"] or 0,
        "failed": failed,
        "failed_rate": round(failed / total, 3) if total else 0.0,
        "avg_time_to_locate_seconds": round(float(row["avg_ttl"]), 1)
        if row["avg_ttl"] is not None
        else None,
    }


async def hotspots(conn, account_id: str) -> list[dict]:
    out = []
    for r in await repo.hotspots(conn, account_id):
        total = r["total"]
        failed = r["failed"]
        out.append(
            {
                "lga": r["lga"],
                "total": total,
                "failed": failed,
                "failed_rate": round(failed / total, 3) if total else 0.0,
            }
        )
    return out
