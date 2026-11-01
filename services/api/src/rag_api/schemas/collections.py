from typing import Annotated

from pydantic import Field

from rag_api.contracts_gen.shared.common_schema import DenseModel, SparseModel
from rag_api.schemas.base import Id, Model, Timestamp

CollectionName = Annotated[
    str, Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9_-]*$")
]


class CollectionOut(Model):
    id: Id
    name: str
    qdrant_name: str
    dense_model: str
    dense_dims: int
    sparse_model: str
    created_at: Timestamp


class CollectionCreate(Model):
    name: CollectionName
    dense_model: DenseModel
    sparse_model: SparseModel


class CollectionList(Model):
    items: list[CollectionOut]
