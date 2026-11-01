"""Validate JSON against a contract schema (with $ref resolution across contracts/)."""

import json
from functools import cache
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from tests.conftest import CONTRACTS


@cache
def _registry() -> Registry:
    pairs = []
    for p in CONTRACTS.rglob("*.schema.json"):
        doc = json.loads(p.read_text())
        pairs.append((doc["$id"], Resource.from_contents(doc, default_specification=DRAFT202012)))
    return Registry().with_resources(pairs)


def errors(instance: Any, schema_path: str) -> list[str]:
    """schema_path relative to contracts/, optionally with '#/$defs/X'. [] = valid."""
    path, _, frag = schema_path.partition("#")
    doc = json.loads((CONTRACTS / path).read_text())
    ref = doc["$id"] + (("#" + frag) if frag else "")
    v = Draft202012Validator({"$ref": ref}, registry=_registry())
    return [f"{'/'.join(map(str, e.path))}: {e.message}" for e in v.iter_errors(instance)]
