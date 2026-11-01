"""initial schema (plan/services/api.schema.sql)"""

from alembic import op

revision = "0001"
down_revision = None

DDL = """
CREATE TABLE batches (
    id uuid PRIMARY KEY, name varchar(200) NOT NULL, tags varchar[] NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL);
CREATE INDEX ix_batches_created_at ON batches (created_at DESC, id DESC);
CREATE TABLE files (
    id uuid PRIMARY KEY, batch_id uuid NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
    filename varchar(255) NOT NULL, mime varchar(100) NOT NULL,
    size_bytes bigint NOT NULL CONSTRAINT ck_files_size CHECK (size_bytes > 0),
    sha256 varchar(64) NOT NULL, s3_key varchar(1024) NOT NULL, tags varchar[] NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL);
CREATE INDEX ix_files_batch_id ON files (batch_id);
CREATE INDEX ix_files_created ON files (created_at DESC, filename ASC);
CREATE INDEX ix_files_tags ON files USING gin (tags);
CREATE TABLE collections (
    id uuid PRIMARY KEY, name varchar(64) NOT NULL UNIQUE, qdrant_name varchar(35) NOT NULL UNIQUE,
    dense_model varchar(50) NOT NULL,
    dense_dims integer NOT NULL CONSTRAINT ck_collections_dims CHECK (dense_dims IN (384, 768, 1024)),
    sparse_model varchar(100) NOT NULL, created_at timestamptz NOT NULL);
CREATE TABLE ingest_runs (
    id uuid PRIMARY KEY, file_id uuid NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    collection_id uuid NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    run_all_plan jsonb NOT NULL DEFAULT '[]', created_at timestamptz NOT NULL);
CREATE INDEX ix_ingest_runs_file_id ON ingest_runs (file_id);
CREATE INDEX ix_ingest_runs_collection_id ON ingest_runs (collection_id);
CREATE TABLE query_runs (
    id uuid PRIMARY KEY, collection_id uuid NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    question varchar(2000) NOT NULL, run_all_plan jsonb NOT NULL DEFAULT '[]',
    created_at timestamptz NOT NULL);
CREATE INDEX ix_query_runs_collection_id ON query_runs (collection_id, created_at DESC);
CREATE TABLE stage_runs (
    id uuid PRIMARY KEY, run_id uuid NOT NULL, run_kind varchar(10) NOT NULL,
    stage varchar(20) NOT NULL, version integer NOT NULL CONSTRAINT ck_stage_runs_version CHECK (version >= 1),
    params jsonb NOT NULL, status varchar(10) NOT NULL, artifact_key varchar(1024), summary jsonb,
    error jsonb, created_at timestamptz NOT NULL, started_at timestamptz, finished_at timestamptz,
    CONSTRAINT uq_stage_runs_version UNIQUE (run_id, stage, version));
CREATE INDEX ix_stage_runs_run_id ON stage_runs (run_id, stage, version DESC);
CREATE TABLE settings (key varchar(50) PRIMARY KEY, value jsonb NOT NULL, updated_at timestamptz NOT NULL);
CREATE TABLE pipeline_graphs (
    stage varchar(20) NOT NULL, variant varchar(40) NOT NULL, graph jsonb NOT NULL,
    updated_at timestamptz NOT NULL, PRIMARY KEY (stage, variant));
"""


def upgrade() -> None:
    for stmt in DDL.split(";"):
        if stmt.strip():
            op.execute(stmt)


def downgrade() -> None:
    for table in (
        "pipeline_graphs",
        "settings",
        "stage_runs",
        "query_runs",
        "ingest_runs",
        "collections",
        "files",
        "batches",
    ):
        op.execute(f"DROP TABLE IF EXISTS {table}")
