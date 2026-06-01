"""End-to-end harness: a real uvicorn server against a dedicated e2e database,
driven through a real browser (Playwright). Excluded from the default suite.
"""

import os
import pathlib
import subprocess
import sys
import time
import urllib.request

import psycopg
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
E2E_DSN = "postgresql://pinpoint:pinpoint@localhost:55432/pinpoint_e2e"
ADMIN_DSN = "postgresql://pinpoint:pinpoint@localhost:55432/postgres"
PORT = 8099
BASE_URL = f"http://127.0.0.1:{PORT}"


def _recreate_db() -> None:
    try:
        admin = psycopg.connect(ADMIN_DSN, autocommit=True)
    except psycopg.OperationalError:
        pytest.skip(
            "Postgres not reachable for E2E (run `docker compose up -d`).", allow_module_level=True
        )
    with admin, admin.cursor() as cur:
        cur.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            "WHERE datname = 'pinpoint_e2e' AND pid <> pg_backend_pid()"
        )
        cur.execute("DROP DATABASE IF EXISTS pinpoint_e2e")
        cur.execute("CREATE DATABASE pinpoint_e2e")


@pytest.fixture(scope="session")
def live_server():
    _recreate_db()
    env = {**os.environ, "PINPOINT_DATABASE_URL": E2E_DSN}

    # Schema + demo data (account, keys, Lagos fixtures) into the e2e database.
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "init_db.py"), "--seed"],
        env=env,
        cwd=str(ROOT),
        check=True,
    )

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--app-dir",
            "src",
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
            "--log-level",
            "warning",
        ],
        env=env,
        cwd=str(ROOT),
    )
    try:
        for _ in range(60):
            try:
                with urllib.request.urlopen(f"{BASE_URL}/health", timeout=1) as resp:
                    if resp.status == 200:
                        break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("E2E server did not become healthy in time")
        yield BASE_URL
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
