from typing import Any

from haystack import Document
from haystack_integrations.document_stores.qdrant.converters import convert_id

from rag_worker.contracts_gen.qdrant.payload_schema import Meta


def to_hit(doc: Document, rank: int, score: float | None = None) -> dict[str, Any]:
    """Retrieved Haystack Document -> Hit (contracts/shared/common.schema.json#/$defs/Hit):
    point_id = qdrant convert_id(doc.id), doc_id = doc.id, rank, score = score or doc.score or 0.0
    (round 6), content, meta = doc.meta (validated with Meta)."""
    Meta.model_validate(
        doc.meta
    )  # raises ValidationError for invalid meta; the raw dict carries over
    return {
        "point_id": convert_id(doc.id),
        "doc_id": doc.id,
        "rank": rank,
        "score": round(score or doc.score or 0.0, 6),
        "content": doc.content or "",
        "meta": doc.meta,
    }


def hit_to_document(hit: dict[str, Any]) -> Document:
    """Inverse for reranking: Document(id=doc_id, content, meta, score)."""
    return Document(
        id=hit["doc_id"],
        content=hit["content"],
        meta=hit["meta"],
        score=hit["score"],
    )
