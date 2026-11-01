from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from rag_worker import ids
from rag_worker.config import get_settings
from rag_worker.models.registry import FakeModelSet
from tests.fakes import FakeApi, FakeObjectStore, FakePublisher

REPO_ROOT = Path(__file__).resolve().parents[3]  # /workspace
CONTRACTS = REPO_ROOT / "contracts"
FIXTURES = REPO_ROOT / "tests" / "contract_fixtures"
SAMPLES = REPO_ROOT / "tests" / "e2e" / "fixtures"
FROZEN = datetime(2026, 11, 1, 18, 22, 5, 123000, tzinfo=UTC)


@pytest.fixture
def frozen_now(monkeypatch: pytest.MonkeyPatch) -> datetime:
    monkeypatch.setattr(ids, "_clock", lambda: FROZEN)
    return FROZEN


@pytest.fixture
def ctx() -> dict[str, Any]:
    """arq-like job context wired to fakes (store, api, events) + FakeModelSet."""
    api = FakeApi()
    return {
        "settings": get_settings(),
        "store": FakeObjectStore(),
        "api": api,
        "events": FakePublisher(api.calls),
        "models": FakeModelSet(),
        "qdrant_url": get_settings().qdrant_url,
        "running": 0,
    }
