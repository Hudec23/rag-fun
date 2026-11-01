"""In-memory fakes for unit and integration tests. Use these instead of Redis/arq/S3 in api tests."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from rag_api.s3 import ObjectNotFound


class FakeJobQueue:
    """Records every enqueue: jobs == [(function, payload, queue), ...]."""

    def __init__(self) -> None:
        self.jobs: list[tuple[str, dict[str, Any], str]] = []

    async def enqueue(self, function: str, payload: dict[str, Any], queue: str) -> None:
        self.jobs.append((function, payload, queue))

    def functions(self) -> list[str]:
        return [j[0] for j in self.jobs]


class FakeEventBus:
    """published == [(run_id, event), ...]; subscribe() yields events published afterwards."""

    def __init__(self) -> None:
        self.published: list[tuple[str, dict[str, Any]]] = []
        self._subs: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        self.published.append((run_id, event))
        for q in self._subs.get(run_id, []):
            q.put_nowait(event)

    async def subscribe(self, run_id: str) -> AsyncIterator[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._subs.setdefault(run_id, []).append(q)
        try:
            while True:
                yield await q.get()
        finally:
            self._subs[run_id].remove(q)

    def types(self, run_id: str | None = None) -> list[str]:
        return [e["type"] for r, e in self.published if run_id is None or r == run_id]


class FakeObjectStore:
    """objects == {(bucket, key): (data, content_type)}; buckets == set of ensured buckets."""

    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], tuple[bytes, str]] = {}
        self.buckets: set[str] = set()
        self.fail: bool = False  # set True to make every call raise RuntimeError

    def _check(self) -> None:
        if self.fail:
            raise RuntimeError("fake s3 down")

    async def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        self._check()
        self.objects[(bucket, key)] = (data, content_type)

    async def get_bytes(self, bucket: str, key: str) -> bytes:
        self._check()
        if (bucket, key) not in self.objects:
            raise ObjectNotFound(key)
        return self.objects[(bucket, key)][0]

    async def delete(self, bucket: str, key: str) -> None:
        self._check()
        self.objects.pop((bucket, key), None)

    async def ensure_bucket(self, bucket: str) -> None:
        self._check()
        self.buckets.add(bucket)

    async def head_bucket(self, bucket: str) -> None:
        self._check()
        if bucket not in self.buckets:
            raise RuntimeError(f"no bucket {bucket}")
