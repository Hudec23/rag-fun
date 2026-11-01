# rag-fun — System spec

## 1. Purpose
rag-fun is a local, single-user **visual learning lab for Retrieval-Augmented Generation**. A learner
uploads files (PDF, Office, text, images) and walks them through every RAG stage, one stage at a time:
upload to local S3 → parse (several strategies) → chunk (several strategies) → embed (inspected
*before* storing) → store in Qdrant (with filterable payload tags) → query transform → retrieve
(dense / sparse / hybrid + filters) → rerank → generate (with citations). Every stage is a separate,
re-runnable step with its own parameters and its own visualization, and the real Haystack pipeline
graph behind each stage is shown. Everything starts with **one command** (`./start.sh` on macOS, `start.cmd` on Windows) that brings up
all containers and opens the UI in the browser, using native Ollama on the host; a Settings page lets the user swap the local chat model for Anthropic or any
OpenAI-compatible endpoint.

## 1a. Requirements
| ID | Requirement | Kind | Covered by |
|---|---|---|---|
| R-001 | User can upload multiple files in one batch (drag & drop); each file is stored in local S3 and listed with name, type, size, batch | functional | features |
| R-002 | Supported types: PDF (text and scanned), DOCX, PPTX, XLSX, MD, TXT, HTML, CSV, PNG, JPG, TIFF; others rejected with `UNSUPPORTED_FILE_TYPE` | functional | features |
| R-003 | User can attach free-form tags to a file and to a whole batch; tags become Qdrant payload | functional | features |
| R-004 | Parse stage with 3 strategies: `docling_layout`, `docling_ocr` (forced full-page OCR), `plain_text` | functional | features |
| R-005 | Parse visualization: page images with colored bounding boxes per element type (text, heading, table, picture, list), element list, tables rendered as tables, OCR text shown next to image | functional | features |
| R-006 | Chunk stage with 6 strategies: `fixed`, `sentence`, `recursive`, `semantic`, `structure`, `table` — each with its own parameters | functional | features |
| R-007 | Chunk visualization: source text with chunk boundaries color-highlighted (overlaps visible), chunk cards with metadata, chunk length histogram, chunk count | functional | features |
| R-008 | Embed stage computes dense (Ollama) and sparse (BM25 or SPLADE) vectors but does NOT store them | functional | features |
| R-009 | Embed visualization: per-chunk token view with token count vs model limit, vector heatmap, 2D and 3D scatter (PCA and UMAP), cosine similarity matrix | functional | features |
| R-010 | Store stage upserts embedded chunks into a Qdrant collection with named dense + sparse vectors and the payload in contracts/qdrant/payload.schema.json; re-storing a file replaces its points | functional | features |
| R-011 | Qdrant browser: collection info (vector config, point count, payload indexes), paginated point list with payload, filter builder over payload tags, raw JSON of a point | functional | features |
| R-012 | User manages Collections (name, dense model, sparse model) — embedding model fixed per collection | functional | features |
| R-013 | Step-by-step flow: each stage runs on demand, can be re-run with new params (new version); re-running a stage marks downstream stages `stale`. "Run all" runs remaining stages with current params | functional | features |
| R-014 | Live progress of every running stage is pushed to the browser (SSE) | functional | features |
| R-015 | Query transform stage: `none`, `rewrite`, `multi_query`, `hyde`; shows generated queries/text | functional | features |
| R-016 | Retrieve stage: `dense`, `sparse`, `hybrid` (RRF); with metadata filters; hybrid view shows the dense list, sparse list and fused list side by side with scores and ranks | functional | features |
| R-017 | Rerank stage: cross-encoder reorders top-K; shows before/after rank and score | functional | features |
| R-018 | Generate stage: shows the assembled prompt, context token budget bar, streamed answer, and citations `[n]` that link back to chunks | functional | features |
| R-019 | Pipeline graph view: renders the actual Haystack pipeline (components + connections) used for each stage | functional | features |
| R-020 | Settings page: chat provider `ollama` / `anthropic` / `openai_compatible` with model, base URL, API key; Ollama base URL; reranker on/off; "test connection" button | functional | features |
| R-021 | Default install is fully local: no API key needed; works on macOS (Apple Silicon) and Windows (Docker Desktop) | non-functional | skeleton |
| R-022 | Every error response uses the shared error shape | cross-cutting | skeleton |
| R-023 | All services log JSON lines with the shared fields | cross-cutting | skeleton |
| R-024 | Every service exposes or reports health; web shows a status bar of api, worker, postgres, redis, qdrant, s3, ollama | cross-cutting | features |
| R-025 | One command starts everything preconfigured and opens the UI: `./start.sh` (macOS/Linux) or `start.cmd` (Windows) checks Docker and Ollama, pulls missing default models, runs `docker compose up -d --build --wait`, waits for `/api/v1/health`, opens `http://localhost:8080`. `./stop.sh` / `stop.cmd` stops it. No manual config: defaults in `.env.defaults`, DB migrations, S3 buckets, the default collection and settings row are created automatically on api startup | non-functional | features |

