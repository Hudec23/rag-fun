-- api-private Postgres schema (database ragfun). NOT a contract: only the api touches it.
-- Source of truth for services/api/src/rag_api/db/models.py and the first Alembic migration
-- (services/api/alembic/versions/0001_initial.py). Every id is a UUIDv7 generated in Python.
-- Every timestamp is timestamptz in UTC.

CREATE TABLE batches (
    id          uuid PRIMARY KEY,
    name        varchar(200) NOT NULL,
    tags        text[]       NOT NULL DEFAULT '{}',          -- sorted, unique
    created_at  timestamptz  NOT NULL
);
CREATE INDEX ix_batches_created_at ON batches (created_at DESC, id DESC);

CREATE TABLE files (
    id          uuid PRIMARY KEY,
    batch_id    uuid         NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    filename    varchar(255) NOT NULL,
    mime        varchar(100) NOT NULL,
    size_bytes  bigint       NOT NULL CHECK (size_bytes > 0),
    sha256      char(64)     NOT NULL,
    s3_key      varchar(1024) NOT NULL,                       -- key in bucket uploads
    tags        text[]       NOT NULL DEFAULT '{}',
    created_at  timestamptz  NOT NULL
);
CREATE INDEX ix_files_batch ON files (batch_id);
CREATE INDEX ix_files_created ON files (created_at DESC, filename ASC);
CREATE INDEX ix_files_tags ON files USING gin (tags);

CREATE TABLE collections (
    id            uuid PRIMARY KEY,
    name          varchar(64)  NOT NULL UNIQUE,
    qdrant_name   varchar(35)  NOT NULL UNIQUE,               -- 'rf_' || replace(id::text, '-', '')
    dense_model   varchar(50)  NOT NULL,
    dense_dims    integer      NOT NULL CHECK (dense_dims IN (384, 768, 1024)),
    sparse_model  varchar(100) NOT NULL,
    created_at    timestamptz  NOT NULL
);

CREATE TABLE ingest_runs (
    id               uuid PRIMARY KEY,
    file_id          uuid        NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    collection_id    uuid        NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    run_all_plan     jsonb       NOT NULL DEFAULT '[]',       -- [{"stage": "chunk", "params": {...}}, ...] not yet started
    created_at       timestamptz NOT NULL
);
CREATE INDEX ix_ingest_runs_file ON ingest_runs (file_id);
CREATE INDEX ix_ingest_runs_collection ON ingest_runs (collection_id);

CREATE TABLE query_runs (
    id               uuid PRIMARY KEY,
    collection_id    uuid          NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    question         varchar(2000) NOT NULL,
    run_all_plan     jsonb         NOT NULL DEFAULT '[]',
    created_at       timestamptz   NOT NULL
);
CREATE INDEX ix_query_runs_collection ON query_runs (collection_id, created_at DESC);

-- One row per (re)run of a stage. run_id points to ingest_runs or query_runs depending on run_kind
-- (no FK: polymorphic; rows are deleted explicitly with their run).
CREATE TABLE stage_runs (
    id            uuid PRIMARY KEY,
    run_id        uuid        NOT NULL,
    run_kind      varchar(10) NOT NULL CHECK (run_kind IN ('ingest', 'query')),
    stage         varchar(20) NOT NULL CHECK (stage IN ('parse','chunk','embed','store','transform','retrieve','rerank','generate')),
    version       integer     NOT NULL CHECK (version >= 1),
    params        jsonb       NOT NULL,
    status        varchar(10) NOT NULL CHECK (status IN ('queued','running','done','failed','stale')),
    artifact_key  varchar(1024),
    summary       jsonb,
    error         jsonb,                                       -- ErrorBody
    created_at    timestamptz NOT NULL,
    started_at    timestamptz,
    finished_at   timestamptz,
    UNIQUE (run_id, stage, version)
);
CREATE INDEX ix_stage_runs_run ON stage_runs (run_id, stage, version DESC);

-- Single row key='app'. value shape (api-private; secrets in clear text, local single-user tool):
-- {"chat_provider": "ollama",
--  "ollama": {"url": "...", "chat_model": "qwen3:8b"},
--  "anthropic": {"model": "claude-sonnet-5-5", "api_key": null},
--  "openai_compatible": {"base_url": null, "model": null, "api_key": null},
--  "reranker_model": "Xenova/ms-marco-MiniLM-L-6-v2"}
CREATE TABLE settings (
    key         varchar(50) PRIMARY KEY,
    value       jsonb       NOT NULL,
    updated_at  timestamptz NOT NULL
);

CREATE TABLE pipeline_graphs (
    stage       varchar(20) NOT NULL,
    variant     varchar(40) NOT NULL,
    graph       jsonb       NOT NULL,                          -- contracts/shared/pipeline-graph.schema.json
    updated_at  timestamptz NOT NULL,
    PRIMARY KEY (stage, variant)
);
