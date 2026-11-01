"""Stage failures. Raise WorkerError inside a job; run_stage turns it into a failed result
(contracts/shared/common.schema.json#/$defs/ErrorBody). Any other exception -> INTERNAL_ERROR."""

from typing import Any

type DetailValue = str | int | float | bool | None

# Codes a stage may fail with (contracts/shared/errors.json, "stage": true) -> default message.
STAGE_ERRORS: dict[str, str] = {
    "VALIDATION_ERROR": "Request body or parameters are invalid",
    "FILE_NOT_FOUND": "File not found",
    "ARTIFACT_NOT_FOUND": "Stage artifact not found",
    "UNSUPPORTED_FOR_STRATEGY": "This file type cannot be processed with the chosen strategy",
    "PARSE_FAILED": "Document conversion failed",
    "MODEL_NOT_AVAILABLE": "Model is not installed or not reachable",
    "LLM_ERROR": "Chat model call failed",
    "EMBEDDING_ERROR": "Embedding model call failed",
    "QDRANT_ERROR": "Qdrant request failed",
    "S3_ERROR": "S3 request failed",
    "INTERNAL_ERROR": "Unexpected error",
}


class WorkerError(Exception):
    def __init__(
        self, code: str, message: str | None = None, details: dict[str, DetailValue] | None = None
    ) -> None:
        if code not in STAGE_ERRORS:
            raise ValueError(f"unknown stage error code {code}")
        self.code = code
        self.message = message or STAGE_ERRORS[code]
        self.details: dict[str, DetailValue] = details or {}
        super().__init__(f"{code}: {self.message}")

    def error_body(self) -> dict[str, Any]:
        """ErrorBody: {'code', 'message', 'details'}."""
        return {"code": self.code, "message": self.message[:2000], "details": self.details}
