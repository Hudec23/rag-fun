"""ArqJobQueue.enqueue against redis-test (REDIS_URL). Flush the db at the start of each test."""

import os
import re
from collections.abc import AsyncIterator

import pytest
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from rag_api.queue import ArqJobQueue


@pytest.fixture
async def pool() -> AsyncIterator[ArqRedis]:
    p = await create_pool(RedisSettings.from_dsn(os.environ["REDIS_URL"]))
    yield p
    await p.aclose()


async def test_enqueue_puts_job_on_named_queue(pool: ArqRedis) -> None:
    await pool.flushdb()
    queue = ArqJobQueue(pool)
    await queue.enqueue("chunk", {"stage_run_id": "x1", "a": 1}, "ingest")
    jobs = await pool.queued_jobs(queue_name="ingest")
    assert len(jobs) == 1
    assert jobs[0].function == "chunk"
    assert jobs[0].args == ({"stage_run_id": "x1", "a": 1},)
    assert jobs[0].kwargs == {}


async def test_enqueue_uses_stage_run_id_as_job_id(pool: ArqRedis) -> None:
    await pool.flushdb()
    queue = ArqJobQueue(pool)
    await queue.enqueue("chunk", {"stage_run_id": "x1", "a": 1}, "ingest")
    jobs = await pool.queued_jobs(queue_name="ingest")
    assert [job.job_id for job in jobs] == ["x1"]


async def test_duplicate_stage_run_id_enqueues_once(pool: ArqRedis) -> None:
    await pool.flushdb()
    queue = ArqJobQueue(pool)
    await queue.enqueue("chunk", {"stage_run_id": "x1", "a": 1}, "ingest")
    await queue.enqueue("chunk", {"stage_run_id": "x1", "a": 1}, "ingest")
    jobs = await pool.queued_jobs(queue_name="ingest")
    assert len(jobs) == 1
    assert jobs[0].job_id == "x1"


async def test_enqueue_without_stage_run_id_uses_generated_id(pool: ArqRedis) -> None:
    await pool.flushdb()
    queue = ArqJobQueue(pool)
    payload = {"qdrant_name": "rf_019a4b2c1d007b0080000000000000aa"}
    await queue.enqueue("drop_collection", payload, "query")
    jobs = await pool.queued_jobs(queue_name="query")
    assert len(jobs) == 1
    assert jobs[0].function == "drop_collection"
    assert jobs[0].args == (payload,)
    assert re.fullmatch(r"[0-9a-f]{32}", jobs[0].job_id or "") is not None
    assert await pool.queued_jobs(queue_name="ingest") == []
