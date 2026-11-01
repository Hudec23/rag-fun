# syntax=docker/dockerfile:1.7
FROM python:3.12.16-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /uvx /bin/
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH \
    MODELS_DIR=/opt/models \
    HF_HOME=/opt/models/hf \
    FASTEMBED_CACHE_PATH=/opt/models/fastembed \
    NLTK_DATA=/opt/models/nltk \
    DOCLING_ARTIFACTS_PATH=/opt/models/docling \
    EASYOCR_MODULE_PATH=/opt/models/docling/EasyOcr \
    NUMBA_CACHE_DIR=/tmp/numba

# Dependencies (no project code) + all model files, shared by dev and runtime.
FROM base AS deps
WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project
COPY docker/download_models.py ./
RUN python download_models.py

# Toolchain for the executor: code mounted at /workspace; /opt/venv is pre-populated
# (a fresh named volume copies it), `uv sync --frozen` then only installs the project + dev group.
FROM deps AS dev
ENV HF_HUB_OFFLINE=1
WORKDIR /workspace/services/worker

FROM deps AS runtime
ENV HF_HUB_OFFLINE=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev
CMD ["arq", "rag_worker.main.WorkerSettings"]
