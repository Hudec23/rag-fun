from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Id = Annotated[
    str, Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
]
PointId = Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
Tag = Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9_.:-]*$")]
Tags = Annotated[list[Tag], Field(max_length=32)]
Timestamp = str  # always produced with rag_api.ids.to_iso


class Model(BaseModel):
    """Base for every api DTO: unknown fields are rejected (422 VALIDATION_ERROR)."""

    model_config = ConfigDict(extra="forbid")


class PageInfo(Model):
    total: int
    limit: int
    offset: int
