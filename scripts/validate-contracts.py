#!/usr/bin/env python3
"""Validate every contract: JSON Schema meta-validation, OpenAPI 3.1 validation, and every example
against its schema. Run from the repo root (needs only Docker):
  docker run --rm -v "$PWD":/w -w /w python:3.12.16-slim sh -c \
    'pip install -q --root-user-action=ignore --disable-pip-version-check jsonschema==4.26.0 \
     openapi-spec-validator==0.9.0 pyyaml==6.0.3 && python scripts/validate-contracts.py'
"""
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import validate as validate_openapi
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path("contracts").resolve()
errors: list[str] = []
checked = 0


def resource(doc):
    return Resource.from_contents(doc, default_specification=DRAFT202012)


schemas = {p: json.loads(p.read_text()) for p in sorted(ROOT.rglob("*.schema.json"))}
openapis = {p: yaml.safe_load(p.read_text()) for p in sorted(ROOT.rglob("*.yaml"))}
pairs = []
for p, doc in schemas.items():
    pairs.append((p.as_uri(), resource(doc)))
    if "$id" in doc:
        pairs.append((doc["$id"], resource(doc)))
for p, doc in openapis.items():
    pairs.append((p.as_uri(), resource(doc)))
registry = Registry().with_resources(pairs)


def absolutize(node, doc_uri):
    """Make '#/...' refs absolute so the wrapper can point into an OpenAPI document."""
    if isinstance(node, dict):
        return {k: (doc_uri + v if k == "$ref" and isinstance(v, str) and v.startswith("#") else absolutize(v, doc_uri))
                for k, v in node.items()}
    if isinstance(node, list):
        return [absolutize(v, doc_uri) for v in node]
    return node


def check(instance, schema, doc_uri, where):
    global checked
    checked += 1
    wrapper_id = doc_uri.rsplit("/", 1)[0] + "/__wrapper__.json"
    wrapped = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": wrapper_id,
               "allOf": [absolutize(schema, doc_uri)]}
    v = Draft202012Validator(wrapped, registry=registry, format_checker=FormatChecker())
    for e in sorted(v.iter_errors(instance), key=lambda e: list(e.path)):
        errors.append(f"{where}: {'/'.join(map(str, e.path)) or '<root>'}: {e.message[:300]}")


# 1. JSON schemas: meta-valid, refs resolve, examples valid
for p, doc in schemas.items():
    rel = p.relative_to(ROOT.parent)
    try:
        Draft202012Validator.check_schema(doc)
    except Exception as e:  # noqa: BLE001
        errors.append(f"{rel}: invalid schema: {e}")
        continue
    if '"additionalProperties": true' in p.read_text():
        errors.append(f"{rel}: additionalProperties true is forbidden")
    base = doc.get("$id", p.as_uri())
    for i, ex in enumerate(doc.get("examples", [])):
        check(ex, {"$ref": base}, base, f"{rel} examples[{i}]")
    for name, sub in doc.get("$defs", {}).items():
        for i, ex in enumerate(sub.get("examples", [])):
            check(ex, {"$ref": f"{base}#/$defs/{name}"}, base, f"{rel} $defs/{name} examples[{i}]")

# 2. OpenAPI: spec-valid, every media example valid against its schema
def media_examples(node, path):
    if isinstance(node, dict):
        if "schema" in node and ("example" in node or "examples" in node):
            if "example" in node:
                yield path, node["schema"], node["example"]
            for k, ex in (node.get("examples") or {}).items():
                if isinstance(ex, dict) and "value" in ex:
                    yield f"{path}/examples/{k}", node["schema"], ex["value"]
        for k, v in node.items():
            yield from media_examples(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from media_examples(v, f"{path}/{i}")


for p, doc in openapis.items():
    rel = p.relative_to(ROOT.parent)
    try:
        validate_openapi(doc, base_uri=p.as_uri())
    except Exception as e:  # noqa: BLE001
        errors.append(f"{rel}: invalid OpenAPI: {str(e)[:500]}")
    for where, schema, ex in media_examples(doc.get("paths", {}), "paths"):
        if "multipart" in where:
            continue
        check(ex, schema, p.as_uri(), f"{rel} {where}")
    for where, schema, ex in media_examples(doc.get("components", {}), "components"):
        check(ex, schema, p.as_uri(), f"{rel} {where}")
    for name, sch in (doc.get("components", {}).get("schemas") or {}).items():
        if "example" in sch:
            check(sch["example"], {"$ref": f"#/components/schemas/{name}"}, p.as_uri(), f"{rel} schemas/{name} example")

# 3. errors.json ⇔ ErrorCode enum
codes = set(json.loads((ROOT / "shared/errors.json").read_text())["codes"])
enum = set(schemas[ROOT / "shared/common.schema.json"]["$defs"]["ErrorCode"]["enum"])
if codes != enum:
    errors.append(f"errors.json vs ErrorCode enum differ: {sorted(codes ^ enum)}")

for e in errors:
    print("ERROR", e)
print(f"CONTRACT CHECK: {len(schemas)} schemas, {len(openapis)} openapi, {checked} examples, {len(errors)} errors")
sys.exit(1 if errors else 0)
