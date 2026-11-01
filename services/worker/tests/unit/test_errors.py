import json

import pytest

from rag_worker.errors import STAGE_ERRORS, WorkerError
from tests.conftest import CONTRACTS


def test_stage_errors_match_contract() -> None:
    codes = json.loads((CONTRACTS / "shared/errors.json").read_text())["codes"]
    expected = {c: v["message"] for c, v in codes.items() if v["stage"]}
    assert STAGE_ERRORS == expected


def test_error_body_shape() -> None:
    body = WorkerError("UNSUPPORTED_FOR_STRATEGY", details={"mime": "image/png"}).error_body()
    assert body == {
        "code": "UNSUPPORTED_FOR_STRATEGY",
        "message": "This file type cannot be processed with the chosen strategy",
        "details": {"mime": "image/png"},
    }


def test_unknown_code_rejected() -> None:
    with pytest.raises(ValueError):
        WorkerError("BATCH_NOT_FOUND")
