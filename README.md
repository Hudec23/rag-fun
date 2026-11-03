# rag-fun

A local, single-user **visual lab for Retrieval-Augmented Generation**. Upload files and walk them
through every RAG stage one step at a time, inspecting what each stage produced before running the
next:

upload → **parse** → **chunk** → **embed** → **store** (Qdrant) → query **transform** → **retrieve** →
**rerank** → **generate** (with citations)

Every stage is a separate, re-runnable step with its own parameters, its own visualization, and the
real Haystack pipeline graph behind it. Runs fully locally with Ollama; no API key needed.

## Quick start

Requirements: [Docker Desktop](https://www.docker.com/products/docker-desktop/) and
[Ollama](https://ollama.com/download), both on the host.

```sh
./start.sh          # macOS / Linux   (start.cmd on Windows)
./stop.sh           # stop.cmd on Windows; data is kept
```

`start.sh` checks Docker and Ollama, pulls `qwen3:8b` and `bge-m3` if missing, runs
`docker compose up -d --build --wait`, waits for the api and opens <http://localhost:8080>.
The **first start takes 10–20 min**: the worker image downloads its Docling, OCR, sparse-embedding
and reranker models at build time, so later runs are offline except for model calls.
`./start.sh --no-browser` skips opening the browser.

Wipe all data (database, Qdrant, S3): `docker compose down -v`.

## What's in the UI

| Page | Path | What you do there |
|---|---|---|
| Files | `/` | Upload batches (drag & drop), tag files and batches, start ingest runs |
| Ingest run | `/ingest/:runId` | Parse (`docling_layout`, `docling_ocr`, `plain_text`) → chunk (`fixed`, `sentence`, `recursive`, `semantic`, `structure`, `table`) → embed (inspect tokens, heatmap, PCA/UMAP scatter, similarity matrix) → store |
| Query | `/query`, `/query/:runId` | Transform (`none`, `rewrite`, `multi_query`, `hyde`) → retrieve (`dense`, `sparse`, `hybrid` + filters) → rerank → generate (prompt, token budget, streamed answer, citations) |
| Qdrant browser | `/qdrant/:collectionId?` | Collection info, paginated points, payload filter builder, raw JSON of a point |
| Collections | `/collections` | Create collections (dense + sparse model fixed per collection) |
| Pipelines | `/pipelines` | The actual Haystack pipeline graph of every stage |
| Settings | `/settings` | Chat provider: Ollama, Anthropic or any OpenAI-compatible endpoint; reranker on/off; test connection |

Re-running a stage creates a new version and marks downstream stages `stale`; "Run all" runs the
remaining stages with the current parameters. Progress streams live over SSE, and the status bar shows
the health of every service.

## Architecture

| Service | Stack | Role |
|---|---|---|
| `web` | React 19 + Vite, served by nginx on **:8080** | UI; proxies `/api` to the api |
| `api` | FastAPI + Postgres, **:8000** | REST + SSE, uploads, run/stage bookkeeping, settings, read-only Qdrant browser; enqueues jobs |
| `worker-ingest` / `worker-query` | Haystack + arq (one image, two queues) | Run every pipeline; write Qdrant and artifacts; report back to the api |
| postgres, redis, qdrant (**:6333**), s3 (rustfs, console **:9001**) | pinned images | Storage and queueing |
| Ollama | native on the host, `:11434` | Default chat (`qwen3:8b`) and dense embeddings (`bge-m3`) |

All ports bind to `127.0.0.1`. Every interface between services is a frozen contract in
[`contracts/`](contracts) (OpenAPI, JSON Schema for jobs, events, artifacts and the Qdrant payload).
The full spec is [`plan/SYSTEM.md`](plan/SYSTEM.md).

Configuration: `docker-compose.yml` loads [`.env.defaults`](.env.defaults) (all values preset).
Put overrides in an optional `.env` (gitignored). Chat provider, models and API keys are set in the
Settings page, not in env vars.

## Checking the code

Everything runs in containers; the host only needs Docker. Tests use `MODEL_BACKEND=fake`
(deterministic fake embedders, ranker and chat), so no test calls a real model.

**Lint, types and tests per service.** `docker-compose.dev.yml` starts throwaway
postgres/redis/qdrant/s3 test containers as needed:

```sh
D="docker compose -f docker-compose.dev.yml run --rm"

# api
$D api-dev sh -c 'uv run --frozen ruff format --check . && uv run --frozen ruff check . && uv run --frozen mypy src'
$D api-dev uv run --frozen pytest -q

# worker
$D worker-dev sh -c 'uv run --frozen ruff format --check . && uv run --frozen ruff check . && uv run --frozen mypy src'
$D worker-dev uv run --frozen pytest -q

# web
$D web-dev npm run build      # tsc -b && vite build
$D web-dev npm run lint       # prettier --check . && eslint .
$D web-dev npx vitest run
```

**End-to-end.** This runs the whole app stack with fake models in its own `ragfun-e2e` project. It
publishes no host ports, so it can run while the real app is up:

```sh
E="docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml"
$E up -d --build --wait
$E --profile e2e run --rm e2e pytest -q                                          # all of tests/e2e
$E --profile e2e run --rm e2e pytest -q /workspace/tests/e2e/test_generate.py    # one feature
$E down -v
```

**Contracts.** Run these after editing anything in `contracts/`:

```sh
docker run --rm -v "$PWD":/w -w /w python:3.12.16-slim sh -c \
  'pip install -q --root-user-action=ignore --disable-pip-version-check jsonschema==4.26.0 \
   openapi-spec-validator==0.9.0 pyyaml==6.0.3 && python scripts/validate-contracts.py'
scripts/gen-contracts.sh      # regenerate the pydantic models in services/*/src/*/contracts_gen
```

**Manual check with real models.** The automated suites never touch Ollama, Docling, OCR or the
reranker, so after `./start.sh` walk one file through the UI:

1. Files: upload a PDF and a scanned image, tag them.
2. Ingest run: parse the PDF with `docling_layout` (bounding boxes appear) and the image with
   `docling_ocr`; chunk, embed, store.
3. Qdrant browser: the points exist, the tag filter narrows them, a point shows its vectors.
4. Query: ask something from the PDF with `hybrid` retrieval and rerank on; the answer streams in and
   its `[n]` citations link to the chunks.
5. Settings: "test connection" succeeds for Ollama.

## Repository layout

```
services/api               FastAPI app, alembic migrations, tests
services/worker            Haystack jobs and pipelines, tests
services/web               React app, vitest tests
contracts/                 frozen cross-service interfaces (source of truth)
tests/e2e                  end-to-end tests, one file per feature
tests/contract_fixtures    one valid instance per contract message, shared by all suites
scripts/                   contract validation and codegen, fixture generator, autospec plan tools
start.* / stop.*           one-command start/stop (sh, ps1, cmd)
```

### How it was built

rag-fun was planned with Claude and then implemented task by task by a local model using
[autospec-kit](https://github.com/Hudec23/autospec-kit):

- `plan/` holds the spec, the per-service configs, the feature → test mapping and the 220 task files.
- `.autospec/state.json` records the status of each task.
- `planning/`, `templates/`, `CLAUDE.md`, `AGENTS.md` and `.opencode/` are the kit's prompts and agent
  rules.
- `scripts/autospec-check.py` checks the plan and regenerates `plan/TRACEABILITY.md`.
- `scripts/autospec-run.py` is the task runner.

None of this is needed to run or develop the app.

## License

See [LICENSE](LICENSE).
