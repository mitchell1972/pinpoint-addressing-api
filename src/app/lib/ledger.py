"""Tamper-evident hash chain for the verification audit log.

Each entry's hash covers the previous entry's hash plus this entry's fields, so
editing or deleting any past entry breaks every hash after it. Pure functions;
the DB ordering and the serialising lock live in repositories/verify.py.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

GENESIS = "GENESIS"


def chain_fields(address_id, method, score, freshness, evidence, verifier, verified_at) -> dict:
    """The exact field set that gets hashed — kept in one place so the writer and
    the verifier always agree. Timestamps are normalised to UTC so a DB round-trip
    reproduces the same string."""
    if isinstance(verified_at, datetime):
        verified_at = verified_at.astimezone(UTC).isoformat()
    return {
        "address_id": str(address_id),
        "method": method,
        "score": score,
        "freshness": freshness,
        "evidence": evidence,
        "verifier": verifier,
        "verified_at": verified_at,
    }


def entry_hash(prev_hash: str, fields: dict) -> str:
    payload = (
        prev_hash + "|" + json.dumps(fields, sort_keys=True, separators=(",", ":"), default=str)
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def verify_chain(entries: list[dict]) -> tuple[bool, int | None]:
    """`entries` ordered by seq ascending, each carrying prev_hash, entry_hash and
    the chained fields. Returns (ok, first_broken_seq)."""
    prev = GENESIS
    for e in entries:
        recomputed = entry_hash(
            prev,
            chain_fields(
                e["address_id"],
                e["method"],
                e["score"],
                e["freshness"],
                e["evidence"],
                e["verifier"],
                e["verified_at"],
            ),
        )
        if e["prev_hash"] != prev or e["entry_hash"] != recomputed:
            return False, e["seq"]
        prev = e["entry_hash"]
    return True, None
