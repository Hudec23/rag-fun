"""ORM tables. Mirrors plan/services/api.schema.sql exactly."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _uuid() -> Any:
    return UUID(as_uuid=False)


def _ts() -> Any:
    return DateTime(timezone=True)


class BatchRow(Base):
    __tablename__ = "batches"
    id: Mapped[str] = mapped_column(_uuid(), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(_ts())


class FileRow(Base):
    __tablename__ = "files"
    __table_args__ = (CheckConstraint("size_bytes > 0", name="ck_files_size"),)
    id: Mapped[str] = mapped_column(_uuid(), primary_key=True)
    batch_id: Mapped[str] = mapped_column(
        _uuid(), ForeignKey("batches.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(255))
    mime: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(String(64))
    s3_key: Mapped[str] = mapped_column(String(1024))
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(_ts())


class CollectionRow(Base):
    __tablename__ = "collections"
    __table_args__ = (
        CheckConstraint("dense_dims IN (384, 768, 1024)", name="ck_collections_dims"),
    )
    id: Mapped[str] = mapped_column(_uuid(), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    qdrant_name: Mapped[str] = mapped_column(String(35), unique=True)
    dense_model: Mapped[str] = mapped_column(String(50))
    dense_dims: Mapped[int] = mapped_column(Integer)
    sparse_model: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(_ts())


class IngestRunRow(Base):
    __tablename__ = "ingest_runs"
    id: Mapped[str] = mapped_column(_uuid(), primary_key=True)
    file_id: Mapped[str] = mapped_column(
        _uuid(), ForeignKey("files.id", ondelete="CASCADE"), index=True
    )
    collection_id: Mapped[str] = mapped_column(
        _uuid(), ForeignKey("collections.id", ondelete="CASCADE"), index=True
    )
    # [{"stage": "chunk", "params": {...}}, ...] — planned stages not yet started
    run_all_plan: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, server_default="[]"
    )
    created_at: Mapped[datetime] = mapped_column(_ts())


class QueryRunRow(Base):
    __tablename__ = "query_runs"
    id: Mapped[str] = mapped_column(_uuid(), primary_key=True)
    collection_id: Mapped[str] = mapped_column(
        _uuid(), ForeignKey("collections.id", ondelete="CASCADE"), index=True
    )
    question: Mapped[str] = mapped_column(String(2000))
    run_all_plan: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, server_default="[]"
    )
    created_at: Mapped[datetime] = mapped_column(_ts())


class StageRunRow(Base):
    __tablename__ = "stage_runs"
    __table_args__ = (
        UniqueConstraint("run_id", "stage", "version", name="uq_stage_runs_version"),
        CheckConstraint("version >= 1", name="ck_stage_runs_version"),
    )
    id: Mapped[str] = mapped_column(_uuid(), primary_key=True)
    run_id: Mapped[str] = mapped_column(_uuid(), index=True)
    run_kind: Mapped[str] = mapped_column(String(10))  # ingest | query
    stage: Mapped[str] = mapped_column(String(20))
    version: Mapped[int] = mapped_column(Integer)
    params: Mapped[dict[str, Any]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(10))  # queued|running|done|failed|stale
    artifact_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)  # ErrorBody
    created_at: Mapped[datetime] = mapped_column(_ts())
    started_at: Mapped[datetime | None] = mapped_column(_ts(), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(_ts(), nullable=True)


class SettingsRow(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(_ts())


class PipelineGraphRow(Base):
    __tablename__ = "pipeline_graphs"
    stage: Mapped[str] = mapped_column(String(20), primary_key=True)
    variant: Mapped[str] = mapped_column(String(40), primary_key=True)
    graph: Mapped[dict[str, Any]] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(_ts())
