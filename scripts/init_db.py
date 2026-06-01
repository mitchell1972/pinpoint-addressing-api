#!/usr/bin/env python3
"""Apply db/schema.sql to PINPOINT_DATABASE_URL, optionally with demo data.

    python scripts/init_db.py            # schema only
    python scripts/init_db.py --seed     # schema + demo account, keys, Lagos fixtures

Demo API keys (test/live):  pk_test_pinpoint_demo_0001 / pk_live_pinpoint_demo_0001
"""

import json
import pathlib
import sys

import psycopg

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))  # allow running without `pip install -e .`

from app.core.config import settings  # noqa: E402
from app.core.security import hash_key  # noqa: E402
from app.lib.geohash import encode as geohash_encode  # noqa: E402
from app.lib.olc import encode as olc_encode  # noqa: E402

SCHEMA = (ROOT / "db" / "schema.sql").read_text()
FIXTURES = json.loads((ROOT / "test" / "fixtures" / "lagos-known-points.json").read_text())

TEST_KEY = "pk_test_pinpoint_demo_0001"
LIVE_KEY = "pk_live_pinpoint_demo_0001"
ADMIN_KEY = "pk_test_pinpoint_admin_0001"  # scope=admin: account/key management


def seed(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO account (name, type, tier) VALUES (%s, %s, %s) RETURNING id",
            ("Demo Courier", "courier", "pro"),
        )
        account_id = cur.fetchone()[0]
        for raw, env, limit in ((TEST_KEY, "test", 60), (LIVE_KEY, "live", 120)):
            cur.execute(
                "INSERT INTO api_key (account_id, key_hash, key_prefix, env, rate_limit) "
                "VALUES (%s, %s, %s, %s, %s)",
                (account_id, hash_key(raw), raw[:16], env, limit),
            )
        cur.execute(
            "INSERT INTO api_key (account_id, key_hash, key_prefix, env, scope, rate_limit) "
            "VALUES (%s, %s, %s, 'test', 'admin', 1000)",
            (account_id, hash_key(ADMIN_KEY), ADMIN_KEY[:16]),
        )
        for f in FIXTURES:
            cur.execute(
                "INSERT INTO address (code, olc, alias, lat, lng, geohash, state, lga, confidence, status) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'verified') RETURNING id",
                (
                    f["code"],
                    olc_encode(f["lat"], f["lng"]),
                    f.get("alias"),
                    f["lat"],
                    f["lng"],
                    geohash_encode(f["lat"], f["lng"]),
                    f["state"],
                    f["lga"],
                    0.95,
                ),
            )
            address_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO address_metadata (address_id, landmark, building_desc) "
                "VALUES (%s, %s, %s)",
                (address_id, f.get("landmark"), f.get("building_desc")),
            )


def main() -> None:
    do_seed = "--seed" in sys.argv[1:]
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
        print(f"schema applied to {settings.database_url}")
        if do_seed:
            seed(conn)
            print(f"seeded demo account, 3 API keys (incl. admin), {len(FIXTURES)} Lagos addresses")


if __name__ == "__main__":
    main()
