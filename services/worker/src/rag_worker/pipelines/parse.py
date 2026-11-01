from typing import Any

from haystack import Pipeline


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
    raise NotImplementedError("not implemented")


def run_parse(
    pipeline: Pipeline, strategy: str, data: bytes, mime: str, filename: str
) -> dict[str, Any]:
    """Run the pipeline (docling: sources=[ByteStream(data, meta={'file_name': filename}, mime_type=
    mime)]) -> {'elements', 'pages', 'page_images' ({} for plain_text), 'ocr_used', 'docling_json'
    (None for plain_text)}. Docling conversion error -> WorkerError('PARSE_FAILED',
    details={'reason': str(e)[:300]})."""
    raise NotImplementedError("not implemented")
