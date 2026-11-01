from typing import Any

from haystack import Document, component


def table_documents(elements: list[dict[str, Any]], row_chunks: bool) -> list[Document]:
    """One Document per table element: content = table.markdown, meta element_ids [id], page_numbers
    [page_no] (or []), section_path, element_type 'table', split_idx_start = element char_start.
    row_chunks: additionally per data row (not header rows) a Document with content lines
    '<header>: <cell>' joined by '\\n' (header = header cell text of that column, or 'col<N>'),
    meta no_span True, element_type 'table'. Order: table chunk, then its row chunks."""
    raise NotImplementedError("not implemented")


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
        raise NotImplementedError("not implemented")
