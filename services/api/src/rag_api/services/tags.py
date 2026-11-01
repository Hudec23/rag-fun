TAG_PATTERN = r"^[a-z0-9][a-z0-9_.:-]*$"


def normalize_tags(tags: list[str]) -> list[str]:
    """Deduplicate and sort ascending. Tags are already pattern-validated by the DTO."""
    raise NotImplementedError("not implemented")


def parse_tags_csv(raw: str | None) -> list[str]:
    """'finance, q3,,Q3 ' -> ['finance', 'q3']: split on ',', strip, lowercase, drop empty, normalize.
    Any tag not matching TAG_PATTERN or longer than 64 chars, or more than 32 tags ->
    AppError('VALIDATION_ERROR', details={'field': 'tags'})."""
    raise NotImplementedError("not implemented")
