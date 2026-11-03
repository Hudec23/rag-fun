"""parse job: read the upload from the store, run the parse pipeline for the strategy
(docling_layout / docling_ocr / plain_text), store page images + docling.json (docling strategies)
and the parse artifact, report per-page progress."""

import asyncio
import ctypes
import gc
from typing import Any

from haystack.core.errors import PipelineRuntimeError

from rag_worker import keys
from rag_worker.components.text_layout import assign_spans
from rag_worker.contracts_gen.jobs.parse_schema import JobPayloadParse
from rag_worker.errors import WorkerError
from rag_worker.pipelines.parse import build_parse_pipeline, run_parse
from rag_worker.report import StageReporter, run_stage


def _release_heap_memory() -> None:
    """Best-effort release of freed-but-kept heap memory (e.g. left by a previous heavy parse in the
    same process) so the next docling run has room to grow."""
    gc.collect()
    try:
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except OSError:
        pass


async def parse_body(
    job: JobPayloadParse, rep: StageReporter, ctx: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Returns (artifact, summary) — contracts/artifacts/parse.schema.json and the parse summary of
    contracts/shared/summary.schema.json. ctx keys: settings, store, api, events, models, qdrant_url,
    running."""
    _release_heap_memory()
    settings = ctx["settings"]
    store = ctx["store"]
    data = await store.get_bytes(settings.s3_bucket_uploads, job.file.s3_key)
    strategy = job.params.strategy
    params = job.params.model_dump()
    pipe = await asyncio.to_thread(build_parse_pipeline, strategy, params)
    try:
        res = await asyncio.to_thread(
            run_parse, pipe, strategy, data, job.file.mime, job.file.filename
        )
    except PipelineRuntimeError as e:
        # run_parse (docling) already maps pipeline errors to WorkerError('PARSE_FAILED'); the
        # plain_text path re-raises the component error wrapped in PipelineRuntimeError — re-raise
        # the documented WorkerError (e.g. UNSUPPORTED_FOR_STRATEGY from PlainTextConverter),
        # anything else is PARSE_FAILED.
        cause = e.__cause__
        if isinstance(cause, WorkerError):
            raise cause from e
        raise WorkerError("PARSE_FAILED", details={"reason": str(e)[:300]}) from e
    elements, full_text = assign_spans(res["elements"])

    page_images = res["page_images"]
    total = len(page_images)
    for i, (page_no, png) in enumerate(page_images.items(), start=1):
        await store.put_bytes(
            settings.s3_bucket_artifacts,
            keys.page_image_key(job.run_id, job.version, page_no),
            png,
            "image/png",
        )
        await rep.progress(i, total, f"page {i}/{total}")

    docling_key: str | None = None
    if res["docling_json"] is not None:
        docling_key = keys.docling_json_key(job.run_id, job.version)
        await store.put_bytes(
            settings.s3_bucket_artifacts,
            docling_key,
            res["docling_json"].encode("utf-8"),
            "application/json",
        )

    pages: list[dict[str, Any]] = []
    for page in res["pages"]:
        entry = dict(page)
        entry["image_key"] = (
            keys.page_image_key(job.run_id, job.version, page["page_no"])
            if page["page_no"] in page_images
            else None
        )
        pages.append(entry)

    artifact = {
        "schema_version": 1,
        "stage": "parse",
        "strategy": strategy,
        "file_id": job.file.file_id,
        "mime": job.file.mime,
        "ocr_used": res["ocr_used"],
        "pages": pages,
        "elements": elements,
        "full_text": full_text,
        "docling_json_key": docling_key,
    }
    summary = {
        "stage": "parse",
        "pages": len(pages),
        "elements": len(elements),
        "tables": sum(1 for element in elements if element["type"] == "table"),
        "pictures": sum(1 for element in elements if element["type"] == "picture"),
        "chars": len(full_text),
        "ocr_used": res["ocr_used"],
    }
    return artifact, summary


async def parse(ctx: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    return await run_stage(ctx, payload, JobPayloadParse, parse_body)
