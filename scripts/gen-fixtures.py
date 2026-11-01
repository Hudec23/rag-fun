#!/usr/bin/env python3
"""Planner tool: write tests/contract_fixtures/*.json — one valid instance per contract message
(schema examples + synthetic stage artifacts) — and validate them. Run inside any image with
jsonschema (e.g. the e2e image): python scripts/gen-fixtures.py"""

import json
import math
import random
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[1]
C = ROOT / "contracts"
OUT = ROOT / "tests/contract_fixtures"
OUT.mkdir(exist_ok=True)
schemas = {p: json.loads(p.read_text()) for p in C.rglob("*.schema.json")}
reg = Registry().with_resources([(d["$id"], Resource.from_contents(d, default_specification=DRAFT202012)) for d in schemas.values()])

FILE = "019a4b2c-1f00-7a3e-9c11-2b7f4e5d6a01"
BATCH = "019a4b2c-1e00-7b00-8000-000000000001"
RUN = "019a4b2c-2000-7c00-9000-000000000002"
QRUN = "019a4b2c-2200-7c00-9000-000000000004"
TS = "2026-11-01T18:22:05.123Z"
rnd = random.Random(42)

fixtures: dict[str, tuple[str, object]] = {}
for p, d in schemas.items():
    if d.get("examples"):
        rel = p.relative_to(C).as_posix()
        fixtures[rel.replace("/", "__").replace(".schema.json", ".json")] = (rel, d["examples"][0])

texts = [
    "Q3 Report", "Revenue grew 12 percent year over year, driven by subscriptions.",
    "Operating costs stayed flat while headcount increased slightly.",
    "Regional results", "Europe contributed most of the new subscription revenue.",
    "Outlook", "We expect revenue growth to continue in Q4 thanks to the new pricing.",
    "The board approved a dividend of 0.40 EUR per share.",
]
full = "\n\n".join(texts)
elements, pos, section = [], 0, []
for i, t in enumerate(texts):
    typ = "heading" if t in ("Q3 Report", "Regional results", "Outlook") else "text"
    if typ == "heading":
        section = [t]
    page = 1 if i < 5 else 2
    elements.append({"id": f"e-{i:04d}", "type": typ, "text": t, "page_no": page,
                     "bbox": {"l": 72, "t": 60 + 40 * (i % 5), "r": 540, "b": 90 + 40 * (i % 5)},
                     "heading_level": 2 if typ == "heading" else None,
                     "section_path": [] if typ == "heading" else list(section), "table": None,
                     "from_ocr": False, "char_start": pos, "char_end": pos + len(t)})
    pos += len(t) + 2
parse = {"schema_version": 1, "stage": "parse", "strategy": "docling_layout", "file_id": FILE,
         "mime": "application/pdf", "ocr_used": False,
         "pages": [{"page_no": 1, "width": 612, "height": 792, "image_key": f"{RUN}/parse/v1/page-1.png"},
                   {"page_no": 2, "width": 612, "height": 792, "image_key": f"{RUN}/parse/v1/page-2.png"}],
         "elements": elements, "full_text": full, "docling_json_key": f"{RUN}/parse/v1/docling.json"}
fixtures["artifact_parse.json"] = ("artifacts/parse.schema.json", parse)

chunks = []
bounds = [(0, 2), (1, 3), (3, 5), (5, 8)]  # element ranges; (1,3) overlaps (0,2) → overlap visible
for i, (a, b) in enumerate(bounds):
    s, e = elements[a]["char_start"], elements[b - 1]["char_end"]
    text = full[s:e]
    chunks.append({"index": i, "doc_id": f"{FILE}:{i:05d}", "text": text, "char_start": s, "char_end": e,
                   "element_ids": [el["id"] for el in elements[a:b]],
                   "page_numbers": sorted({el["page_no"] for el in elements[a:b]}),
                   "section_path": elements[b - 1]["section_path"], "element_type": "text",
                   "char_count": len(text), "token_estimate": math.ceil(len(text) / 4)})
