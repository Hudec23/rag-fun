"""Unit tests for StructureChunker and TokenizerAdapter (Docling HybridChunker, strategy
'structure'): build DoclingDocuments inline, call the component's run() directly, assert exact
chunk lists. StructureChunker is a stub — every test here is red until T-worker-020."""

from docling_core.types.doc import (
    BoundingBox,
    DocItemLabel,
    DoclingDocument,
    ProvenanceItem,
    Size,
    TableCell,
    TableData,
)

from rag_worker.components.structure_chunker import StructureChunker, TokenizerAdapter
from rag_worker.models.registry import load_tokenizer


def _cell(row: int, col: int, text: str, *, header: bool = False) -> TableCell:
    return TableCell(
        start_row_offset_idx=row,
        end_row_offset_idx=row + 1,
        start_col_offset_idx=col,
        end_col_offset_idx=col + 1,
        text=text,
        column_header=header,
    )


def _report_doc() -> DoclingDocument:
    doc = DoclingDocument(name="q3-report")
    doc.add_page(page_no=1, size=Size(width=612, height=792))
    doc.add_page(page_no=2, size=Size(width=612, height=792))
    doc.add_title("Q3 Report")
    doc.add_heading("Overview", level=1)
    doc.add_text(
        label=DocItemLabel.TEXT,
        text="Revenue grew by twelve percent compared with the same quarter last year overall.",
    )
    doc.add_text(
        label=DocItemLabel.TEXT,
        text="The main driver was expansion of the enterprise business segment across three regions.",
    )
    doc.add_text(
        label=DocItemLabel.TEXT,
        text="Costs stayed flat in absolute terms while headcount grew modestly through the quarter.",
    )
    doc.add_heading("Details", level=2)
    doc.add_text(
        label=DocItemLabel.TEXT,
        text="Engineering spent the quarter consolidating the internal build pipeline and tooling stack.",
    )
    doc.add_text(
        label=DocItemLabel.TEXT,
        text="Customer support tickets fell by roughly nine percent after the new onboarding flow shipped.",
    )
    doc.add_text(
        label=DocItemLabel.TEXT,
        text="Marketing launched two campaigns targeting mid-market accounts in the second half of the quarter.",
    )
    return doc


def _table_doc() -> DoclingDocument:
    doc = DoclingDocument(name="budget")
    doc.add_page(page_no=1, size=Size(width=612, height=792))
    doc.add_title("Budget")
    doc.add_table(
        data=TableData(
            num_rows=2,
            num_cols=2,
            table_cells=[
                _cell(0, 0, "A", header=True),
                _cell(0, 1, "B", header=True),
                _cell(1, 0, "1"),
                _cell(1, 1, "2"),
            ],
        ),
        prov=ProvenanceItem(
            page_no=1,
            bbox=BoundingBox(l=72, t=100, r=300, b=180),
            charspan=(0, 10),
        ),
    )
    return doc


def test_adapter_counts_tokens_and_max_tokens() -> None:
    adapter = TokenizerAdapter(load_tokenizer("all-minilm"), 128)
    assert adapter.count_tokens("hello world") == 2
    assert adapter.get_max_tokens() == 128


def test_run_returns_documents_with_no_span_and_section_path() -> None:
    chunker = StructureChunker(load_tokenizer("all-minilm"), 64, True)
    docs = chunker.run(docling_json=_report_doc().model_dump_json())["documents"]

    assert len(docs) == 2
    assert all(d.meta["no_span"] is True for d in docs)
    assert docs[0].meta["section_path"] == ["Q3 Report", "Overview"]
    assert docs[1].meta["section_path"] == ["Q3 Report", "Overview", "Details"]


def test_every_chunk_within_token_budget_plus_heading_context() -> None:
    adapter = TokenizerAdapter(load_tokenizer("all-minilm"), 64)
    chunker = StructureChunker(load_tokenizer("all-minilm"), 64, True)
    docs = chunker.run(docling_json=_report_doc().model_dump_json())["documents"]

    assert len(docs) == 2
    for doc in docs:
        heading_context = adapter.count_tokens(" ".join(doc.meta["section_path"]))
        assert adapter.count_tokens(doc.content) <= 64 + heading_context


def test_table_document_has_table_or_mixed_chunk() -> None:
    chunker = StructureChunker(load_tokenizer("all-minilm"), 64, True)
    docs = chunker.run(docling_json=_table_doc().model_dump_json())["documents"]

    assert len(docs) >= 1
    assert any(d.meta["element_type"] in ("table", "mixed") for d in docs)
