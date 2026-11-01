import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.schemas.settings import ModelCatalog


async def get_catalog(session: AsyncSession, http: httpx.AsyncClient) -> ModelCatalog:
    """GET {ollama_url}/api/tags (timeout 3 s). dense = catalog.DENSE_MODELS in catalog order;
    installed = some installed name == model or startswith(model + ':'). Ollama error ->
    ollama_reachable False, ollama_installed [], installed False everywhere."""
    raise NotImplementedError("not implemented")
