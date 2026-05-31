"""Async Postgres connection pool.

A single process-wide pool. `get_conn` is a FastAPI dependency; because FastAPI
caches dependency results per-request, the auth check and the controller share
one connection per request.
"""
from __future__ import annotations

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from .config import settings

_pool: AsyncConnectionPool | None = None


async def open_pool(dsn: str | None = None) -> AsyncConnectionPool:
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(
            dsn or settings.database_url,
            open=False,
            # autocommit so single statements commit immediately; multi-statement
            # writes use an explicit `async with conn.transaction()` block.
            kwargs={"autocommit": True, "row_factory": dict_row},
        )
        await _pool.open()
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_conn():
    pool = await open_pool()
    async with pool.connection() as conn:
        yield conn
