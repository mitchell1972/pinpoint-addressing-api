# Pinpoint Addressing API

Verified digital addresses + geocoding, verification, analytics and an offline-tolerant
capture flow for Nigerian logistics, e-commerce and fintech. Scoped from
[`Pinpoint_Addressing_API_Spec.docx`](Pinpoint_Addressing_API_Spec.docx).

A B2B API with three web surfaces (dispatch dashboard, embeddable checkout widget,
field-capture PWA), a Python SDK, connector examples, and a Docker/CI-CD setup.

## Stack

- **FastAPI** (async) — JSON-Schema contracts + OpenAPI at `/docs`.
- **PostGIS** — spatial source of truth; forward match via `pg_trgm` + query cleaning, reverse via KNN.
- **psycopg 3** (async pool) + **raw SQL** — no ORM; spatial queries read clearly as SQL.
- **pytest + httpx** (real PostGIS, no mocks) and **Playwright** (browser E2E).
- **Docker** + a tiny SQL migration runner; **GitHub Actions** gates lint + tests + E2E and publishes the image.

## Architecture

Layer-first MVC, one deployable. Request flow:

```
controller (HTTP) -> service (business logic) -> repository (SQL) -> PostGIS
                     schema (Pydantic) = the View / JSON serialization
```

- **Model** → `repositories/` (all SQL) + `db/schema.sql`
- **View** → `schemas/` (Pydantic models)
- **Controller** → `controllers/` (thin APIRouters)
- **+ Service** → `services/` (business logic)

```
src/app/
  main.py            app factory; routers + middleware + error handlers
  core/              config · db (async pool) · security · errors · rate_limit
  lib/               olc · geohash · codes · normalize · scoring · ledger
  controllers/       addresses · geocode · verify · usage · accounts · imports
                     · analytics · sync · data
  services/          (one per controller) + auth
  repositories/      (all SQL)
  schemas/           (Pydantic DTOs)
  middleware/        idempotency · metering · audit
  dependencies/      auth (require_principal / require_admin)
  web/               dashboard/ · widget/ · capture/   (static surfaces)
db/schema.sql        canonical schema  ·  db/migrations/  deltas
clients/python/      Python SDK        ·  connectors/    platform examples
test/                unit · contract · integration · accuracy · e2e
```

We do **not** invent an address code — we wrap Plus Codes and add a human alias
`PIN-XXXX-XX`. Every SQL statement lives in `repositories/`.

## Quickstart

Requires Docker and Python 3.11+.

```bash
docker compose up -d                      # Postgres + PostGIS on host :55432
python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev]"

make test                                 # unit + integration (real PostGIS)
make lint                                 # ruff check + format (what CI gates on)
.venv/bin/playwright install chromium && make e2e   # browser E2E (first time installs the browser)

# Run it against the dev DB:
make seed                                 # schema + demo account/keys/fixtures
make import                               # bulk-load ~30 real Lagos points
make dev                                  # -> http://127.0.0.1:8000/docs
```

Or the **whole stack in one command** (builds the image, migrates, serves):

```bash
make compose-app                          # -> http://localhost:8000
```

Demo keys (from `make seed`): `pk_test_pinpoint_demo_0001` (read), `pk_test_pinpoint_admin_0001` (admin).

### Web surfaces

- `/docs` — interactive API docs
- `/dashboard/` — dispatch console (search, delivery analytics, record deliveries)
- `/widget/demo.html` — drop-in checkout address picker
- `/capture/` — offline-tolerant field capture (PWA)

## Endpoints (v1)

| Area | Endpoints |
|------|-----------|
| Geocoding | `POST /v1/geocode` · `POST /v1/reverse` · `POST /v1/batch/geocode` |
| Addresses | `POST /v1/addresses` · `GET /v1/addresses/{code}` · `POST /v1/addresses/{code}/claim` |
| Verification | `POST /v1/verify` (freshness/confidence; KYC writes a tamper-evident ledger entry) |
| Deliveries | `POST /v1/deliveries` · `GET /v1/analytics/summary` · `GET /v1/analytics/hotspots` |
| Offline | `POST /v1/sync` (idempotent per capture) |
| Metering | `GET /v1/usage` |
| Admin | `POST /v1/accounts` · `POST /v1/accounts/{id}/keys` · `POST /v1/keys/{id}/revoke` · `POST /v1/import` · `GET /v1/data/coverage` |
| Ops | `GET /health` · `GET /ready` |

Cross-cutting: per-key **rate limiting** (429 + Retry-After), **idempotency** (`Idempotency-Key`),
and a full **request audit log** with retention.

## Testing & CI

- `test/unit/` — pure logic (rate limiter, scoring, ledger, normalize, SDK), no DB.
- `test/contract/` + `test/integration/` — against real PostGIS.
- `test/accuracy/` — forward-geocode north-star vs `test/fixtures/` (`pytest test/accuracy -s`).
- `test/e2e/` — Playwright drives the dashboard, widget and capture page against a live server.

CI runs **lint**, **test** (`-m "not e2e"`) and **e2e** on every PR (all three required to merge to `main`),
and a **build-image** job that builds the Docker image and pushes it to GHCR on `main`.

## Deploy

- `Dockerfile` builds the app; the container runs `scripts/migrate.py` (waits for the DB,
  applies `db/schema.sql` + any `db/migrations/*.sql` deltas) then `uvicorn`.
- `docker compose --profile app up --build` runs the full stack locally.
- CI publishes `ghcr.io/<owner>/pinpoint-addressing-api:{latest,<sha>}` on `main`.
- Liveness `/health`, readiness `/ready`. Point a host (Fly/Render/ECS/K8s) at the image and
  set `PINPOINT_DATABASE_URL` — that final switch needs your hosting account.

## Honest status

What's real and tested vs. what genuinely remains:

- **Geocoding** is `pg_trgm` + query cleaning. It scores well on the small Lagos fixture set,
  but production accuracy needs a **large real dataset** (the importer + `/v1/import` are ready
  for it) and likely libpostal/embeddings. The accuracy harness exists to drive that.
- **No native mobile apps.** The `/capture` PWA (offline queue + deferred sync) stands in for
  the Android/iOS SDK; true native + on-device tiles is separate work.
- **Not hosted yet.** The image builds and publishes; pointing it at a real host + domain + TLS
  + managed Postgres is the operator step.
- **Rate limiting is in-process** (fine for one process; use Redis for multi-host).
- **Batch geocoding is synchronous** (a real async job queue is the next step for huge jobs).
- **Layer-first MVC trade-off:** extracting one of the spec's §9.1 services later means
  gathering its controller/service/repository/schema from across folders — a deliberate choice.
```
