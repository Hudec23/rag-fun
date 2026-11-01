"""Baseline: the stack is up and reachable through the web container's /api proxy."""

import os

import httpx


def test_api_health(api: httpx.Client) -> None:
    r = api.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_web_serves_ui_and_proxies_api() -> None:
    web = os.environ.get("E2E_WEB_URL", "http://web")
    assert httpx.get(f"{web}/").status_code == 200
    assert httpx.get(f"{web}/api/v1/health").json()["service"] == "api"
