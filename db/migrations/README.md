# Migrations

`db/schema.sql` is the baseline (idempotent — `CREATE ... IF NOT EXISTS`).

For schema changes after the baseline, add a numbered delta here:

```
db/migrations/0001_add_something.sql
db/migrations/0002_backfill_x.sql
```

`scripts/migrate.py` applies the baseline then each delta once (in filename
order), tracked in a `schema_migrations` table. Run it with `make migrate`, or it
runs automatically when the app container starts (see docker-compose `app`).

No ORM / Alembic on purpose: the app is raw-SQL, so a plain SQL runner keeps the
dependency surface small and the DDL transparent.
