"""Minimal YAML subset reader for task frontmatter and .autospec/plan/services/*.yaml (stdlib only).

autospec-run.py runs on the host without PyYAML, so it reads plan files with this.
autospec-check.py parses the same files with PyYAML too and fails if the two disagree, so a plan
that passes the checker is read identically by the runner.

Supported: `key: scalar`, `key: [a, b]`, `key:` followed by `- item` lines, `key:` followed by one
level of indented `sub: scalar` lines, full-line and trailing ` #` comments, '...' and "..." strings.
Anything else (block scalars, multi-line values, deeper nesting) raises ValueError.
"""

from __future__ import annotations

import json
import re

_KV = re.compile(r"^([A-Za-z_][\w-]*):(\s.*)?$")


def _strip_comment(s: str) -> str:
    quote = None
    i = 0
    while i < len(s):
        c = s[i]
        if quote:
            if (c == "\\" and quote == '"') or (c == "'" == quote and s[i + 1:i + 2] == "'"):
                i += 1  # skip the escaped character
            elif c == quote:
                quote = None
        elif c in "'\"" and (i == 0 or s[i - 1] in " [,"):
            quote = c
        elif c == "#" and (i == 0 or s[i - 1] in " \t"):
            return s[:i].rstrip()
        i += 1
    return s.rstrip()


def _split_flow(inner: str) -> list[str]:
    items, quote, start = [], None, 0
    for i, c in enumerate(inner):
        if quote:
            if c == quote:
                quote = None
        elif c in "'\"":
            quote = c
        elif c == ",":
            items.append(inner[start:i])
            start = i + 1
    items.append(inner[start:])
    return [x.strip() for x in items]


def _scalar(v: str):
    v = v.strip()
    if v.startswith("'"):
        if len(v) < 2 or not v.endswith("'"):
            raise ValueError(f"unterminated string: {v}")
        return v[1:-1].replace("''", "'")
    if v.startswith('"'):
        return json.loads(v)
    if v.startswith("["):
        if not v.endswith("]"):
            raise ValueError(f"flow list must fit on one line: {v}")
        inner = v[1:-1].strip()
        items = [_scalar(x) for x in _split_flow(inner)] if inner else []
        if any(isinstance(x, list) for x in items):
            raise ValueError(f"nested lists are not supported: {v}")
        return items
    if v in ("", "~", "null"):
        return None
    if v in ("true", "false"):
        return v == "true"
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def _kv(s: str) -> tuple[str, str]:
    m = _KV.match(s)
    if not m:
        raise ValueError(f"expected `key: value`, got: {s}")
    return m.group(1), (m.group(2) or "").strip()


def load(text: str) -> dict:
    lines = []
    for raw in text.splitlines():
        s = _strip_comment(raw)
        if s.strip():
            lines.append((len(s) - len(s.lstrip(" ")), s.strip()))
    out: dict = {}
    i = 0
    while i < len(lines):
        indent, s = lines[i]
        if indent:
            raise ValueError(f"unexpected indentation: {s}")
        key, rest = _kv(s)
        i += 1
        if rest:
            out[key] = _scalar(rest)
        elif i < len(lines) and lines[i][1].startswith("- "):
            items = []
            while i < len(lines) and lines[i][1].startswith("- "):
                items.append(_scalar(lines[i][1][2:]))
                i += 1
            out[key] = items
        elif i < len(lines) and lines[i][0] > 0:
            sub = {}
            while i < len(lines) and lines[i][0] > 0:
                k, r = _kv(lines[i][1])
                if not r:
                    raise ValueError(f"nesting deeper than one level: {key}.{k}")
                sub[k] = _scalar(r)
                i += 1
            out[key] = sub
        else:
            out[key] = None
    return out


def frontmatter(text: str) -> dict:
    """The YAML between the leading `---` lines of a task file."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError("no frontmatter between --- lines")
    return load(m.group(1))
