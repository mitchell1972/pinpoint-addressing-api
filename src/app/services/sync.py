"""Deferred sync for offline capture (spec §9.7).

A mobile/PWA client captures locations offline, each tagged with a client-generated
capture_id, and uploads the queue when back online. Ingest is idempotent: a
capture_id already seen returns its existing address instead of creating a new one,
so re-syncing the same queue (after a flaky connection) never duplicates.
"""

from app.repositories import sync as repo
from app.schemas.addresses import AddressCreate
from app.services import addresses as addresses_service


async def sync(conn, captures, account_id: str) -> dict:
    results = []
    for cap in captures:
        existing = await repo.find_capture(conn, cap["capture_id"])
        if existing is not None:
            results.append(
                {"capture_id": cap["capture_id"], "code": existing["code"], "status": "duplicate"}
            )
            continue

        data = AddressCreate(
            lat=cap["lat"],
            lng=cap["lng"],
            landmark=cap.get("landmark"),
            building_desc=cap.get("building_desc"),
            contact=cap.get("contact"),
            consent=cap.get("consent", False),
        )
        row = await addresses_service.create(conn, data, account_id)
        await repo.record_capture(conn, cap["capture_id"], row["id"], account_id)
        results.append({"capture_id": cap["capture_id"], "code": row["code"], "status": "created"})
    return {"results": results}