counts = [c["char_count"] for c in chunks]
chunk = {"schema_version": 1, "stage": "chunk", "strategy": "recursive",
         "params": {"strategy": "recursive", "length": 300, "overlap": 30, "separators": ["\n\n", "sentence", "\n", " "]},
         "parse_strategy": "docling_layout", "source_text": full, "chunks": chunks,
         "stats": {"count": 4, "min_chars": min(counts), "max_chars": max(counts),
                   "mean_chars": round(sum(counts) / 4, 2),
                   "histogram": {"bin_edges": [float(min(counts)), float(max(counts))], "counts": [4]}},
         "semantic": None}
fixtures["artifact_chunk.json"] = ("artifacts/chunk.schema.json", chunk)

def vec(n):
    v = [rnd.gauss(0, 1) for _ in range(n)]
    norm = math.sqrt(sum(x * x for x in v))
    return [round(x / norm, 6) for x in v]
vs = [vec(384) for _ in chunks]
sim = [[round(1.0 if i == j else sum(a * b for a, b in zip(vs[i], vs[j])), 6) for j in range(4)] for i in range(4)]
embed = {"schema_version": 1, "stage": "embed", "dense_model": "all-minilm", "dense_dims": 384, "max_tokens": 256,
         "sparse_model": "Qdrant/bm25", "tokenizer": "sentence-transformers/all-MiniLM-L6-v2",
         "chunks": [{"index": c["index"], "doc_id": c["doc_id"], "dense": vs[i],
                     "sparse": {"indices": [3, 17, 99], "values": [1.0, 0.5, 0.25]},
                     "tokens": ["[CLS]"] + c["text"].lower().split()[:20] + ["[SEP]"],
                     "token_count": 300 if i == 3 else 22, "over_limit": i == 3} for i, c in enumerate(chunks)],
         "sample_indices": [0, 1, 2, 3],
         "projections": {"pca2": [[round(rnd.uniform(-1, 1), 6) for _ in range(2)] for _ in range(4)],
                         "pca3": [[round(rnd.uniform(-1, 1), 6) for _ in range(3)] for _ in range(4)],
                         "pca_explained_variance": [0.5, 0.3, 0.2], "umap2": None, "umap3": None},
         "similarity": sim}
fixtures["artifact_embed.json"] = ("artifacts/embed.schema.json", embed)

meta = lambda c: {"file_id": FILE, "batch_id": BATCH, "batch_name": "Q3 reports", "filename": "q3-report.pdf",
                  "mime": "application/pdf", "tags": ["finance", "q3"], "page": c["page_numbers"][0],
                  "page_numbers": c["page_numbers"], "section_path": c["section_path"], "element_type": "text",
                  "chunk_index": c["index"], "chunk_strategy": "recursive", "parse_strategy": "docling_layout",
                  "ingest_run_id": RUN, "dense_model": "all-minilm", "sparse_model": "Qdrant/bm25", "stored_at": TS}
pid = lambda i: f"{i:032x}"
payload0 = {"id": chunks[0]["doc_id"], "content": chunks[0]["text"], "blob": None, "score": None, "meta": meta(chunks[0])}
store = {"schema_version": 1, "stage": "store", "qdrant_collection": "rf_019a4b2c1d007b0080000000000000aa",
         "points_deleted": 0, "points_written": 4, "point_ids": [pid(i + 1) for i in range(4)], "payload_sample": payload0,
         "vector_config": {"dense_name": "text-dense", "dense_size": 384, "distance": "Cosine",
                           "sparse_name": "text-sparse", "sparse_modifier": "idf"}}
fixtures["artifact_store.json"] = ("artifacts/store.schema.json", store)

transform = {"schema_version": 1, "stage": "transform", "strategy": "multi_query", "question": "How did revenue change?",
             "queries": ["How did revenue change?", "revenue growth Q3", "subscription revenue trend"],
             "hyde_document": None,
             "messages": [{"role": "system", "content": "You write 2 different search queries ..."},
                          {"role": "user", "content": "How did revenue change?"}],
             "model": {"provider": "ollama", "model": "qwen3:8b"}}