## 2. Services
| Service | Language / version | Framework / version | Owns | Responsibility | Must NOT |
|---|---|---|---|---|---|
| web | TypeScript 5.9.3, Node 24.19.0 | React 19.3.1, Vite 8.3.5; served by `nginx:1.30.6-alpine` in the app stack | – | Browser UI: all pages and visualizations | call worker, Qdrant, S3 or Ollama directly; hold API keys after saving |
| api | Python 3.12.16 | FastAPI 0.162.0 | Postgres DB `ragfun`; S3 bucket `uploads` | Public REST + SSE for web; file upload; run/stage bookkeeping; settings; enqueues worker jobs; read-only Qdrant browser | import Haystack; compute embeddings; write to Qdrant; write to bucket `artifacts` |
| worker | Python 3.12.16 | Haystack 3.4.1 + arq 0.28.0 | Qdrant (all writes); S3 bucket `artifacts` | Runs every Haystack pipeline (parse, chunk, embed, store, query transform, retrieve, rerank, generate); publishes progress; reports results to api | expose HTTP; touch Postgres; write to bucket `uploads`; read settings from anywhere except the job payload |

The worker image runs as **two containers**: `worker-ingest` (queue `ingest`: parse, chunk, embed,
store) and `worker-query` (queue `query`: transform, retrieve, rerank, generate, qdrant-free
utility jobs), so a long OCR job never blocks a query.

Infrastructure (pinned images, no code of ours):
| Name | Image | Ports (host) |
|---|---|---|
| postgres | `postgres:17.11` | 5432 |
| redis | `redis:8.6.8` | 6379 |
| qdrant | `qdrant/qdrant:v1.19.2` | 6333 (REST + dashboard), 6334 (gRPC) |
| s3 | `rustfs/rustfs:1.0.3` (S3-compatible) | 9000 (S3 API), 9001 (console) |
| ollama | **native on host**, not in compose | 11434, reached as `http://host.docker.internal:11434` |

App stack host ports (`docker-compose.yml`): web **8080** (nginx: static build + proxy `/api` → `api:8000`,
SSE buffering off), api 8000, qdrant 6333, s3 console 9001. All bound to `127.0.0.1`.

