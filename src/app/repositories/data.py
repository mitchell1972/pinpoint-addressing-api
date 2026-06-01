async def coverage(conn) -> list[dict]:
    """Anonymised, aggregate-only coverage for the data product — counts per LGA,
    no individual records, no personal fields (spec §10 privacy / §8 data subscription)."""
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT lga, "
            "count(*)::int AS total, "
            "count(*) FILTER (WHERE status = 'verified')::int AS verified, "
            "round(avg(confidence)::numeric, 3)::float AS avg_confidence "
            "FROM address GROUP BY lga ORDER BY total DESC"
        )
        return await cur.fetchall()
