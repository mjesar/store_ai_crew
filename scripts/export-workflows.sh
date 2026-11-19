#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

docker compose exec -T n8n rm -rf /tmp/workflows
docker compose exec -T n8n n8n export:workflow --all --published --pretty --separate --output=/tmp/workflows/
rm -f n8n/workflows/*.json
mkdir -p n8n/workflows
docker compose cp n8n:/tmp/workflows/. n8n/workflows/

for f in n8n/workflows/*.json; do
  jq 'del(.shared)' "$f" > "$f.tmp" && mv "$f.tmp" "$f"
done
