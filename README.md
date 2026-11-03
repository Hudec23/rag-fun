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
The full spec is [`.autospec/plan/SYSTEM.md`](.autospec/plan/SYSTEM.md).

Configuration: `docker-compose.yml` loads [`.env.defaults`](.env.defaults) (all values preset).
Put overrides in an optional `.env` (gitignored). Chat provider, models and API keys are set in the
Settings page, not in env vars.

## Checking the code

All checks run in containers; the host only needs Docker. Tests use `MODEL_BACKEND=fake`
(deterministic fake embedders, ranker and chat), so no test calls a real model.

```sh
D="docker compose -f docker-compose.dev.yml run --rm"
E="docker compose -p ragfun-e2e -f docker-compose.yml -f docker-compose.e2e.yml"

# lint + types + unit/integration tests, per service (svc = api | worker)
$D api-dev sh -c 'uv run --frozen ruff format --check . && uv run --frozen ruff check . && uv run --frozen mypy src && uv run --frozen pytest -q'
$D web-dev sh -c 'npm run build && npm run lint && npx vitest run'

# end-to-end: full stack with fake models, no host ports (safe next to the running app)
$E up -d --build --wait && $E --profile e2e run --rm e2e pytest -q; $E down -v
```

Swap `api-dev` for `worker-dev` to check the worker. To run one e2e feature, pass its file:
`pytest -q /workspace/tests/e2e/test_generate.py`. After editing `contracts/`, validate them with
`scripts/validate-contracts.py` (the Docker command is in its docstring) and regenerate the pydantic
models with `scripts/gen-contracts.sh`.

**Manual check with real models.** The automated suites never touch Ollama, Docling, OCR or the
reranker. After `./start.sh`, walk one file through the UI:

1. Upload a PDF and a scanned image, then tag them.
2. Parse the PDF with `docling_layout` (bounding boxes appear) and the image with `docling_ocr`.
   Then chunk, embed and store.
3. In the Qdrant browser, the points exist, the tag filter narrows them, and a point shows its
   vectors.
4. Ask a question about the PDF with `hybrid` retrieval and rerank on. The answer should stream in,
   and its `[n]` citations should link to the chunks.
5. In Settings, "test connection" succeeds for Ollama.

## Repository layout

```
services/api               FastAPI app, alembic migrations, tests
services/worker            Haystack jobs and pipelines, tests
services/web               React app, vitest tests
contracts/                 frozen cross-service interfaces (source of truth)
tests/e2e                  end-to-end tests, one file per feature
tests/contract_fixtures    one valid instance per contract message, shared by all suites
scripts/                   contract validation and codegen, fixture generator
start.* / stop.*           one-command start/stop (sh, ps1, cmd)
.autospec/                 the AI plan + build kit that produced this repo (see below)
```

## Autospec

rag-fun was planned by Claude and implemented, task by task, by a local model, using
[autospec-kit](https://github.com/Hudec23/autospec-kit). None of it is needed to run or develop
the app.

```
.autospec/
  kit/               the kit (git subtree; never edit it here, see "Update the kit")
  plan/              SYSTEM.md (spec), services/*.yaml, features.yaml, tasks/T-*.md, TRACEABILITY.md
  plan/generator/    this repo's task generator (planner tool)
  state.json         status of every task; runs/ holds logs (gitignored)
CLAUDE.md            imports the kit's planner instructions
AGENTS.md            this repo's commands for the executor (rules come from the kit)
opencode.json        local vLLM model, kit executor rules, rescue agent
```

**Plan or change the plan (Claude Code).** Open Claude Code in the repo root and run the planning
skills (`/autospec-system`, `/autospec-contracts`, `/autospec-tasks`, `/autospec-audit`). After any
plan change, run the checker; it regenerates `.autospec/plan/TRACEABILITY.md`:

```sh
docker run --rm -v "$PWD":/w -w /w python:3.12.16-slim sh -c \
  'pip install -q --root-user-action=ignore pyyaml==6.0.2 && python .autospec/kit/scripts/autospec-check.py'
```

**Build (the runner).** This needs [opencodocker](https://github.com/Hudec23/opencodocker).
Run it from a real terminal, because `run.sh` needs a TTY:

```sh
export AUTOSPEC_RUNNER=~/Dev/opencodocker/run.sh
python3 .autospec/kit/scripts/autospec-run.py --dry-run          # order + status
python3 .autospec/kit/scripts/autospec-run.py                    # run every pending task
python3 .autospec/kit/scripts/autospec-run.py --only T-api-001
```

Ctrl-C stops at once and leaves the task pending. `touch .autospec/STOP` stops after the current
task. To fix blocked tasks, run `/autospec-unblock` in Claude Code.

**Update the kit.**

```sh
git subtree pull --prefix .autospec/kit https://github.com/Hudec23/autospec-kit main --squash
sh .autospec/kit/init.sh && git add -A && git commit -m "Update autospec kit"
```

Do not rerun the task generator (`.autospec/plan/generator/gen.py`) on this finished repo. It
pastes the current stub source into every task, and the stubs are now real implementations.

## License

See [LICENSE](LICENSE).
