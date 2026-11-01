"""FastAPI dependencies. Real objects are created in main.lifespan and stored on app.state;
tests replace them with app.dependency_overrides."""

from typing import Any

import httpx
from fastapi import Request

from rag_api.config import Settings, get_settings
from rag_api.events import EventBus
from rag_api.qdrant_read import QdrantReader
from rag_api.queue import JobQueue
from rag_api.s3 import ObjectStore


def settings_dep() -> Settings:
    return get_settings()


def get_queue(request: Request) -> JobQueue:
    q: JobQueue = request.app.state.queue
    return q


def get_events(request: Request) -> EventBus:
    bus: EventBus = request.app.state.events
    return bus


def get_store(request: Request) -> ObjectStore:
    store: ObjectStore = request.app.state.store
    return store


def get_qdrant(request: Request) -> QdrantReader:
    reader: QdrantReader = request.app.state.qdrant
    return reader


def get_http(request: Request) -> httpx.AsyncClient:
    client: httpx.AsyncClient = request.app.state.http
    return client


def get_redis(request: Request) -> Any:
    return request.app.state.redis
