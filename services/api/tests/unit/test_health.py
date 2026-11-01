import httpx

from rag_api import VERSION
from rag_api.main import create_app


async def test_health_returns_ok_and_version() -> None:
    app = create_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "api", "version": VERSION}


async def test_unknown_route_uses_error_shape() -> None:
    app = create_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/api/v1/nope")
    assert r.status_code == 404
    assert set(r.json()["error"]) == {"code", "message", "details"}
