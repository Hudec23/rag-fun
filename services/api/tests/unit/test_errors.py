"""Example unit test file — house style: plain async functions, one behaviour per test, exact asserts."""

import json

import httpx
import pytest
from fastapi import FastAPI
from pydantic import BaseModel

from rag_api.errors import ERRORS, AppError, install_error_handlers
from tests.conftest import CONTRACTS


def test_error_table_matches_contract() -> None:
    contract = json.loads((CONTRACTS / "shared/errors.json").read_text())["codes"]
    assert {code: (c["http"], c["message"]) for code, c in contract.items()} == ERRORS


def test_app_error_defaults_message_and_status() -> None:
    err = AppError("FILE_NOT_FOUND", details={"file_id": "x"})
    assert err.status == 404
    assert err.body() == {
        "error": {
            "code": "FILE_NOT_FOUND",
            "message": "File not found",
            "details": {"file_id": "x"},
        }
    }


def test_unknown_code_is_rejected() -> None:
    with pytest.raises(ValueError):
        AppError("NOPE")


class _Body(BaseModel):
    n: int


def _app() -> FastAPI:
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/boom")
    async def boom() -> None:
        raise AppError("STAGE_ALREADY_RUNNING", details={"stage": "chunk"})

    @app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("secret internals")

    @app.post("/body")
    async def body(b: _Body) -> int:
        return b.n

    return app


async def _call(method: str, path: str, **kw: object) -> httpx.Response:
    transport = httpx.ASGITransport(app=_app(), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        return await c.request(method, path, **kw)  # type: ignore[arg-type]


async def test_app_error_handler_returns_status_and_shape() -> None:
    r = await _call("GET", "/boom")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "STAGE_ALREADY_RUNNING"
    assert r.json()["error"]["details"] == {"stage": "chunk"}


async def test_validation_error_reports_field_path() -> None:
    r = await _call("POST", "/body", json={"n": "x"})
    assert r.status_code == 422
    assert r.json()["error"] == {
        "code": "VALIDATION_ERROR",
        "message": "Request body or parameters are invalid",
        "details": {"field": "n"},
    }


async def test_unexpected_exception_is_500_without_internals() -> None:
    r = await _call("GET", "/crash")
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "secret" not in r.text
