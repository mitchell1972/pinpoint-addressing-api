"""Test harness: a real PostGIS database, no mocks.

Session: drop+recreate `pinpoint_test` and apply db/schema.sql.
Per test: open the pool, TRUNCATE, and seed a demo account, two API keys, and
the Lagos ground-truth fixtures. Requires `docker compose up -d` first.
"""
import hashlib
import json
import os
import pathlib
import sys

import psycopg
import pytest
import pytest_asyncio

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "src"))  # ensure `app` importable regardless of install

TEST_DSN = "postgresql://pinpoint:pinpoint@localhost:55432/pinpoint_test"
ADMIN_DSN = "postgresql://pinpoint:pinpoint@localhost:55432/postgres"
os.environ["PINPOINT_DATABASE_URL"] = TEST_DSN  # set before any app import

from app.lib.geohash import encode as geohash_encode  # noqa: E402
from app.lib.olc import encode as olc_encode  # noqa: E402

SCHEMA = (ROOT / "db" / "schema.sql").read_text()
FIXTURES = json.loads((HERE / "fixtures" / "lagos-known-points.json").read_text())

TEST_KEY = "pk_test_pinpoint_demo_0001"
LIVE_KEY = "pk_live_pinpoint_demo_0001"


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


@pytest.fixture(scope="session", autouse=True)
def _create_test_db():
    try:
        admin = psycopg.connect(ADMIN_DSN, autocommit=True)
    except psycopg.OperationalError as e:
        pytest.exit(
            f"Postgres not reachable at {ADMIN_DSN}.\n"
            f"Run `docker compose up -d` and wait for the container to be healthy, then re-run.\n{e}",
            returncode=1,
        )
    with admin:
        with admin.cursor() as cur:
            cur.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = 'pinpoint_test' AND pid <> pg_backend_pid()"
            )
            cur.execute("DROP DATABASE IF EXISTS pinpoint_test")
            cur.execute("CREATE DATABASE pinpoint_test")
    with psycopg.connect(TEST_DSN, autocommit=True) as db:
        with db.cursor() as cur:
            cur.execute(SCHEMA)
    yield


async def _seed() -> None:
    from app.core.db import open_pool

    pool = await open_pool(TEST_DSN)
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "TRUNCATE address, address_metadata, verification, account, api_key, usage_event "
                "RESTART IDENTITY CASCADE"
            )
            await cur.execute(
                "INSERT INTO account (name, type, tier) VALUES (%s, %s, %s) RETURNING id",
                ("Demo Courier", "courier", "pro"),
            )
            account_id = (await cur.fetchone())["id"]
            await cur.execute(
                "INSERT INTO api_key (account_id, key_hash, key_prefix, env, rate_limit) "
                "VALUES (%s, %s, %s, 'test', 60)",
                (account_id, _sha(TEST_KEY), TEST_KEY[:16]),
            )
            await cur.execute(
                "INSERT INTO api_key (account_id, key_hash, key_prefix, env, rate_limit) "
                "VALUES (%s, %s, %s, 'live', 120)",
                (account_id, _sha(LIVE_KEY), LIVE_KEY[:16]),
            )
            for f in FIXTURES:
                await cur.execute(
                    "INSERT INTO address (code, olc, alias, lat, lng, geohash, state, lga, confidence, status) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'verified') RETURNING id",
                    (f["code"], olc_encode(f["lat"], f["lng"]), f.get("alias"),
                     f["lat"], f["lng"], geohash_encode(f["lat"], f["lng"]),
                     f["state"], f["lga"], 0.95),
                )
                address_id = (await cur.fetchone())["id"]
                await cur.execute(
                    "INSERT INTO address_metadata (address_id, landmark, building_desc) "
                    "VALUES (%s, %s, %s)",
                    (address_id, f.get("landmark"), f.get("building_desc")),
                )


@pytest_asyncio.fixture
async def client(_create_test_db):
    from httpx import ASGITransport, AsyncClient

    from app.core.db import close_pool, open_pool
    from app.main import app

    await open_pool(TEST_DSN)
    await _seed()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await close_pool()


@pytest.fixture
def test_auth() -> dict:
    return {"Authorization": f"Bearer {TEST_KEY}"}


@pytest.fixture
def live_auth() -> dict:
    return {"Authorization": f"Bearer {LIVE_KEY}"}


@pytest.fixture
def fixtures() -> list:
    return FIXTURES
