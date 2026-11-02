"""Table-aware chunker (house style for components/): every table element becomes its own
Document (plus one per data row when row_chunks is on), each maximal run of consecutive
non-table elements is split recursively on chars, and the output stays in source order so
ChunkAnnotator can resolve spans from split_idx_start."""

from typing import Any

from haystack import Document, component
from haystack.components.preprocessors import RecursiveDocumentSplitter


def _rows(table: dict[str, Any]) -> dict[int, dict[int, dict[str, Any]]]:
    """Table cells indexed by {row: {col: cell}}."""
    rows: dict[int, dict[int, dict[str, Any]]] = {}
    for cell in table.get("cells") or []:
        rows.setdefault(cell["row"], {})[cell["col"]] = cell
    return rows


def _header_label(rows: dict[int, dict[int, dict[str, Any]]], col: int) -> str:
    """Text of the header cell of column col, or 'col<N>' when the column has none."""
    for cells in rows.values():
        header = cells.get(col)
        if header is not None and header.get("is_header") and header.get("text"):
            return str(header["text"])
    return f"col{col}"


def table_documents(elements: list[dict[str, Any]], row_chunks: bool) -> list[Document]:
    """One Document per table element: content = table.markdown, meta element_ids [id], page_numbers
    [page_no] (or []), section_path, element_type 'table', split_idx_start = element char_start.
    row_chunks: additionally per data row (not header rows) a Document with content lines
    '<header>: <cell>' joined by '\\n' (header = header cell text of that column, or 'col<N>'),
    meta no_span True, element_type 'table'. Order: table chunk, then its row chunks."""
    docs: list[Document] = []
    for el in elements:
        table = el.get("table") or {}
        docs.append(
            Document(
                content=table.get("markdown"),
                meta={
                    "element_type": "table",
                    "element_ids": [el["id"]],
                    "page_numbers": [el["page_no"]] if el.get("page_no") else [],
                    "section_path": list(el.get("section_path") or []),
                    "split_idx_start": el.get("char_start"),
                },
            )
        )
        if not row_chunks:
            continue
        rows = _rows(table)
        for cells in (rows[r] for r in sorted(rows)):
            if not cells or any(c.get("is_header") for c in cells.values()):
                continue
            lines = [
                f"{_header_label(rows, col)}: {cell['text']}" for col, cell in sorted(cells.items())
            ]
            if lines:
                docs.append(
                    Document(
                        content="\n".join(lines), meta={"no_span": True, "element_type": "table"}
                    )
                )
    return docs


def text_run_documents(
    splitter: RecursiveDocumentSplitter, run: list[dict[str, Any]]
) -> list[Document]:
    """One Document per chunk of one maximal non-table run: the run's texts concatenated are split
    by `splitter`, each chunk keeps its splitter split_idx_start offset by the run's char_start."""
    offset = run[0].get("char_start") or 0
    content = "".join(el.get("text") or "" for el in run)
    chunks = splitter.run(documents=[Document(content=content)])["documents"]
    return [
        Document(
            content=chunk.content, meta={"split_idx_start": offset + chunk.meta["split_idx_start"]}
        )
        for chunk in chunks
    ]


@component
class TableChunker:
    """Tables -> table_documents; non-table text -> RecursiveDocumentSplitter(split_length=
    text_length, split_overlap=text_overlap, split_unit='char') over each maximal run of consecutive
    non-table elements (as one Document with split_idx offset of the run). Output documents ordered
    by source position."""

    def __init__(self, row_chunks: bool, text_length: int, text_overlap: int) -> None:
        self.row_chunks = row_chunks
        self.text_length = text_length
        self.text_overlap = text_overlap

    @component.output_types(documents=list[Document])
    def run(self, elements: list[dict[str, Any]], source_text: str) -> dict[str, Any]:
        splitter = RecursiveDocumentSplitter(
            split_length=self.text_length,
            split_overlap=self.text_overlap,
            split_unit="char",
        )
        docs: list[Document] = []
        run: list[dict[str, Any]] = []
        for el in elements:
            if el.get("type") == "table":
                if run:
                    docs.extend(text_run_documents(splitter, run))
                    run = []
                docs.extend(table_documents([el], self.row_chunks))
            else:
                run.append(el)
        if run:
            docs.extend(text_run_documents(splitter, run))
        return {"documents": docs}
