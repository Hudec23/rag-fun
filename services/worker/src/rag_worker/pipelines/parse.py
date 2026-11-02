"""Parse pipelines (strategies docling_layout / docling_ocr / plain_text): build_parse_pipeline
assembles the Haystack pipeline for a strategy, run_parse feeds it the file bytes and normalizes
the result to {'elements', 'pages', 'page_images', 'ocr_used', 'docling_json'}."""

import json
import os
from dataclasses import replace
from pathlib import Path
from typing import Any

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions
from docling.document_converter import DocumentConverter, ImageFormatOption, PdfFormatOption
from haystack import Document, Pipeline, component
from haystack.core.errors import PipelineRuntimeError
from haystack.dataclasses import ByteStream
from haystack_integrations.components.converters.docling import DoclingConverter, ExportType

from rag_worker.components.docling_extractor import DoclingExtractor
from rag_worker.components.plain_text_converter import PlainTextConverter
from rag_worker.errors import WorkerError

_DOCLING_STRATEGIES = ("docling_layout", "docling_ocr")


def _docling_converter(params: dict[str, Any], full_page_ocr: bool) -> DocumentConverter:
    """PdfPipelineOptions (table structure, page images, easyocr) for PDF + image formats, default
    options for office/html/md/csv."""
    pipeline_options = PdfPipelineOptions(
        artifacts_path=os.environ["DOCLING_ARTIFACTS_PATH"],
        do_table_structure=params["extract_tables"],
        generate_page_images=params["page_images"],
        images_scale=1.5,
        do_ocr=True,
        ocr_options=EasyOcrOptions(
            lang=["en"],
            force_full_page_ocr=full_page_ocr,  # type: ignore[call-arg]
        ),
    )
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
            InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipeline_options),
        }
    )


def _scan_origin_mimetype(content: str, mime: str) -> str:
    """origin.mimetype of the exported DoclingDocument JSON as the source mime (docling's PDF
    pipeline hardcodes 'application/pdf' even for raster inputs)."""
    data = json.loads(content)
    if not isinstance(data.get("origin"), dict):
        data["origin"] = {"mimetype": mime, "filename": "", "binary_hash": 0}
    data["origin"]["mimetype"] = mime
    return json.dumps(data)


class _ScanMimeDoclingConverter(DoclingConverter):
    """DoclingConverter that restores the source mime in origin.mimetype of the exported JSON for
    raster inputs, so DoclingExtractor marks scanned documents as ocr_used.

    Plain subclass (no @component: it would re-create the class and break super())."""

    @component.output_types(documents=list[Document])
    def run(
        self,
        paths: list[str | Path] | None = None,
        sources: list[str | Path | ByteStream] | None = None,
        meta: dict[str, Any] | list[dict[str, Any]] | None = None,
    ) -> dict[str, list[Document]]:
        out = super().run(paths=paths, sources=sources, meta=meta)
        inputs = list(sources) if sources is not None else list(paths or [])
        documents = out["documents"]
        for index, (source, doc) in enumerate(zip(inputs, documents, strict=True)):
            mime = source.mime_type if isinstance(source, ByteStream) else None
            if mime is None or not mime.startswith("image/") or not doc.content:
                continue
            documents[index] = replace(doc, content=_scan_origin_mimetype(doc.content, mime))
        return out


def build_parse_pipeline(strategy: str, params: dict[str, Any]) -> Pipeline:
    """docling_layout / docling_ocr: 'converter' = docling-haystack DoclingConverter(converter=
    DocumentConverter with PdfPipelineOptions(artifacts_path=$DOCLING_ARTIFACTS_PATH,
    do_table_structure=params.extract_tables, generate_page_images=params.page_images,
    images_scale=1.5, do_ocr=True, ocr_options=EasyOcrOptions(lang=['en'],
    force_full_page_ocr=(strategy == 'docling_ocr'))) for PDF and image formats, default options for
    office/html/md/csv), export_type=ExportType.JSON) -> 'extractor' = DoclingExtractor
    (import: from haystack_integrations.components.converters.docling import DoclingConverter, ExportType)
    (converter.documents -> extractor.documents).
    plain_text: single component 'converter' = PlainTextConverter."""
    pipeline = Pipeline()
    if strategy in _DOCLING_STRATEGIES:
        converter = _ScanMimeDoclingConverter(
            converter=_docling_converter(params, full_page_ocr=(strategy == "docling_ocr")),
            export_type=ExportType.JSON,
        )
        pipeline.add_component("converter", converter)
        pipeline.add_component("extractor", DoclingExtractor())
        pipeline.connect("converter.documents", "extractor.documents")
    elif strategy == "plain_text":
        pipeline.add_component("converter", PlainTextConverter())
    else:
        raise WorkerError("UNSUPPORTED_FOR_STRATEGY", details={"strategy": strategy})
    return pipeline


def run_parse(
    pipeline: Pipeline, strategy: str, data: bytes, mime: str, filename: str
) -> dict[str, Any]:
    """Run the pipeline (docling: sources=[ByteStream(data, meta={'file_name': filename}, mime_type=
    mime)]) -> {'elements', 'pages', 'page_images' ({} for plain_text), 'ocr_used', 'docling_json'
    (None for plain_text)}. Docling conversion error -> WorkerError('PARSE_FAILED',
    details={'reason': str(e)[:300]})."""
    if strategy == "plain_text":
        out = pipeline.run({"data": data, "mime": mime})["converter"]
        return {
            "elements": out["elements"],
            "pages": out["pages"],
            "page_images": {},
            "ocr_used": False,
            "docling_json": None,
        }
    try:
        result = pipeline.run(
            {"sources": [ByteStream(data, meta={"file_name": filename}, mime_type=mime)]}
        )
    except PipelineRuntimeError as e:
        raise WorkerError("PARSE_FAILED", details={"reason": str(e)[:300]}) from e
    return result["extractor"]
