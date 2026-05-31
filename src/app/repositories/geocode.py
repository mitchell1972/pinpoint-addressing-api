"""Geocoding queries.

MVP forward matching is Postgres-native: pg_trgm similarity over alias/landmark/
building_desc, optionally filtered by admin hierarchy. This is deliberately the
"boring" baseline — the place to layer libpostal/embeddings later when the
accuracy harness (test/accuracy) demands it. Reverse uses PostGIS KNN.
"""

# similarity() across the three matchable text fields; GREATEST is the row score.
_SIM = """
GREATEST(
    similarity(coalesce(m.landmark, ''), %(q)s),
    similarity(coalesce(m.building_desc, ''), %(q)s),
    similarity(coalesce(a.alias, ''), %(q)s)
)
"""

_FORWARD = f"""
SELECT a.code, a.olc, a.lat, a.lng, a.status, m.landmark,
       {_SIM} AS sim
FROM address a
LEFT JOIN address_metadata m ON m.address_id = a.id
-- ::text casts so Postgres can type the bind param in the `IS NULL` branch.
WHERE (%(state)s::text IS NULL OR a.state ILIKE %(state)s::text)
  AND (%(lga)s::text   IS NULL OR a.lga   ILIKE %(lga)s::text)
  AND {_SIM} > 0.05
ORDER BY sim DESC
LIMIT %(limit)s
"""

_REVERSE = """
SELECT a.code, a.olc, a.lat, a.lng, a.status, a.confidence, m.landmark,
       ST_Distance(
           a.geom::geography,
           ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography
       ) AS dist_m
FROM address a
LEFT JOIN address_metadata m ON m.address_id = a.id
WHERE ST_DWithin(
        a.geom::geography,
        ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)::geography,
        %(radius)s)
ORDER BY a.geom <-> ST_SetSRID(ST_MakePoint(%(lng)s, %(lat)s), 4326)
LIMIT %(limit)s
"""


async def forward_geocode(conn, query: str, state: str | None, lga: str | None, limit: int) -> list[dict]:
    async with conn.cursor() as cur:
        await cur.execute(_FORWARD, {"q": query, "state": state, "lga": lga, "limit": limit})
        return await cur.fetchall()


async def reverse_geocode(conn, lat: float, lng: float, limit: int, radius_m: int) -> list[dict]:
    async with conn.cursor() as cur:
        await cur.execute(_REVERSE, {"lat": lat, "lng": lng, "limit": limit, "radius": radius_m})
        return await cur.fetchall()
