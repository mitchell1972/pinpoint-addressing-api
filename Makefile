# Convenience targets. Assumes a local virtualenv at .venv (see README).
.PHONY: venv up down init-db seed dev test lint format import e2e

venv:
	python3.11 -m venv .venv && .venv/bin/pip install -e ".[dev]"

up:
	docker compose up -d

down:
	docker compose down

init-db:        ## apply db/schema.sql to PINPOINT_DATABASE_URL
	.venv/bin/python scripts/init_db.py

seed:           ## apply schema + insert a demo account, API keys, and Lagos fixtures
	.venv/bin/python scripts/init_db.py --seed

import:         ## bulk-load the bundled Lagos sample into the dev DB
	.venv/bin/python scripts/import_addresses.py data/lagos_sample.csv

dev:            ## run the API with autoreload
	.venv/bin/uvicorn app.main:app --reload --app-dir src

test:           ## unit + integration (excludes browser E2E)
	.venv/bin/pytest -m "not e2e" -q

e2e:            ## browser end-to-end tests (first run: .venv/bin/playwright install chromium)
	.venv/bin/pytest -m e2e -q

lint:           ## what CI gates on: lint + formatting check (no changes written)
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .

format:         ## autofix lint + apply formatting in place
	.venv/bin/ruff check --fix .
	.venv/bin/ruff format .
