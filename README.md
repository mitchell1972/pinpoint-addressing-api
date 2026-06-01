# Pinpoint Addressing API

MVP backend spine for **Pinpoint** — verified digital addresses + forward/reverse
geocoding and address verification for Nigerian logistics, e-commerce and fintech.
Scoped from [`Pinpoint_Addressing_API_Spec.docx`](Pinpoint_Addressing_API_Spec.docx).

This repo is the **backend spine only** (the spec's MVP phase, §12): the address
graph, geocoding, a stubbed verification surface, API-key auth, and usage metering.
The checkout widget, mobile SDKs and dispatch dashboard are deliberately out of scope here.

## Stack

- **FastAPI** (async) — JSON-Schema request/response contracts + OpenAPI at `/docs`.
- **PostGIS** — spatial source of truth; forward match via `pg_trgm`, reverse via KNN.
- **psycopg 3** (async pool) + **raw SQL** — no ORM; spatial queries read clearly as SQL.
- **pytest + httpx** — every test hits a real PostGIS database, no DB mocks.
- One external dependency for codes: **`openlocationcode`** (Google's Plus Code reference impl).

## Architecture

Layer-first MVC, one deployable. Request flow:

```
controller (HTTP)  ->  service (business logic)  ->  repository (SQL)  ->  PostGIS
                       schema (Pydantic) = the View / JSON serialization
```

How MVC maps onto a raw-SQL JSON API (no ORM, by design):

- **Model** → `repositories/` (all SQL) + `db/schema.sql`
- **View** → `schemas/` (Pydantic request/response models)
- **Controller** → `controllers/` (thin APIRouters — HTTP in/out only)
- **+ Service** → `services/` (business logic; the layer textbook MVC omits and then regrets)

```
src/app/
  main.py            app factory; router + middleware + error-handler wiring
  core/              config · db (async pool) · security (Principal) · errors
  lib/               olc · geohash · codes        (pure, stateless helpers)
  controllers/       addresses · geocode · verify · usage          (HTTP)
  services/          addresses · geocode · verify · metering · auth (logic)
  repositories/      addresses · geocode · verify · metering · auth (SQL = Model)
  schemas/           addresses · geocode · verify · metering        (DTOs = View)
  middleware/        metering   (usage_event capture + rate-limit headers)
  dependencies/      auth       (require_principal)
db/schema.sql        the 6-entity data model (§9.3)
test/                contract · integration · accuracy
```

We do **not** invent an address code — we wrap Plus Codes and add a human alias
`PIN-XXXX-XX` (§9.2). Every SQL statement lives in `repositories/`; services take a
connection handle and never touch the DB driver or the web framework directly.

## Quickstart

Requires Docker and Python 3.11+.

```bash
docker compose up -d            # Postgres + PostGIS on host :55432 (avoids a local :5432)
python3.11 -m venv .venv
.venv/bin/pip install -e ".[dev]"

.venv/bin/pytest -q             # run the suite (recreates a pinpoint_test DB)
make lint                       # ruff check + format --check (what CI gates on)

# Run the API against the dev DB:
.venv/bin/python scripts/init_db.py --seed     # schema + demo account/keys/fixtures
.venv/bin/uvicorn app.main:app --reload --app-dir src
# -> http://127.0.0.1:8000/docs
```

Demo keys (created by `--seed`): `pk_test_pinpoint_demo_0001`, `pk_live_pinpoint_demo_0001`.

```bash
curl -s localhost:8000/v1/geocode \
  -H "Authorization: Bearer pk_test_pinpoint_demo_0001" \
  -H "Content-Type: application/json" \
  -d '{"query":"silverbird galleria ahmadu bello way","area":{"state":"Lagos","lga":"Eti-Osa"}}'
```

## Endpoints (v1)

| Method | Path | Status |
|--------|------|--------|
| POST | `/v1/geocode` | implemented (pg_trgm + query cleaning) |
| POST | `/v1/reverse` | implemented (PostGIS KNN) |
| POST | `/v1/addresses` | implemented |
| GET  | `/v1/addresses/{code}` | implemented |
| POST | `/v1/verify` | MVP stub — existence + confidence; KYC writes a minimal record |
| POST | `/v1/batch/geocode` | implemented **synchronously** (real async queue is V1) |
| GET  | `/v1/usage` | implemented |

## Test layout

- `test/contract/` — per-endpoint shape + status-code contracts (auth, validation).
- `test/integration/` — service+repo against real PostGIS (address round-trip, metering).
- `test/accuracy/` — the **north-star**: forward-geocode top-candidate accuracy vs
  `test/fixtures/lagos-known-points.json`, target >90% (§11). Non-gating (`xfail`,
  strict=False). See the number + any misses with: `pytest test/accuracy -s`.
  **Caveat:** 16 examples is still small — 100% here is encouraging, not proof.

## Honest status / TODO

- **Geocoding = pg_trgm similarity + a query-normalisation step** (`lib/normalize.py`:
  short-forms like VI/unilag/bstop, number-words → digits, filler/pidgin removal).
  Scores 16/16 on the hard fixture set (was 15/16 without normalisation). The real
  next step is a **large, realistic dataset** — 16 examples can't tell you much — and
  then heavier matching (libpostal/embeddings) if the bigger set exposes gaps.
- **Verification is a stub.** No immutable evidence store, device/agent attestation, or
  re-verification yet (§6.3, §10) — V1.
- **Rate limiting is not enforced.** `X-RateLimit-*` headers are surfaced; a Redis token
  bucket is the next step.
- **Metering bills batch as one event**, not per query; resolve-by-code is unmetered.
- **Migrations are SQL-first** (`db/schema.sql`). Move to Alembic once the schema changes.
- **Layer-first MVC trade-off:** extracting one of the spec's §9.1 services later means
  gathering its controller/service/repository/schema from across four folders. A
  feature-first layout would localise that; this was a deliberate structure choice.
- **CI** (GitHub Actions, on every push/PR to `main`): a `lint` job (ruff check +
  format) and a `test` job (pytest against a real PostGIS service). Both must pass.
```
