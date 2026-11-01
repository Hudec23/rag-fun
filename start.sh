#!/usr/bin/env bash
# One-command start for macOS / Linux: checks Docker + Ollama, pulls default models, starts every
# container and opens the UI. Usage: ./start.sh [--no-browser]
set -euo pipefail
cd "$(dirname "$0")"

URL="http://localhost:8080"
OLLAMA="http://localhost:11434"
MODELS=("qwen3:8b" "bge-m3")
OPEN_BROWSER=1
[[ "${1:-}" == "--no-browser" ]] && OPEN_BROWSER=0

step() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31mxx\033[0m %s\n' "$*" >&2; exit 1; }

step "Checking Docker"
docker info >/dev/null 2>&1 || fail "Docker is not running. Start Docker Desktop and run ./start.sh again."

step "Checking Ollama"
command -v ollama >/dev/null 2>&1 || fail "Ollama is not installed. Get it from https://ollama.com/download and run ./start.sh again."
if ! curl -fsS "$OLLAMA/api/tags" >/dev/null 2>&1; then
  step "Starting Ollama in the background"
  (ollama serve >/dev/null 2>&1 &)
  for _ in $(seq 1 30); do curl -fsS "$OLLAMA/api/tags" >/dev/null 2>&1 && break; sleep 1; done
  curl -fsS "$OLLAMA/api/tags" >/dev/null 2>&1 || fail "Ollama did not start within 30 s."
fi

TAGS="$(curl -fsS "$OLLAMA/api/tags")"
for m in "${MODELS[@]}"; do
  if grep -q "\"name\":\"$m\(:latest\)\?\"" <<<"$TAGS"; then
    step "Model $m already installed"
  else
    step "Pulling model $m (one time)"
    ollama pull "$m"
  fi
done

step "Starting containers (first start builds images and takes 10-20 min)"
docker compose up -d --build --wait

step "Waiting for the api"
for _ in $(seq 1 120); do
  curl -fsS "$URL/api/v1/health" >/dev/null 2>&1 && break
  sleep 1
done
curl -fsS "$URL/api/v1/health" >/dev/null 2>&1 || fail "The api did not become healthy in 120 s. See: docker compose logs api"

step "rag-fun is running at $URL"
if [[ $OPEN_BROWSER == 1 ]]; then
  if command -v open >/dev/null 2>&1; then open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" >/dev/null 2>&1 || true
  fi
fi