fixtures["artifact_transform.json"] = ("artifacts/transform.schema.json", transform)

hit = lambda i, rank, score: {"point_id": pid(i + 1), "doc_id": chunks[i]["doc_id"], "rank": rank, "score": score,
                              "content": chunks[i]["text"], "meta": meta(chunks[i])}
dense = [hit(1, 1, 0.81), hit(3, 2, 0.62), hit(0, 3, 0.4)]
sparse = [hit(3, 1, 7.2), hit(1, 2, 5.1), hit(2, 3, 1.3)]
def rrf(i, ranks):
    return round(sum(1 / (60 + r) for r in ranks), 6)
fused = [
    {"hit": hit(1, 1, rrf(1, [1, 2])), "source_ranks": [{"query_index": 0, "list": "dense", "rank": 1}, {"query_index": 0, "list": "sparse", "rank": 2}]},
    {"hit": hit(3, 2, rrf(3, [2, 1])), "source_ranks": [{"query_index": 0, "list": "dense", "rank": 2}, {"query_index": 0, "list": "sparse", "rank": 1}]},
    {"hit": hit(0, 3, rrf(0, [3])), "source_ranks": [{"query_index": 0, "list": "dense", "rank": 3}]},
    {"hit": hit(2, 4, rrf(2, [3])), "source_ranks": [{"query_index": 0, "list": "sparse", "rank": 3}]},
]
retrieve = {"schema_version": 1, "stage": "retrieve", "mode": "hybrid", "top_k": 10, "rrf_k": 60,
            "filters": {"must": [{"key": "tags", "match": {"any": ["finance"]}}]},
            "per_query": [{"query": "How did revenue change?", "dense": dense, "sparse": sparse}], "fused": fused}
fixtures["artifact_retrieve.json"] = ("artifacts/retrieve.schema.json", retrieve)

before = [f["hit"] for f in fused]
after = [{"hit": hit(3, 1, 0.97), "previous_rank": 2, "rerank_score": 0.97},
         {"hit": hit(1, 2, 0.88), "previous_rank": 1, "rerank_score": 0.88},
         {"hit": hit(2, 3, 0.12), "previous_rank": 4, "rerank_score": 0.12}]
rerank = {"schema_version": 1, "stage": "rerank", "enabled": True, "model": "Xenova/ms-marco-MiniLM-L-6-v2",
          "top_n": 3, "query": "How did revenue change?", "before": before, "after": after}
fixtures["artifact_rerank.json"] = ("artifacts/rerank.schema.json", rerank)

ctx = [{"n": 1, "hit": after[0]["hit"], "tokens": 40}, {"n": 2, "hit": after[1]["hit"], "tokens": 35}]
generate = {"schema_version": 1, "stage": "generate", "model": {"provider": "ollama", "model": "qwen3:8b"},
            "messages": [{"role": "system", "content": "Answer the question using only the numbered context passages. ..."},
                         {"role": "user", "content": "Context:\n[1] ...\n\nQuestion: How did revenue change?"}],
            "budget": {"max_context_tokens": 4000, "system_tokens": 60, "question_tokens": 8,
                       "used_context_tokens": 75, "chunks_included": 2, "chunks_dropped": 1},
            "context": ctx, "answer": "Revenue grew 12 percent [2] and growth should continue in Q4 [1, 2].",
            "citations": [1, 2], "usage": {"prompt_tokens": 210, "completion_tokens": 18}}
fixtures["artifact_generate.json"] = ("artifacts/generate.schema.json", generate)

errors = 0
for name, (schema_rel, inst) in sorted(fixtures.items()):
    v = Draft202012Validator({"$ref": schemas[C / schema_rel]["$id"]}, registry=reg)
    errs = list(v.iter_errors(inst))
    for e in errs[:3]:
        print("INVALID", name, "/".join(map(str, e.path)), e.message[:200])
    errors += len(errs)
    (OUT / name).write_text(json.dumps(inst, indent=2, ensure_ascii=False) + "\n")
print(f"{len(fixtures)} fixtures, {errors} errors")
raise SystemExit(1 if errors else 0)
