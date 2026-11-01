"""Example unit test file (house style for worker tests): build inputs inline, call the component's
run() directly, assert exact dicts."""

from haystack import Document

from rag_worker.components.chunk_annotator import ChunkAnnotator, element_type_of

FILE_ID = "019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01"
SOURCE = "Intro\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\nScanned words"
ELEMENTS = [
    {
        "id": "e-0000",
        "type": "heading",
        "page_no": 1,
        "section_path": [],
        "from_ocr": False,
        "char_start": 0,
        "char_end": 5,
    },
    {
        "id": "e-0001",
        "type": "table",
        "page_no": 1,
        "section_path": ["Intro"],
        "from_ocr": False,
        "char_start": 7,
        "char_end": 36,
    },
    {
        "id": "e-0002",
        "type": "text",
        "page_no": 2,
        "section_path": ["Intro"],
        "from_ocr": True,
        "char_start": 38,
        "char_end": 51,
    },
]


def _run(docs: list[Document]) -> list[dict]:  # type: ignore[type-arg]
    return ChunkAnnotator().run(
        documents=docs, elements=ELEMENTS, source_text=SOURCE, file_id=FILE_ID
    )["chunks"]


def test_span_from_split_idx_start_and_overlaps() -> None:
    [c] = _run([Document(content=SOURCE[0:20], meta={"split_idx_start": 0})])
    assert c["char_start"] == 0 and c["char_end"] == 20
    assert c["element_ids"] == ["e-0000", "e-0001"]
    assert c["page_numbers"] == [1]
    assert c["element_type"] == "mixed"
    assert c["doc_id"] == f"{FILE_ID}:00000"
    assert c["token_estimate"] == 5


def test_span_found_by_search_when_no_hint() -> None:
    [c] = _run([Document(content="Scanned words")])
    assert (c["char_start"], c["char_end"]) == (38, 51)
    assert c["element_type"] == "image_ocr"
    assert c["section_path"] == ["Intro"]


def test_preset_meta_wins_and_no_span() -> None:
    [c] = _run(
        [
            Document(
                content="a: 1\nb: 2",
                meta={
                    "no_span": True,
                    "element_type": "table",
                    "element_ids": ["e-0001"],
                    "page_numbers": [1],
                },
            )
        ]
    )
    assert c["char_start"] is None and c["char_end"] is None
    assert c["element_ids"] == ["e-0001"]
    assert c["element_type"] == "table"


def test_blank_documents_skipped_and_indices_contiguous() -> None:
    chunks = _run([Document(content="Intro"), Document(content="  "), Document(content="Scanned")])
    assert [c["index"] for c in chunks] == [0, 1]
    assert chunks[1]["doc_id"].endswith(":00001")


def test_element_type_rules() -> None:
    assert element_type_of([]) == "text"
    assert element_type_of([ELEMENTS[1]]) == "table"
    assert element_type_of([ELEMENTS[0]]) == "text"
