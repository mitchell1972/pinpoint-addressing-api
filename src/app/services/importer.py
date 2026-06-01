"""Map-data import pipeline (spec §9.8).

Bootstraps the address graph from CSV/structured rows (OpenStreetMap, government
open data, partner lists) with provenance + a source confidence. De-duplicates by
Plus Code so re-running an import is safe.
"""

import csv
import io

from psycopg import errors

from app.lib.codes import new_alias
from app.lib.geohash import encode as geohash_encode
from app.lib.olc import encode as olc_encode
from app.repositories import addresses as repo

DEFAULT_CONFIDENCE = 0.6  # imported, not yet delivery-verified


def parse_csv(text: str) -> list[dict]:
    """Parse CSV text into import rows. Requires lat,lng; the rest are optional."""
    rows: list[dict] = []
    for r in csv.DictReader(io.StringIO(text)):
        rows.append(
            {
                "lat": float(r["lat"]),
                "lng": float(r["lng"]),
                "alias": (r.get("alias") or "").strip() or None,
                "landmark": (r.get("landmark") or "").strip() or None,
                "building_desc": (r.get("building_desc") or "").strip() or None,
                "state": (r.get("state") or "").strip() or None,
                "lga": (r.get("lga") or "").strip() or None,
                "confidence": float(r["confidence"]) if r.get("confidence") else None,
            }
        )
    return rows


async def import_rows(conn, rows, source: str = "import") -> dict:
    inserted = skipped = 0
    for row in rows:
        olc = olc_encode(row["lat"], row["lng"])
        if await repo.exists_by_olc(conn, olc):
            skipped += 1
            continue
        geohash = geohash_encode(row["lat"], row["lng"])
        confidence = row.get("confidence") or DEFAULT_CONFIDENCE
        for _ in range(5):
            try:
                await repo.insert_imported(conn, new_alias(), olc, geohash, row, source, confidence)
                inserted += 1
                break
            except errors.UniqueViolation:
                continue  # alias collision — retry with a new alias
    return {"inserted": inserted, "skipped": skipped}
