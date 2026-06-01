#!/usr/bin/env python3
"""Tiny SQL migration runner (no ORM — this codebase is deliberately raw-SQL).

Applies db/schema.sql as the baseline, then any db/migrations/*.sql deltas in
filename order, each exactly once, tracked in a schema_migrations table. Safe to
re-run: the baseline uses IF NOT EXISTS, and applied files are skipped.

    python scripts/migrate.py
"""

import pathlib
import sys
import time

import psycopg

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from app.core.config import settings  # noqa: E402

SCHEMA = ROOT / "db" / "schema.sql"
MIGRATIONS_DIR = ROOT / "db" / "migrations"


def _connect(attempts: int = 30, delay: float = 1.0):
    """Connect, waiting for the database to accept connections (it may still be
    starting up at deploy time)."""
    last = None
    for _ in range(attempts):
        try:
            return psycopg.connect(settings.database_url, autocommit=True)
        except psycopg.OperationalError as exc:
            last = exc
            time.sleep(delay)
    raise last


def main() -> None:
    steps = [("baseline:schema.sql", SCHEMA)]
    if MIGRATIONS_DIR.exists():
        steps += [(p.name, p) for p in sorted(MIGRATIONS_DIR.glob("*.sql"))]

    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())"
        )
        for name, path in steps:
            cur.execute("SELECT 1 FROM schema_migrations WHERE name = %s", (name,))
            if cur.fetchone():
                print(f"skip    {name}")
                continue
            cur.execute(path.read_text())
            cur.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (name,))
            print(f"applied {name}")
    print(f"migrations up to date on {settings.database_url}")


if __name__ == "__main__":
    main()
