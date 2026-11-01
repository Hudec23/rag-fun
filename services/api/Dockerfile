# syntax=docker/dockerfile:1.7
FROM python:3.12.16-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /uvx /bin/
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH

# Toolchain for the executor: code is mounted at /workspace, venv lives in a named volume.
FROM base AS dev
WORKDIR /workspace/services/api

FROM base AS runtime
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
RUN uv sync --frozen --no-dev
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --retries=30 CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health').status==200 else 1)"
CMD ["uvicorn", "rag_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
