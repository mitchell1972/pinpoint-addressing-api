#!/usr/bin/env python3
"""Bulk-import addresses from a CSV into the address graph.

    python scripts/import_addresses.py [path/to/file.csv] [--source=osm]

Defaults to data/lagos_sample.csv. De-dupes by Plus Code, so re-running is safe.
"""

import asyncio
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from app.core.db import close_pool, open_pool  # noqa: E402
from app.services.importer import import_rows, parse_csv  # noqa: E402


async def _run(path: str, source: str) -> None:
    rows = parse_csv(pathlib.Path(path).read_text())
    pool = await open_pool()
    async with pool.connection() as conn:
        result = await import_rows(conn, rows, source)
    await close_pool()
    print(
        f"imported {result['inserted']}, skipped {result['skipped']} (source={source}, file={path})"
    )


def main() -> None:
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    source_flags = [a for a in sys.argv[1:] if a.startswith("--source=")]
    path = positional[0] if positional else str(ROOT / "data" / "lagos_sample.csv")
    source = source_flags[0].split("=", 1)[1] if source_flags else "osm"
    asyncio.run(_run(path, source))


if __name__ == "__main__":
    main()
