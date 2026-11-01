import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.schemas.settings import TestConnectionRequest, TestConnectionResult


async def test_connection(
    session: AsyncSession, http: httpx.AsyncClient, body: TestConnectionRequest
) -> TestConnectionResult:
    """Never raises for provider problems; timeout 10 s. Values: override fields when given
    (api_key None -> stored key), else stored settings.
    ollama: GET {url}/api/tags -> models = [m['name'] for m in models].
    anthropic: GET https://api.anthropic.com/v1/models, headers x-api-key + anthropic-version
    '2023-06-01' -> models = [d['id'] for d in data].
    openai_compatible: GET {base_url}/models, Authorization 'Bearer <key>' if key -> data[].id.
    Non-2xx -> ok False, detail 'HTTP <status>'; network error -> ok False, detail = str(exc)[:500];
    missing key/base_url -> ok False, detail 'not configured', latency 0."""
    raise NotImplementedError("not implemented")
