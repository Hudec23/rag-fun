"""parse strategy 'plain_text': no layout model. Supported mimes: application/pdf (pypdf, one 'text'
element per non-empty page, page_no set, no bbox), text/plain + text/markdown (one 'text' element per
blank-line separated block; markdown lines starting with '#' become 'heading' with heading_level =
number of '#'), text/html (tags stripped with html.parser, one 'text' element per block-level
element's text), text/csv (one 'table' element; first row = header). Others ->
WorkerError('UNSUPPORTED_FOR_STRATEGY', details={'mime': mime})."""

from typing import Any

from haystack import component


def convert_plain(data: bytes, mime: str) -> dict[str, Any]:
    """-> {'elements': [Element dict without char spans], 'pages': [{'page_no', 'width', 'height'}]}.
    pages: PDF -> one per page with mediabox width/height; others -> []. Text decoded UTF-8 with
    errors='replace'. Element ids e-0000.. in order; section_path built from preceding headings;
    from_ocr False; bbox None; table None except csv."""
    raise NotImplementedError("not implemented")


@component
class PlainTextConverter:
    @component.output_types(elements=list[dict[str, Any]], pages=list[dict[str, Any]])
    def run(self, data: bytes, mime: str) -> dict[str, Any]:
        return convert_plain(data, mime)
