from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All worker configuration, from env vars (SYSTEM.md §6)."""

    model_config = SettingsConfigDict(extra="ignore")

    redis_url: str
    s3_endpoint_url: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket_uploads: str = "uploads"
    s3_bucket_artifacts: str = "artifacts"
    qdrant_url: str
    internal_token: str
    api_internal_url: str
    model_backend: Literal["real", "fake"] = "real"
    worker_queue: Literal["ingest", "query"] = "ingest"
    log_level: str = "INFO"
    models_dir: str = "/opt/models"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
