"""Append-only, hash-chained verification ledger (KYC/AML audit trail)."""

from psycopg.types.json import Json

from app.lib.ledger import GENESIS, chain_fields, entry_hash, verify_chain

# Transaction-level advisory lock id, serialising appends so the hash chain stays
# consistent under concurrency.
_LEDGER_LOCK = 8714

_INSERT = """
INSERT INTO verification
    (address_id, method, score, freshness, evidence, verifier, prev_hash, entry_hash, verified_at)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
RETURNING id, entry_hash
"""

_ALL_ORDERED = """
SELECT seq, address_id, method, score, freshness, evidence, verifier, prev_hash, entry_hash, verified_at
FROM verification ORDER BY seq ASC
"""


async def append(
    conn, address_id, method, score, freshness, evidence: dict, verifier, verified_at
) -> dict:
    async with conn.transaction():
        async with conn.cursor() as cur:
            await cur.execute("SELECT pg_advisory_xact_lock(%s)", (_LEDGER_LOCK,))
            await cur.execute("SELECT entry_hash FROM verification ORDER BY seq DESC LIMIT 1")
            last = await cur.fetchone()
            prev = last["entry_hash"] if last else GENESIS
            fields = chain_fields(
                address_id, method, score, freshness, evidence, verifier, verified_at
            )
            this_hash = entry_hash(prev, fields)
            await cur.execute(
                _INSERT,
                (
                    address_id,
                    method,
                    score,
                    freshness,
                    Json(evidence),
                    verifier,
                    prev,
                    this_hash,
                    verified_at,
                ),
            )
            return await cur.fetchone()


async def history_for_address(conn, address_id) -> list[dict]:
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT method, score, freshness, verifier, entry_hash, verified_at "
            "FROM verification WHERE address_id = %s ORDER BY seq ASC",
            (address_id,),
        )
        return await cur.fetchall()


async def integrity(conn) -> dict:
    """Walk the whole ledger and confirm the hash chain is intact."""
    async with conn.cursor() as cur:
        await cur.execute(_ALL_ORDERED)
        rows = await cur.fetchall()
    ok, broken_seq = verify_chain(rows)
    return {"ok": ok, "entries": len(rows), "broken_seq": broken_seq}
