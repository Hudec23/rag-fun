"""Example custom Haystack component (house style for components/): one class per file,
@component, typed output_types, pure logic in module-level helpers so it is easy to unit test."""

import math
from typing import Any

from haystack import Document, component

from rag_worker.keys import doc_id


def overlapping(elements: list[dict[str, Any]], start: int, end: int) -> list[dict[str, Any]]:
    """Parse elements whose [char_start, char_end) intersects [start, end)."""
    out = []
    for el in elements:
        s, e = el.get("char_start"), el.get("char_end")
        if s is not None and e is not None and s < end and start < e:
            out.append(el)
    return out


def element_type_of(elements: list[dict[str, Any]]) -> str:
    """table only -> 'table'; table + other -> 'mixed'; only OCR text -> 'image_ocr'; else 'text'."""
    if not elements:
        return "text"
    tables = [e for e in elements if e["type"] == "table"]
    if tables and len(tables) == len(elements):
        return "table"
    if tables:
        return "mixed"
    if all(e.get("from_ocr") for e in elements):
        return "image_ocr"
    return "text"


def locate(source_text: str, text: str, hint: int | None, search_from: int) -> int | None:
    """Start offset of `text` in source_text: the hint if it matches, else first match at or after
    search_from, else None."""
    if hint is not None and source_text[hint : hint + len(text)] == text:
        return hint
    found = source_text.find(text, search_from)
    return found if found >= 0 else None


@component
class ChunkAnnotator:
    """Split Documents -> chunk dicts of contracts/artifacts/chunk.schema.json#/$defs/Chunk.

    Spans come from doc.meta['split_idx_start'] (Haystack splitters) or a search in source_text.
    A splitter may preset meta 'element_ids', 'page_numbers', 'section_path', 'element_type' and
    'no_span' (True = text is not a substring of source_text); preset values win."""

    @component.output_types(chunks=list[dict[str, Any]])
    def run(
        self,
        documents: list[Document],
        elements: list[dict[str, Any]],
        source_text: str,
        file_id: str,
    ) -> dict[str, Any]:
        chunks: list[dict[str, Any]] = []
        cursor = 0
        index = 0
        for doc in documents:
            text = doc.content or ""
            if not text.strip():
                continue
            meta = doc.meta
            start = (
                None
                if meta.get("no_span")
                else locate(source_text, text, meta.get("split_idx_start"), cursor)
            )
            end = start + len(text) if start is not None else None
            if start is not None:
                cursor = start + 1
            hits = (
                overlapping(elements, start, end) if start is not None and end is not None else []
            )
            element_ids = meta.get("element_ids") or [e["id"] for e in hits]
            pages = meta.get("page_numbers") or sorted(
                {e["page_no"] for e in hits if e.get("page_no")}
            )
            section = meta.get("section_path") or (hits[0]["section_path"] if hits else [])
            chunks.append(
                {
                    "index": index,
                    "doc_id": doc_id(file_id, index),
                    "text": text,
                    "char_start": start,
                    "char_end": end,
                    "element_ids": list(element_ids),
                    "page_numbers": list(pages),
                    "section_path": list(section)[:10],
                    "element_type": meta.get("element_type") or element_type_of(hits),
                    "char_count": len(text),
                    "token_estimate": max(1, math.ceil(len(text) / 4)),
                }
            )
            index += 1
        return {"chunks": chunks}
