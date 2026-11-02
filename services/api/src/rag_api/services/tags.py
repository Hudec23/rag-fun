"""Tag helpers: normalize_tags + parse_tags_csv (F-upload)."""

import re

from rag_api.errors import AppError

TAG_PATTERN = r"^[a-z0-9][a-z0-9_.:-]*$"
MAX_TAG_LEN = 64
MAX_TAGS = 32


def normalize_tags(tags: list[str]) -> list[str]:
    """Deduplicate and sort ascending. Tags are already pattern-validated by the DTO."""
    return sorted(set(tags))


def parse_tags_csv(raw: str | None) -> list[str]:
    """'finance, q3,,Q3 ' -> ['finance', 'q3']: split on ',', strip, lowercase, drop empty, normalize.
    Any tag not matching TAG_PATTERN or longer than 64 chars, or more than 32 tags ->
    AppError('VALIDATION_ERROR', details={'field': 'tags'})."""
    if raw is None:
        return []
    tags = [tag.strip().lower() for tag in raw.split(",")]
    tags = [tag for tag in tags if tag]
    for tag in tags:
        if not re.fullmatch(TAG_PATTERN, tag) or len(tag) > MAX_TAG_LEN:
            raise AppError("VALIDATION_ERROR", details={"field": "tags"})
    if len(tags) > MAX_TAGS:
        raise AppError("VALIDATION_ERROR", details={"field": "tags"})
    return normalize_tags(tags)
