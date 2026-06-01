from app.repositories import data as repo


async def coverage(conn) -> list[dict]:
    return await repo.coverage(conn)
