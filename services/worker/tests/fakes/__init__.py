"""In-memory fakes for worker tests (no Redis, S3 or api needed)."""

import json
from typing import Any

from rag_worker.errors import WorkerError


class FakeObjectStore:
    """objects == {(bucket, key): bytes}. Missing key -> same WorkerError codes as S3ObjectStore."""

    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}

    async def get_bytes(self, bucket: str, key: str) -> bytes:
        if (bucket, key) not in self.objects:
            code = "FILE_NOT_FOUND" if bucket == "uploads" else "ARTIFACT_NOT_FOUND"
            raise WorkerError(code, details={"key": key})
        return self.objects[(bucket, key)]

    async def put_bytes(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        self.objects[(bucket, key)] = data

    async def get_json(self, bucket: str, key: str) -> Any:
        return json.loads(await self.get_bytes(bucket, key))

    async def put_json(self, bucket: str, key: str, obj: Any) -> None:
        self.objects[(bucket, key)] = json.dumps(obj, separators=(",", ":")).encode()


class FakeApi:
    """Records callbacks: started == [(stage_run_id, started_at)], results == [StageResult dict],
    graphs == [graph dict]. Set fail_results=True to make stage_result raise."""

    def __init__(self) -> None:
        self.started: list[tuple[str, str]] = []
        self.results: list[dict[str, Any]] = []
        self.graphs: list[dict[str, Any]] = []
        self.fail_results = False
        self.calls: list[str] = []

    async def stage_started(self, stage_run_id: str, started_at: str) -> None:
        self.calls.append("started")
        self.started.append((stage_run_id, started_at))

    async def stage_result(self, result: dict[str, Any]) -> None:
        self.calls.append("result")
        if self.fail_results:
            raise RuntimeError("api down")
        self.results.append(result)

    async def put_graph(self, graph: dict[str, Any]) -> None:
        self.graphs.append(graph)


class FakePublisher:
    """events == [(run_id, event)]; shares `calls` with a FakeApi when given, to assert ordering."""

    def __init__(self, calls: list[str] | None = None) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []
        self.calls = calls if calls is not None else []

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        self.calls.append(event["type"])
        self.events.append((run_id, event))

    def types(self) -> list[str]:
        return [e["type"] for _, e in self.events]
