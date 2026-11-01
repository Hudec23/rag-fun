"""F-settings (R-020)."""

import httpx


def _base(api: httpx.Client) -> dict:  # type: ignore[type-arg]
    s = api.get("/settings").json()
    return {
        "chat_provider": "ollama",
        "ollama": s["ollama"],
        "anthropic": {"model": s["anthropic"]["model"], "api_key": None},
        "openai_compatible": {"base_url": None, "model": None, "api_key": None},
        "reranker_model": s["reranker_model"],
    }


def test_keys_are_masked_kept_and_removed(api: httpx.Client) -> None:
    body = _base(api)
    body["anthropic"]["api_key"] = ""
    api.put("/settings", json=body)
    bad = {**body, "chat_provider": "anthropic", "anthropic": {"model": "claude-sonnet-5-5", "api_key": None}}
    r = api.put("/settings", json=bad)
    assert r.status_code == 422 and r.json()["error"]["details"]["field"] == "anthropic.api_key"
    good = {**body, "chat_provider": "anthropic", "anthropic": {"model": "claude-sonnet-5-5", "api_key": "sk-ant-secret-abcd"}}
    s = api.put("/settings", json=good).json()
    assert s["anthropic"] == {"model": "claude-sonnet-5-5", "api_key_set": True, "api_key_masked": "sk-…abcd"}
    assert "secret" not in api.get("/settings").text
    keep = {**good, "anthropic": {"model": "claude-sonnet-5-5", "api_key": None}}
    assert api.put("/settings", json=keep).json()["anthropic"]["api_key_set"] is True
    removed = {**body, "anthropic": {"model": "claude-sonnet-5-5", "api_key": ""}}
    assert api.put("/settings", json=removed).json()["anthropic"]["api_key_set"] is False


def test_openai_compatible_requires_url_and_model(api: httpx.Client) -> None:
    body = {**_base(api), "chat_provider": "openai_compatible"}
    r = api.put("/settings", json=body)
    assert r.status_code == 422 and r.json()["error"]["details"]["field"].startswith("openai_compatible.")
    body["openai_compatible"] = {"base_url": "http://host.docker.internal:1234/v1", "model": "local", "api_key": None}
    assert api.put("/settings", json=body).status_code == 200
    api.put("/settings", json=_base(api))


def test_connection_probe_never_raises(api: httpx.Client) -> None:
    r = api.post("/settings/test-connection", json={"target": "ollama"})
    assert r.status_code == 200
    res = r.json()
    assert res["target"] == "ollama" and res["ok"] is False and res["detail"] and res["models"] == []
    r = api.post("/settings/test-connection", json={"target": "openai_compatible",
                                                     "override": {"base_url": "http://api:8000/nothing", "api_key": None}})
    assert r.status_code == 200 and r.json()["ok"] is False
