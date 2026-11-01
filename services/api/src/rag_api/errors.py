"""Shared error shape (contracts/shared/errors.json). Raise AppError; never build error dicts by hand."""

from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = structlog.get_logger()

type DetailValue = str | int | float | bool | None

# code -> (http status, default message). Must equal contracts/shared/errors.json (tested).
ERRORS: dict[str, tuple[int, str]] = {
    "VALIDATION_ERROR": (422, "Request body or parameters are invalid"),
    "UNAUTHORIZED": (401, "Missing or wrong X-Internal-Token"),
    "BATCH_NOT_FOUND": (404, "Batch not found"),
    "FILE_NOT_FOUND": (404, "File not found"),
    "COLLECTION_NOT_FOUND": (404, "Collection not found"),
    "RUN_NOT_FOUND": (404, "Ingest or query run not found"),
    "STAGE_RUN_NOT_FOUND": (404, "Stage run not found"),
    "ARTIFACT_NOT_FOUND": (404, "Stage artifact not found"),
    "PAGE_NOT_FOUND": (404, "Page image not found"),
    "POINT_NOT_FOUND": (404, "Qdrant point not found"),
    "PIPELINE_GRAPH_NOT_FOUND": (404, "No pipeline graph reported for this stage yet"),
    "EMPTY_UPLOAD": (400, "No files in upload"),
    "UNSUPPORTED_FILE_TYPE": (415, "File type is not supported"),
    "FILE_TOO_LARGE": (413, "File exceeds MAX_UPLOAD_MB"),
    "TOO_MANY_FILES": (413, "Batch exceeds MAX_FILES_PER_BATCH"),
    "COLLECTION_NAME_TAKEN": (409, "A collection with this name already exists"),
    "STAGE_PREREQUISITE_MISSING": (409, "The previous stage has no done version yet"),
    "STAGE_ALREADY_RUNNING": (409, "This stage is already queued or running for this run"),
    "UNSUPPORTED_FOR_STRATEGY": (
        422,
        "This file type cannot be processed with the chosen strategy",
    ),
    "PARSE_FAILED": (500, "Document conversion failed"),
    "MODEL_NOT_AVAILABLE": (502, "Model is not installed or not reachable"),
    "LLM_ERROR": (502, "Chat model call failed"),
    "EMBEDDING_ERROR": (502, "Embedding model call failed"),
    "QDRANT_ERROR": (503, "Qdrant request failed"),
    "S3_ERROR": (503, "S3 request failed"),
    "DEPENDENCY_UNAVAILABLE": (503, "A backing service is unavailable"),
    "INTERNAL_ERROR": (500, "Unexpected error"),
}


class AppError(Exception):
    def __init__(
        self, code: str, message: str | None = None, details: dict[str, DetailValue] | None = None
    ) -> None:
        if code not in ERRORS:
            raise ValueError(f"unknown error code {code}")
        self.code = code
        self.status = ERRORS[code][0]
        self.message = message or ERRORS[code][1]
        self.details: dict[str, DetailValue] = details or {}
        super().__init__(f"{code}: {self.message}")

    def body(self) -> dict[str, Any]:
        return error_body(self.code, self.message, self.details)


def error_body(
    code: str, message: str, details: dict[str, DetailValue] | None = None
) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def _field_path(loc: tuple[Any, ...]) -> str:
    parts = [str(p) for p in loc if p not in ("body", "query", "path", "header")]
    return ".".join(parts)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content=exc.body())

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errs = exc.errors()
        field = _field_path(tuple(errs[0]["loc"])) if errs else ""
        err = AppError("VALIDATION_ERROR", details={"field": field})
        return JSONResponse(status_code=422, content=err.body())

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        message = "Not found" if exc.status_code == 404 else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body("VALIDATION_ERROR", message, {"status": exc.status_code}),
        )

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error", exc_type=type(exc).__name__)
        return JSONResponse(status_code=500, content=AppError("INTERNAL_ERROR").body())
