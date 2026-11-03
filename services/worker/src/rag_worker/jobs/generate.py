import asyncio
from typing import Any

from haystack.dataclasses import StreamingChunk

from rag_worker.components.context_builder import select_context
from rag_worker.contracts_gen.jobs.generate_schema import JobPayloadGenerate
from rag_worker.errors import WorkerError
from rag_worker.ids import to_iso, utcnow
from rag_worker.pipelines.generate import build_generate_pipeline, generate_artifact
from rag_worker.pipelines.prompts import ANSWER_SYSTEM
from rag_worker.report import StageReporter, run_stage


async def generate_body(
    job: JobPayloadGenerate, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/generate.schema.json and the generate summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    settings = ctx["settings"]
    store = ctx["store"]
    params = job.params
    src = await store.get_json(settings.s3_bucket_artifacts, job.context_artifact_key)
    entries = src["after"] if job.context_source == "rerank" else src["fused"]
    hits = [entry["hit"] for entry in entries]

    def _counts() -> tuple[list[int], int, int]:
        tok = ctx["models"].tokenizer("bge-m3")

        def count(text: str) -> int:
            return len(tok.encode(text, add_special_tokens=False).ids)

        return [count(h["content"]) for h in hits], count(ANSWER_SYSTEM), count(job.question)

    counts, system_tokens, question_tokens = await asyncio.to_thread(_counts)
    included, used, dropped = select_context(hits, counts, params.max_context_tokens)

    loop = asyncio.get_running_loop()
    index = 0

    def on_chunk(chunk: StreamingChunk) -> None:
        nonlocal index
        event = {
            "type": "generate.token",
            "run_id": job.run_id,
            "stage_run_id": job.stage_run_id,
            "stage": "generate",
            "version": job.version,
            "ts": to_iso(utcnow()),
            "index": index,
            "text": chunk.content,
        }
        index += 1
        asyncio.run_coroutine_threadsafe(ctx["events"].publish(job.run_id, event), loop)

    pipe = await asyncio.to_thread(
        build_generate_pipeline,
        job.chat,
        params.temperature,
        params.max_answer_tokens,
        ctx["models"],
        on_chunk,
    )
    try:
        out = await asyncio.to_thread(
            pipe.run,
            {
                "prompt": {
                    "context": [{"n": c["n"], "text": c["hit"]["content"]} for c in included],
                    "question": job.question,
                }
            },
            {"prompt", "llm"},
        )
    except Exception as e:
        raise WorkerError("LLM_ERROR", details={"exception": type(e).__name__}) from e

    reply = out["llm"]["replies"][0]
    answer = reply.text or ""
    usage = (reply.meta or {}).get("usage") or {}
    prompt_tokens = usage.get("prompt_tokens")
    completion_tokens = usage.get("completion_tokens")
    messages = [{"role": m.role.value, "content": m.text or ""} for m in out["prompt"]]
    budget = {
        "max_context_tokens": params.max_context_tokens,
        "system_tokens": system_tokens,
        "question_tokens": question_tokens,
        "used_context_tokens": used,
        "chunks_included": len(included),
        "chunks_dropped": dropped,
    }
    artifact = generate_artifact(
        job.chat,
        messages,
        budget,
        included,
        answer,
        {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    )
    summary = {
        "stage": "generate",
        "answer_chars": len(answer),
        "citations": len(artifact["citations"]),
        "chunks_included": len(included),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
    return artifact, summary


async def generate(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return await run_stage(ctx, payload, JobPayloadGenerate, generate_body)
