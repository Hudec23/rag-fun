from fastapi import APIRouter

from rag_api import VERSION
from rag_api.schemas.system import Health

router = APIRouter(tags=["system"])


@router.get("/health", response_model=Health)
async def get_health() -> Health:
    return Health(version=VERSION)
