#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting Ollama container..."
docker compose -f "$PROJECT_DIR/docker-compose.yml" up -d ollama

echo "Waiting for Ollama to be ready..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama is ready!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: Ollama did not start within 30 seconds"
        exit 1
    fi
    sleep 1
done

echo "Pulling OpenBioLLM model (this may take a while on first run)..."
docker exec gr8doctor-ollama ollama pull openbiollm

echo "Setup complete! Ollama is running with OpenBioLLM."
echo "Verify: curl http://localhost:11434/api/tags"
