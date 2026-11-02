"""Model catalog (F-status). Fixed catalog plus live ollama /api/tags install status."""

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.catalog import DENSE_MODELS, RERANK_MODELS, SPARSE_MODELS
from rag_api.schemas.settings import DenseCatalogEntry, ModelCatalog
from rag_api.services import app_settings

TAGS_TIMEOUT_S = 3.0


def _dense_entries(installed: list[str]) -> list[DenseCatalogEntry]:
    """DENSE_MODELS in catalog order; installed = some installed name == model or startswith(model + ':')."""
    entries: list[DenseCatalogEntry] = []
    for model, (dims, max_tokens) in DENSE_MODELS.items():
        installed_flag = any(name == model or name.startswith(model + ":") for name in installed)
        entries.append(
            DenseCatalogEntry(
                model=model, dims=dims, max_tokens=max_tokens, installed=installed_flag
            )
        )
    return entries


def _unreachable() -> ModelCatalog:
    return ModelCatalog(
        ollama_reachable=False,
        ollama_installed=[],
        dense=_dense_entries([]),
        sparse=SPARSE_MODELS,
        rerank=RERANK_MODELS,
    )


async def get_catalog(session: AsyncSession, http: httpx.AsyncClient) -> ModelCatalog:
    """GET {ollama_url}/api/tags (timeout 3 s). dense = catalog.DENSE_MODELS in catalog order;
    installed = some installed name == model or startswith(model + ':'). Ollama error ->
    ollama_reachable False, ollama_installed [], installed False everywhere."""
    url = await app_settings.ollama_url(session)
    try:
        resp = await http.get(f"{url}/api/tags", timeout=TAGS_TIMEOUT_S)
    except httpx.HTTPError:
        return _unreachable()
    if resp.status_code >= 400:
        return _unreachable()
    installed = [model["name"] for model in resp.json()["models"]]
    return ModelCatalog(
        ollama_reachable=True,
        ollama_installed=installed,
        dense=_dense_entries(installed),
        sparse=SPARSE_MODELS,
        rerank=RERANK_MODELS,
    )
