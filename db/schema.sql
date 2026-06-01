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
    confidence         real NOT NULL DEFAULT 0.5,
    status             text NOT NULL DEFAULT 'unverified',  -- unverified | verified
    last_verified_at   timestamptz,                         -- last KYC re-verification
    verification_count int NOT NULL DEFAULT 0,              -- feedback loop / freshness
    owner_account_id   uuid REFERENCES account(id),         -- merchant who claimed it
    source             text NOT NULL DEFAULT 'manual',      -- provenance: manual|import|osm|claim
    consent            boolean NOT NULL DEFAULT false,       -- consent to store this location (NDPR)
    created_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS address_geom_gix     ON address USING gist (geom);
CREATE INDEX IF NOT EXISTS address_owner_idx    ON address (owner_account_id);
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

-- Append-only, tamper-evident verification ledger (KYC/AML, spec §6.3 / §10).
-- Each row hash-chains to the previous (entry_hash = sha256(prev_hash | fields)),
-- so editing or deleting any past row breaks every hash after it. score/freshness
-- are double precision so the chain re-verifies exactly after a DB round-trip.
-- The address FK is intentionally NOT cascade-delete: the trail outlives the address.
CREATE TABLE IF NOT EXISTS verification (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    seq         bigserial,
    address_id  uuid NOT NULL REFERENCES address(id),
    method      text NOT NULL,
    score       double precision NOT NULL,
    freshness   double precision NOT NULL DEFAULT 0,
    evidence    jsonb NOT NULL DEFAULT '{}'::jsonb,
    verifier    text,
    prev_hash   text NOT NULL,
    entry_hash  text NOT NULL,
    verified_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS verification_address_idx ON verification (address_id);
CREATE INDEX IF NOT EXISTS verification_seq_idx ON verification (seq);

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

-- Idempotency: first successful response for an Idempotency-Key is stored and
-- replayed on repeat, so a double-submit can't create duplicates. Scope is the
-- hashed API credential, keeping keys isolated per caller (spec §10).
CREATE TABLE IF NOT EXISTS idempotency_key (
    scope               text NOT NULL,   -- sha256 of the Authorization header
    idem_key            text NOT NULL,
    method              text NOT NULL,
    path                text NOT NULL,
    response_status     int  NOT NULL,
    response_body       text NOT NULL,
    response_media_type text NOT NULL DEFAULT 'application/json',
    created_at          timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (scope, idem_key)
);

-- Delivery outcomes per address — drives failed-drop rate, time-to-locate and
-- hotspots, and feeds the confidence loop (spec §6.5, §11).
CREATE TABLE IF NOT EXISTS delivery_event (
    id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    address_id             uuid NOT NULL REFERENCES address(id),
    account_id             uuid NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    status                 text NOT NULL CHECK (status IN ('delivered', 'failed')),
    reason                 text,
    time_to_locate_seconds int,
    created_at             timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS delivery_event_account_idx ON delivery_event (account_id);
CREATE INDEX IF NOT EXISTS delivery_event_address_idx ON delivery_event (address_id);

-- Deferred-sync ledger for offline capture: maps a client-generated capture_id
-- to the address it created, so re-syncing a queued batch is idempotent (the
-- server is authoritative — spec §9.7).
CREATE TABLE IF NOT EXISTS captured_address (
    capture_id  uuid PRIMARY KEY,
    address_id  uuid NOT NULL REFERENCES address(id),
    account_id  uuid NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    created_at  timestamptz NOT NULL DEFAULT now()
);

-- Full API request audit log with a retention policy (spec §10 auditability/privacy).
CREATE TABLE IF NOT EXISTS request_log (
    id          bigserial PRIMARY KEY,
    account_id  uuid,                              -- null when unauthenticated
    method      text NOT NULL,
    path        text NOT NULL,
    status      int  NOT NULL,
    ts          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS request_log_ts_idx ON request_log (ts);
