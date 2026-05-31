from app.repositories import metering as repo


async def record(conn, account_id: str, endpoint: str) -> None:
    await repo.record_usage(conn, account_id, endpoint)


async def usage(conn, account_id: str) -> dict:
    rows = await repo.usage_by_endpoint(conn, account_id)
    return {
        "total_units": sum(r["units"] for r in rows),
        "total_calls": sum(r["calls"] for r in rows),
        "by_endpoint": rows,
    }