## 3. Communication
| From → To | Style | Contract file | Notes |
|---|---|---|---|
| web → api | REST JSON, `/api/v1/*` | contracts/openapi/api.yaml | same origin: nginx (app) or Vite dev proxy (dev) forwards `/api` → `http://api:8000` |
| web ← api | SSE `GET /api/v1/events?run_id=…` | contracts/events/*.schema.json | event name = `type` field |
| api → worker | arq job on Redis | contracts/jobs/*.schema.json | job function name = schema file stem; payload is ONE dict argument `payload`; payload carries resolved model config incl. API key |
| worker → api | REST callbacks `POST /internal/v1/stage-started`, `POST /internal/v1/stage-results`, `PUT /internal/v1/pipeline-graphs/{stage}/{variant}` | contracts/openapi/internal.yaml | header `X-Internal-Token`; worker retries 5× with backoff 1,2,4,8,16 s on network error/5xx |
| api → worker (maintenance) | arq jobs `drop_collection`, `delete_points` on queue `query` | contracts/jobs/drop_collection.schema.json, delete_points.schema.json | no callback, idempotent |
| worker → api (liveness) | Redis key `ragfun:worker:{queue}:heartbeat`, EX 30, every 10 s | contracts/events/worker.heartbeat.schema.json | read by GET /status |
| api → web (run changes) | Redis pub/sub `events:{run_id}` → SSE | contracts/events/run.updated.schema.json | web refetches the run |
| worker → api (progress) | Redis pub/sub channel `events:{run_id}` | contracts/events/*.schema.json | api relays to SSE subscribers unchanged; fire-and-forget |
| worker → S3 `artifacts` | object write | contracts/artifacts/*.schema.json | key layout in §4 |
| api → S3 `artifacts` | object read (serve to web) | contracts/artifacts/*.schema.json | api returns the JSON as-is |
| worker → Qdrant | gRPC/REST via QdrantDocumentStore + qdrant-client | contracts/qdrant/payload.schema.json | |
| api → Qdrant | REST read-only (collections info, scroll, count) | contracts/qdrant/payload.schema.json | never upsert/delete |
| worker → Ollama / Anthropic / OpenAI-compatible | HTTP via Haystack generators/embedders | – | model config from job payload only |

## 4. Data
**api — Postgres 17 database `ragfun`**, SQLAlchemy 2.1 async (asyncpg), migrations with Alembic in
`services/api/alembic/`, schema in `services/api/src/rag_api/db/models.py`. **Exact DDL: plan/services/api.schema.sql** (wins over the summary below). Tables:
- `batches` (id, name, tags text[], created_at)
- `files` (id, batch_id, filename, mime, size_bytes, s3_key, sha256, tags text[], created_at)
- `collections` (id, name unique, qdrant_name unique, dense_model, dense_dims, sparse_model, created_at)
- `ingest_runs` (id, file_id, collection_id, run_all_plan jsonb, created_at) — one learning run of one file into one collection
- `stage_runs` (id, run_id, run_kind `ingest|query`, stage, version int, params jsonb, status
  `queued|running|done|failed|stale`, artifact_key text null, summary jsonb, error jsonb null,
  started_at, finished_at) — unique (run_id, stage, version)
- `query_runs` (id, collection_id, question, run_all_plan jsonb, created_at) — filters live in the retrieve stage params
- `settings` (key text pk, value jsonb, updated_at) — single row `key='app'`; one model + key per provider, plus the active `chat_provider`
- `pipeline_graphs` (stage, variant pk, graph jsonb, updated_at) — written via the internal API at worker startup

**S3 (RustFS)** — bucket `uploads` (api writes): `uploads/{batch_id}/{file_id}/{filename}`.
Bucket `artifacts` (worker writes): `artifacts/{run_id}/{stage}/v{version}.json` (+ for parse:
`artifacts/{run_id}/parse/v{version}/page-{n}.png`). Artifact JSON shapes in contracts/artifacts/.

**worker — Qdrant**: one Qdrant collection per `collections` row, name `rf_{collection_id_hex}`
(UUID without dashes). Created through `QdrantDocumentStore(use_sparse_embeddings=True, sparse_idf=True)`,
so the named vectors are qdrant-haystack's fixed names: dense `text-dense` (cosine, size = dense_dims)
and sparse `text-sparse` (IDF modifier). Payload = Haystack `Document.to_dict(flatten=False)` without
vectors, i.e. `{id, content, blob, meta, score}`; all our tags live under `meta.*` — exact shape in
contracts/qdrant/payload.schema.json. Payload indexes (keyword): `meta.file_id`, `meta.batch_id`,
`meta.tags`, `meta.mime`, `meta.element_type`, `meta.chunk_strategy`, `meta.parse_strategy`;
(integer): `meta.page`, `meta.chunk_index`. Haystack document id = `"{file_id}:{chunk_index:05d}"`;
Qdrant point id = qdrant-haystack `convert_id(doc_id)` = `uuid5(3896d314-1e95-4a3a-b45a-945f9f0b541d, doc_id)`
as 32-char hex. Store first deletes points with `meta.file_id = X`, then writes (DuplicatePolicy.OVERWRITE),
so re-storing is idempotent.

Redis: arq queues `ingest`, `query`; pub/sub `events:{run_id}`. No persistence needed.

## 5. Cross-cutting decisions
| Topic | Decision |
|---|---|
| IDs | UUIDv7 strings in canonical 8-4-4-4-12 form (`str(uuid_utils.uuid7())`), except Haystack document / Qdrant point ids (§4) |
| Time | UTC, ISO-8601 with `Z`, e.g. `2026-11-01T18:22:05.123Z` |
| Errors | `{ "error": { "code": "FILE_NOT_FOUND", "message": "...", "details": {} } }`; codes + HTTP status in contracts/shared/errors.json; stage failures store the same shape in `stage_runs.error` |
| Logging | JSON lines to stdout via structlog: `ts`, `level`, `service`, `msg`, `run_id` (when known), `stage` (when known) |
| Config | env vars only, read once at startup with pydantic-settings; full list in §6. `docker-compose.yml` loads `.env.defaults` (committed, all values preset); optional `.env` (gitignored) overrides |
| Bootstrap | api startup, idempotent, in order: `alembic upgrade head` → create buckets `uploads`, `artifacts` if missing → insert `settings` row `app` with defaults if missing → create collection `default` (bge-m3 + bm25) if no collection exists. worker startup: create Qdrant collection for every collection it is asked to store into if missing; post pipeline graphs |
| Start script | steps, each printing one status line: (1) `docker info` ok, else print "Start Docker Desktop" and exit 1; (2) `ollama` on PATH, else print `https://ollama.com/download` and exit 1; (3) `GET http://localhost:11434/api/tags`, if down start `ollama serve` in background and wait ≤30 s; (4) `ollama pull` each of `qwen3:8b`, `bge-m3` not yet in tags; (5) `docker compose up -d --build --wait` (first run builds the worker image with model files — prints "first start takes 10–20 min"); (6) poll `http://localhost:8080/api/v1/health` ≤120 s; (7) open `http://localhost:8080` (`open` on macOS, `xdg-open` on Linux, `Start-Process` on Windows). Flag `--no-browser` skips 7. Exit 0 only after 6 succeeds |
| Startup order | compose healthchecks: postgres, redis, qdrant, s3 healthy → api healthy (`/api/v1/health`) → worker-ingest, worker-query, web |
| Auth (users) | none — single local user; services bind to `127.0.0.1` on the host |
| Auth (worker → api) | shared secret header `X-Internal-Token` = `INTERNAL_TOKEN`; `/internal/*` rejects otherwise with `UNAUTHORIZED` |
| Secrets | API keys entered in Settings are stored in Postgres `settings`; GET /settings returns them masked (`sk-…abcd`); they leave the api only inside job payloads |
| Stage versions | every (re)run of a stage creates a new `stage_runs` row with version+1; the latest `done` version is "active"; downstream stages' latest rows are set to `stale` |
| Large numbers | vectors in artifacts are float32 rounded to 6 decimals; similarity matrix and heatmap capped at 200 chunks (sampled evenly, sample indices recorded) |
| Determinism (tests) | `MODEL_BACKEND=fake` makes the worker use `FakeDenseEmbedder` (hash-seeded vectors), `FakeSparseEmbedder`, `FakeRanker`, `FakeChatGenerator` (echo); used by e2e and all worker tests. No test calls a real model |
| Model files | Docling layout/table models, EasyOCR (en), fastembed sparse + reranker models, NLTK punkt and the 4 tokenizers are downloaded **at worker image build**; runtime is offline except Ollama/API calls |

## 6. Environment variables
| Var | Service | Example | Required |
|---|---|---|---|
| `DATABASE_URL` | api | `postgresql+asyncpg://ragfun:ragfun@postgres:5432/ragfun` | yes |
| `REDIS_URL` | api, worker | `redis://redis:6379/0` | yes |
| `S3_ENDPOINT_URL` | api, worker | `http://s3:9000` | yes |
| `S3_ACCESS_KEY` | api, worker | `ragfun` | yes |
| `S3_SECRET_KEY` | api, worker | `ragfun-secret` | yes |
| `S3_BUCKET_UPLOADS` | api, worker | `uploads` | yes |
| `S3_BUCKET_ARTIFACTS` | api, worker | `artifacts` | yes |
| `QDRANT_URL` | api, worker | `http://qdrant:6333` | yes |
| `INTERNAL_TOKEN` | api, worker | `dev-internal-token` | yes |
| `API_INTERNAL_URL` | worker | `http://api:8000` | yes |
| `OLLAMA_URL_DEFAULT` | api | `http://host.docker.internal:11434` | yes (seed for settings) |
| `MAX_UPLOAD_MB` | api | `50` | no (default 50) |
| `MAX_FILES_PER_BATCH` | api | `20` | no (default 20) |
| `MODEL_BACKEND` | worker | `real` or `fake` | no (default `real`) |
| `WORKER_QUEUE` | worker | `ingest` or `query` | yes |
| `LOG_LEVEL` | api, worker | `INFO` | no (default INFO) |
| `VITE_API_BASE` | web | `/api/v1` | no (default `/api/v1`) |

## 7. Repo layout
```
services/
  api/        src/rag_api/{main.py,config.py,errors.py,logging.py,db/,routes/,services/,s3.py,qdrant_read.py,queue.py,events.py}
              tests/{unit/,integration/}, alembic/, pyproject.toml, uv.lock, Dockerfile
  worker/     src/rag_worker/{main.py,config.py,errors.py,logging.py,jobs/,pipelines/,components/,viz/,models/,s3.py,report.py}
              tests/{unit/,integration/}, pyproject.toml, uv.lock, Dockerfile
  web/        src/{main.tsx,App.tsx,api/,pages/,components/,viz/,hooks/,lib/}, tests/, package.json, package-lock.json, vite.config.ts, Dockerfile
contracts/    openapi/{api.yaml,internal.yaml}, jobs/, events/, artifacts/, qdrant/, shared/{common,summary,pipeline-graph}.schema.json, shared/errors.json, README.md (index + test plan)
tests/contract_fixtures/  one valid example JSON per contract schema (planner-written, shared by all services)
tests/e2e/    pytest + httpx against the running stack (MODEL_BACKEND=fake), fixtures/ (sample files)
plan/         SYSTEM.md, services/, features.yaml, tasks/, TRACEABILITY.md
docker-compose.yml       full app (web, api, worker-ingest, worker-query, postgres, redis, qdrant, s3), named volumes for data
.env.defaults            committed defaults for every var in §6
start.sh, stop.sh        one-command start/stop for macOS/Linux (bash)
start.cmd, stop.cmd      Windows wrappers → start.ps1, stop.ps1 (PowerShell 5.1+, ExecutionPolicy Bypass)
docker-compose.dev.yml   toolchain containers + test infra for the executor
```

## 8. Conventions per language
### Python (api, worker)
- Package manager: **uv 0.13.6**; deps pinned exactly in `pyproject.toml`, full lock in `uv.lock`.
  Commands always `uv run --frozen …`.
- Formatter + linter: ruff 0.17.3 (`ruff format`, `ruff check`), line length 100, rules `E,F,I,B,UP,ASYNC`.
- Types: mypy 2.4.1 on `src/` with `disallow_untyped_defs = true`, `ignore_missing_imports = true`.
- Tests: pytest 9.2.0 + pytest-asyncio 1.4.1 (`asyncio_mode = "auto"`). Files `tests/unit/test_<module>.py`,
  functions `test_<behaviour>`. Unit tests use no network; integration tests (`tests/integration/`) use
  the compose test infra (`postgres-test`, `redis-test`, `qdrant-test`, `s3-test`).
- Async everywhere in api (FastAPI async routes, async SQLAlchemy, aioboto3). Worker job functions are
  `async def job_name(ctx, payload: dict) -> dict`; CPU-heavy Haystack calls run via `asyncio.to_thread`.
- Errors: raise `AppError(code, message, details)` from `errors.py`; never return error dicts by hand.
- api module layout — one route module per resource, logic in `services/`, copy this pattern:
```python
# services/api/src/rag_api/routes/collections.py  (example module, written in the skeleton)
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from rag_api.db.session import get_session
from rag_api.schemas.collections import CollectionCreate, CollectionOut
from rag_api.services import collections as svc

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("/{collection_id}", response_model=CollectionOut)
async def get_collection(collection_id: str, session: AsyncSession = Depends(get_session)) -> CollectionOut:
    return await svc.get_collection(session, collection_id)  # raises AppError("COLLECTION_NOT_FOUND")
```
- worker layout — one job module per stage in `jobs/` (`async def <stage>(ctx, payload)` = `report.run_stage`
  wrapper, `<stage>_body(job, rep, ctx)` returns (artifact, summary)), Haystack pipeline builders in
  `pipelines/`, custom Haystack components in `components/` (one class per file, `@component`, typed
  `output_types`, pure helpers at module level, never mutate input Documents — use `dataclasses.replace`),
  visualization math in `viz/` (pure functions, plain lists out). Example component (written in the skeleton):
  `services/worker/src/rag_worker/components/chunk_annotator.py` with `tests/unit/test_chunk_annotator.py`.

### TypeScript (web)
- Formatter: prettier 3.9.10 (2 spaces, single quotes, no semicolons, width 100). Linter: eslint 10.14.0 +
  typescript-eslint 8.72.1 + eslint-plugin-react-hooks 7.1.1. `strict: true` in tsconfig.
- Tests: vitest 5.0.5 + @testing-library/react 16.3.3 + jsdom 30.1.3; API mocked with msw 3.0.3.
  Files `tests/<area>/<Component>.test.tsx`.
- API types generated from contracts/openapi/api.yaml with openapi-typescript 7.13.0 into
  `src/api/schema.d.ts` (generated, never hand-edited); fetch wrappers in `src/api/*.ts`; server state via
  @tanstack/react-query only (no global state lib).
- Styling: Tailwind 4.3.3 utility classes only. Charts: Plotly (`react-plotly.js`) for scatter/heatmap/
  histogram/similarity; @xyflow/react for pipeline graphs; page bounding boxes as absolutely-positioned
  divs over the page `<img>`.
- File names: components `PascalCase.tsx`, hooks `useThing.ts`, others `camelCase.ts`. One component per file.
- Component pattern — copy this:
```tsx
// services/web/src/pages/CollectionsPage.tsx  (example module, written in the skeleton)
import { useCollections } from '../hooks/useCollections'
import { ErrorBox } from '../components/ErrorBox'

export function CollectionsPage() {
  const { data, error, isLoading } = useCollections()
  if (isLoading) return <p className="p-4 text-sm text-gray-500">Loading…</p>
  if (error) return <ErrorBox error={error} />
  return (
    <ul className="divide-y">
      {data!.items.map((c) => (
        <li key={c.id} className="p-3">{c.name} <span className="text-gray-500">{c.dense_model}</span></li>
      ))}
    </ul>
  )
}
```

## 9. Allowed dependencies (executor may NOT add any)
| Service | Package | Version | Purpose |
|---|---|---|---|
| api | fastapi | 0.162.0 | web framework |
| api | uvicorn[standard] | 0.54.0 | ASGI server |
| api | pydantic | 2.14.2 | models |
| api | pydantic-settings | 2.16.2 | env config |
| api | sqlalchemy[asyncio] | 2.1.6 | ORM |
| api | asyncpg | 0.32.0 | Postgres driver |
| api | alembic | 1.20.1 | migrations |
| api | arq | 0.28.0 | enqueue jobs |
| api | redis | 5.3.1 | pub/sub for SSE |
| api | sse-starlette | 3.6.0 | SSE responses |
| api | python-multipart | 0.0.33 | uploads |
| api | aioboto3 | 15.5.0 | S3 |
| api | qdrant-client | 1.20.0 | read-only browser |
| api | httpx | 0.28.1 | test-connection to model providers |
| api | structlog | 26.1.0 | logging |
| api | uuid-utils | 1.2.0 | UUIDv7 |
| api (dev) | pytest 9.2.0, pytest-asyncio 1.4.1, ruff 0.17.3, mypy 2.4.1, respx 0.23.1, jsonschema 4.26.0, pyyaml 6.0.3 | | tests/lint; contract validation in tests |
| worker | haystack-ai | 3.4.1 | pipeline engine |
| worker | qdrant-haystack | 13.1.0 | QdrantDocumentStore, hybrid retriever |
| worker | ollama-haystack | 7.0.2 | Ollama embedder + chat generator |
| worker | anthropic-haystack | 8.0.1 | Anthropic chat generator |
| worker | fastembed-haystack | 3.0.0 | sparse embedders (BM25, SPLADE), cross-encoder ranker |
| worker | fastembed | 0.9.1 | (via above) |
| worker | docling[easyocr] | 2.145.0 | parsing, layout, tables, OCR |
| worker | docling-haystack | 3.0.0 | DoclingConverter, HybridChunker export |
| worker | pypdf | 6.21.4 | `plain_text` parse strategy |
| worker | nltk | 3.10.4 | sentence splitting (Haystack) |
| worker | tokenizers | 0.23.3 | token view |
| worker | numpy | 2.5.4 | vector math |
| worker | scikit-learn | 1.9.1 | PCA, cosine similarity |
| worker | umap-learn | 0.5.12 | UMAP projection |
| worker | qdrant-client | 1.20.0 | delete-by-filter, collection creation |
| worker | arq | 0.28.0 | job runner |
| worker | redis | 5.3.1 | progress pub/sub |
| worker | aioboto3 | 15.5.0 | S3 |
| worker | httpx | 0.28.1 | callback to api |
| worker | pydantic 2.14.2, pydantic-settings 2.16.2, structlog 26.1.0, uuid-utils 1.2.0 | | models/config/logging/ids |
| worker (dev) | pytest 9.2.0, pytest-asyncio 1.4.1, ruff 0.17.3, mypy 2.4.1, respx 0.23.1, jsonschema 4.26.0, pyyaml 6.0.3 | | tests/lint; contract validation in tests |
| web | react, react-dom | 19.3.1 | UI |
| web | react-router | 8.5.1 | routing |
| web | @tanstack/react-query | 5.104.5 | server state |
| web | plotly.js-dist-min | 4.2.0 | charts |
| web | react-plotly.js | 4.1.0 | Plotly React binding |
| web | @xyflow/react | 12.12.0 | pipeline graph |
| web | tailwindcss, @tailwindcss/vite | 4.3.3 | styling |
| web (dev) | vite 8.3.5, @vitejs/plugin-react 6.1.2, typescript 5.9.3, vitest 5.0.5, @testing-library/react 16.3.3, @testing-library/jest-dom 7.0.1, jsdom 30.1.3, msw 3.0.3, eslint 10.14.0, typescript-eslint 8.72.1, eslint-plugin-react-hooks 7.1.1, prettier 3.9.10, openapi-typescript 7.13.0, @types/react 19.3.0, @types/react-plotly.js 2.6.4, @types/node 24.19.2 | | build/tests/lint |
| e2e | pytest 9.2.0, httpx 0.28.1, jsonschema 4.26.0, pyyaml 6.0.3 | | acceptance tests (run in `e2e-dev` container) |

## 9a. Models (defaults; user can change in Settings / per collection)
| Role | Default | Alternatives offered | Runs where |
|---|---|---|---|
| Chat / generation / query transforms | Ollama `qwen3:8b` | any pulled Ollama model; Anthropic `claude-sonnet-5-5`; any OpenAI-compatible model by name | host (Ollama, Metal/CUDA) or API |
| Dense embedding | Ollama `bge-m3` (1024 d, 8192 tok) | `nomic-embed-text` (768), `mxbai-embed-large` (1024), `all-minilm` (384) — fixed list, each with a baked tokenizer | host (Ollama) |
| Sparse embedding | fastembed `Qdrant/bm25` | `prithivida/Splade_PP_en_v1` | worker container (CPU) |
| Reranker | fastembed `Xenova/ms-marco-MiniLM-L-6-v2` | `BAAI/bge-reranker-base` | worker container (CPU) |
| OCR | Docling + EasyOCR, language `en` | – | worker container (CPU) |

## 9b. Stages and their parameters
| Stage | Strategies / params | Haystack building blocks | Artifact |
|---|---|---|---|
| parse | `docling_layout` (tables on, OCR only for bitmap regions), `docling_ocr` (force full-page OCR), `plain_text` (pypdf for PDF; md, txt, html, csv read directly; images and office formats → `UNSUPPORTED_FOR_STRATEGY`) | `DoclingConverter` (ExportType.JSON), custom `PlainTextConverter` | parse.schema.json: pages (png key, size), elements (id, type, text, page, bbox, table cells) |
| chunk | `fixed` (split_by word/token, length, overlap), `sentence` (sentences per chunk, overlap), `recursive` (separators, length, overlap), `semantic` (breakpoint percentile 50–99, min/max sentences), `structure` (Docling HybridChunker, max_tokens, merge_peers), `table` (each table = 1 chunk as markdown, optional row-wise chunks with header repeated; non-table text falls back to `recursive`) | `DocumentSplitter`, `RecursiveDocumentSplitter`, custom `SemanticSplitter`, `DoclingConverter` (DOC_CHUNKS), custom `TableChunker` | chunk.schema.json: chunks (index, text, char span in source, element ids, section path, element_type, token estimate) |
| embed | collection's dense + sparse model; batch size 16 | `OllamaDocumentEmbedder`, `FastembedSparseDocumentEmbedder`, custom `ModelTokenizer` | embed.schema.json: per chunk dense vector, sparse indices/values, tokens; projections pca2/pca3/umap2/umap3; similarity matrix; sample indices |
| store | none (uses collection) | `QdrantDocumentStore` (`use_sparse_embeddings=True`), `DocumentWriter` (policy OVERWRITE) | store.schema.json: collection name, points written, point ids, payload sample |
| transform | `none`, `rewrite`, `multi_query` (n=3), `hyde` | `ChatPromptBuilder` + chat generator | transform.schema.json |
| retrieve | `dense`, `sparse`, `hybrid` (RRF k=60), top_k 1–50, filters | `QdrantEmbeddingRetriever`, `QdrantSparseEmbeddingRetriever`, custom `RRFJoiner` (exposes per-list ranks) | retrieve.schema.json: dense list, sparse list, fused list, each with id, score, rank, payload |
| rerank | top_k in, top_n out, on/off | `FastembedRanker` | rerank.schema.json: before/after |
| generate | max context tokens, temperature, citation style `[n]` | `ChatPromptBuilder` + chat generator (streaming callback → pub/sub) | generate.schema.json: prompt messages, token budget, answer, citations |

## 10. Out of scope
- Multi-user, login, sharing, cloud deployment, HTTPS.
- Vision-language captioning and multimodal (CLIP) image embeddings — images are covered by OCR only.
- Hosted embedding providers (OpenAI, Voyage, Cohere) — embeddings are always local via Ollama.
- Native opencode HTTP API adapter — opencode-served models are reached via the OpenAI-compatible URL.
- Evaluation (recall@k, faithfulness) and side-by-side strategy comparison.
- Ollama model management from the UI (pulling models) — user runs `ollama pull`; UI only lists installed models.
- Conversation memory / multi-turn chat; each query is independent.
- Running Ollama inside Docker; GPU inside containers.

## 11. Decisions log
| # | Decision | Reason | Alternatives rejected |
|---|---|---|---|
| 1 | Visual RAG learning lab, step-by-step with "Run all" | user goal: every stage separated and visualized | automatic pipeline with post-hoc inspection |
| 2 | Haystack 3.4.1 as the only RAG engine, all pipelines in worker | user choice; keeps api free of ML deps | LangChain, LlamaIndex, hand-written |
| 3 | Services web (React) + api (FastAPI) + worker (arq, 2 containers) | rich visuals need React; ML work isolated; ingest can't block queries | Streamlit/Gradio; single service |
| 4 | Ollama native on host | Docker on macOS has no GPU; native gives Metal on Mac and CUDA on Windows → same experience | Ollama in Docker (CPU-only on Mac) |
| 5 | Embeddings local-only, chat overridable (Anthropic, OpenAI-compatible) | user choice; Anthropic has no embedding API | hosted embeddings |
| 6 | Opencode support via generic OpenAI-compatible URL | opencode's own server API is session-based and unstable; its backing model servers are OpenAI-compatible | native opencode adapter |
| 7 | Qdrant v1.19.2 with named dense + sparse vectors per collection | user choice; hybrid search native | Chroma, pgvector |
| 8 | RustFS 1.0.3 as local S3 | MinIO no longer publishes community Docker images; RustFS is S3-compatible, Apache-2.0, has a web console | MinIO (no image), SeaweedFS (heavier config) |
| 9 | Postgres 17 for metadata/runs/settings; large artifacts as JSON in S3 | concurrent api writes, JSONB; keeps DB small | SQLite |
| 10 | Redis + arq for jobs, Redis pub/sub + SSE for progress, REST callback for results | async, lightweight; callback has retries and a testable contract | Celery, Postgres queue + polling |
| 11 | OCR via Docling + EasyOCR only for images | user choice | VLM captioning, CLIP |
| 12 | Single local user, no auth; bind to 127.0.0.1 | local learning tool | login, workspaces |
| 13 | Auto + user tags in Qdrant payload with keyword indexes | user choice; enables filter builder | auto only, user-defined typed schema |
| 14 | `MODEL_BACKEND=fake` deterministic models for all tests | weak executor + unattended run need deterministic, offline tests | real Ollama in tests |
| 15 | All model files baked into worker image at build | offline, reproducible runtime | lazy download at first use |
| 16 | TypeScript 5.9.3 (not 7.x) | typescript-eslint 8.72 supports only TS < 6.1 | TS 7 |
| 17 | Fixed list of 4 dense models, each with a baked tokenizer for the token view | token counts must be exact, Ollama does not expose tokenizers | arbitrary Ollama embed models |
| 18 | Default chat `qwen3:8b`, embed `bge-m3` | run well on 16 GB Mac and 8 GB-VRAM Windows GPU; bge-m3 multilingual, long context | larger models |
| 19 | One-command start scripts (`start.sh` / `start.cmd`→`start.ps1`) that also open the browser | user requirement; compose alone cannot check Ollama, pull models or open a browser; no `make` on Windows | Makefile, compose only, Electron/Tauri launcher |
| 20 | Web served by nginx on port 8080 in the app stack | static build + same-origin `/api` proxy, no CORS; Vite dev server only in dev | Vite preview in production, CORS |
| 21 | Contracts as JSON Schema 2020-12 + OpenAPI 3.1; pydantic models generated with datamodel-code-generator 0.87.0 and TS types with openapi-typescript 7.13.0 by the planner, output committed | weak executor must not hand-write wire models; generators are planner tools, not service deps | hand-written models everywhere |
| 22 | Explicit per-stage endpoints (`POST /ingest-runs/{id}/stages/chunk`, …) instead of one generic stage endpoint | each body has its own typed schema; codegen and validation stay simple | `POST …/stages/{stage}` with untyped params |
| 23 | redis-py 5.3.1 (not 8.x) in api and worker | arq 0.28 requires redis<6 | other job queue |
| 24 | Worker image bakes Docling, EasyOCR, fastembed, NLTK and tokenizer files (~11 GB image, CPU-only torch from the PyTorch CPU index) | offline + reproducible runtime; GPU work happens in native Ollama | download at first use |

## 12. Open questions
(none)
