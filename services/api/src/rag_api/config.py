from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All api configuration. Read once from env vars (SYSTEM.md §6)."""

    model_config = SettingsConfigDict(extra="ignore")

    database_url: str
    redis_url: str
    s3_endpoint_url: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket_uploads: str = "uploads"
    s3_bucket_artifacts: str = "artifacts"
    qdrant_url: str
    internal_token: str
    ollama_url_default: str = "http://host.docker.internal:11434"
    max_upload_mb: int = 50
    max_files_per_batch: int = 20
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
