-- Pinpoint MVP schema. Mirrors the spec §9.3 data model.
-- SQL-first and applied verbatim by the test fixture and scripts/init_db.py.
-- Versioned migrations (Alembic) are the upgrade path once the schema starts moving.

CREATE EXTENSION IF NOT EXISTS postgis;   -- spatial types, ST_DWithin, KNN
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- fuzzy text matching for forward geocode

-- Customer organisation (merchant / courier / bank).
CREATE TABLE IF NOT EXISTS account (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name        text NOT NULL,
    type        text NOT NULL CHECK (type IN ('merchant', 'courier', 'bank')),
    tier        text NOT NULL DEFAULT 'free',
    status      text NOT NULL DEFAULT 'active',
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- Scoped API keys. We store a SHA-256 hash, never the raw key; key_prefix is for display.
CREATE TABLE IF NOT EXISTS api_key (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id  uuid NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    key_hash    text NOT NULL UNIQUE,
    key_prefix  text NOT NULL,
    scope       text NOT NULL DEFAULT 'read',
    env         text NOT NULL CHECK (env IN ('test', 'live')),
    rate_limit  int  NOT NULL DEFAULT 60,   -- req/min, illustrative; enforcement is a TODO
    status      text NOT NULL DEFAULT 'active',
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS api_key_account_idx ON api_key (account_id);

-- Canonical verified location. lat/lng is the source of truth; geom is generated from it.
CREATE TABLE IF NOT EXISTS address (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code        text NOT NULL UNIQUE,             -- human alias, e.g. PIN-7F3K-QM
    olc         text NOT NULL,                    -- full Plus Code (interop, spec §9.2)
    alias       text,                             -- user-given name (home/shop/warehouse)
    lat         double precision NOT NULL,
    lng         double precision NOT NULL,
    geom        geometry(Point, 4326)
                GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(lng, lat), 4326)) STORED,
    geohash     text NOT NULL,
    state       text,
    lga         text,
    ward        text,
    confidence  real NOT NULL DEFAULT 0.5,
    status      text NOT NULL DEFAULT 'unverified',  -- unverified | verified
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS address_geom_gix     ON address USING gist (geom);
CREATE INDEX IF NOT EXISTS address_state_lga_idx ON address (state, lga);
CREATE INDEX IF NOT EXISTS address_alias_trgm    ON address USING gin (alias gin_trgm_ops);

-- Rider-useful detail kept off the hot canonical row.
CREATE TABLE IF NOT EXISTS address_metadata (
    address_id          uuid PRIMARY KEY REFERENCES address(id) ON DELETE CASCADE,
    landmark            text,
    building_desc       text,
    access_notes        text,
    frontage_photo_url  text,
    contact             text
);
CREATE INDEX IF NOT EXISTS address_metadata_landmark_trgm
    ON address_metadata USING gin (landmark gin_trgm_ops);
CREATE INDEX IF NOT EXISTS address_metadata_building_trgm
    ON address_metadata USING gin (building_desc gin_trgm_ops);

-- KYC/AML audit trail. MVP writes a minimal record; the full immutable evidence
-- store (capture, device, agent attestation) is V1 per spec §6.3 / §12.
CREATE TABLE IF NOT EXISTS verification (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    address_id   uuid NOT NULL REFERENCES address(id) ON DELETE CASCADE,
    method       text NOT NULL,
    evidence_url text,
    score        real NOT NULL,
    verified_at  timestamptz NOT NULL DEFAULT now(),
    verifier     text
);
CREATE INDEX IF NOT EXISTS verification_address_idx ON verification (address_id);

-- Per-call metering that drives billing counters (spec §9.3 usage_event).
CREATE TABLE IF NOT EXISTS usage_event (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id  uuid NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    endpoint    text NOT NULL,
    units       int  NOT NULL DEFAULT 1,
    cost        numeric(12, 4) NOT NULL DEFAULT 0,
    ts          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS usage_event_account_ts_idx ON usage_event (account_id, ts);
