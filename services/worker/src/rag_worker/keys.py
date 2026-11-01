"""S3 key layout of bucket 'artifacts' (SYSTEM.md §4)."""


def artifact_key(run_id: str, stage: str, version: int) -> str:
    return f"{run_id}/{stage}/v{version}.json"


def page_image_key(run_id: str, version: int, page_no: int) -> str:
    return f"{run_id}/parse/v{version}/page-{page_no}.png"


def docling_json_key(run_id: str, version: int) -> str:
    return f"{run_id}/parse/v{version}/docling.json"


def doc_id(file_id: str, chunk_index: int) -> str:
    return f"{file_id}:{chunk_index:05d}"
