#!/usr/bin/env bash
# Stops every rag-fun container (data volumes are kept). Ollama keeps running.
set -euo pipefail
cd "$(dirname "$0")"
docker compose stop
echo "rag-fun stopped. Data is kept; ./start.sh starts it again."
