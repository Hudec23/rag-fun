"""Collections (R-012). Example module for the house style: get_collection is implemented."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.catalog import DENSE_MODELS
from rag_api.db.models import CollectionRow, IngestRunRow, QueryRunRow, StageRunRow
from rag_api.errors import AppError
from rag_api.ids import new_id, to_iso, utcnow
from rag_api.queue import JobQueue
from rag_api.schemas.collections import CollectionCreate, CollectionList, CollectionOut


def to_out(row: CollectionRow) -> CollectionOut:
    return CollectionOut(
        id=row.id,
        name=row.name,
        qdrant_name=row.qdrant_name,
        dense_model=row.dense_model,
        dense_dims=row.dense_dims,
        sparse_model=row.sparse_model,
        created_at=to_iso(row.created_at),
    )


def qdrant_name_for(collection_id: str) -> str:
    return "rf_" + collection_id.replace("-", "")


def collection_ref(row: CollectionRow, ollama_url: str) -> dict[str, object]:
    """CollectionRef of contracts/shared/common.schema.json (used in job payloads)."""
    return {
        "id": row.id,
        "qdrant_name": row.qdrant_name,
        "dense": {"model": row.dense_model, "dims": row.dense_dims, "ollama_url": ollama_url},
        "sparse_model": row.sparse_model,
    }


async def load_collection(session: AsyncSession, collection_id: str) -> CollectionRow:
    row = await session.get(CollectionRow, collection_id)
    if row is None:
        raise AppError("COLLECTION_NOT_FOUND", details={"collection_id": collection_id})
    return row


async def get_collection(session: AsyncSession, collection_id: str) -> CollectionOut:
    return to_out(await load_collection(session, collection_id))


async def list_collections(session: AsyncSession) -> CollectionList:
    """All collections ordered by name ascending."""
    rows = (await session.scalars(select(CollectionRow).order_by(CollectionRow.name))).all()
    return CollectionList(items=[to_out(r) for r in rows])


async def create_collection(session: AsyncSession, body: CollectionCreate) -> CollectionOut:
    """Insert a row: id = new_id(), qdrant_name = qdrant_name_for(id), dense_dims from
    catalog.DENSE_MODELS[body.dense_model][0], created_at = utcnow(). Name already used ->
    AppError('COLLECTION_NAME_TAKEN', details={'name': name}). Flush (no commit) and return to_out."""
    existing = (
        await session.execute(select(CollectionRow).where(CollectionRow.name == body.name))
    ).scalar_one_or_none()
    if existing is not None:
        raise AppError("COLLECTION_NAME_TAKEN", details={"name": body.name})
    cid = new_id()
    row = CollectionRow(
        id=cid,
        name=body.name,
        qdrant_name=qdrant_name_for(cid),
        dense_model=body.dense_model,
        dense_dims=DENSE_MODELS[body.dense_model][0],
        sparse_model=body.sparse_model,
        created_at=utcnow(),
    )
    session.add(row)
    await session.flush()
    return to_out(row)


async def delete_collection(session: AsyncSession, queue: JobQueue, collection_id: str) -> None:
    """Load (404 COLLECTION_NOT_FOUND), delete stage_runs of its ingest + query runs, delete the row
    (runs cascade), flush, then enqueue('drop_collection', {'qdrant_name': ...}, 'query')."""
    row = await load_collection(session, collection_id)
    qdrant_name = row.qdrant_name
    ingest_ids = [
        run.id
        for run in (
            await session.scalars(
                select(IngestRunRow).where(IngestRunRow.collection_id == collection_id)
            )
        ).all()
    ]
    query_ids = [
        run.id
        for run in (
            await session.scalars(
                select(QueryRunRow).where(QueryRunRow.collection_id == collection_id)
            )
        ).all()
    ]
    run_ids = [*ingest_ids, *query_ids]
    if run_ids:
        await session.execute(delete(StageRunRow).where(StageRunRow.run_id.in_(run_ids)))
    await session.delete(row)
    await session.flush()
    await queue.enqueue("drop_collection", {"qdrant_name": qdrant_name}, "query")
