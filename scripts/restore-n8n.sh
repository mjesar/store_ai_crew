#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Only for an empty n8n: importing overwrites by ID, so the secret-free stubs would wipe
# credentials that already hold secrets (seen in the restore rehearsal)
credentials=$(docker compose exec -T n8n n8n export:credentials --all 2>/dev/null | sed -n '/^\[/,$p' | jq length 2>/dev/null || true)
workflows=$(docker compose exec -T n8n n8n list:workflow 2>/dev/null | grep -c '|' || true)
if [ "${credentials:-0}" -gt 0 ] || [ "${workflows:-0}" -gt 0 ]; then
  echo "This n8n already has ${credentials:-0} credentials and ${workflows:-0} workflows. Restore only runs on an empty n8n." >&2
  exit 1
fi

# Copies one repo folder into the container's /tmp, starting from an empty folder so files
# left over from an earlier run are not imported too
copy_in() {
  docker compose exec -T n8n rm -rf "/tmp/$1"
  docker compose exec -T n8n mkdir -p "/tmp/$1"
  docker compose cp "n8n/$1/." "n8n:/tmp/$1/"
}

# Credentials first: workflow nodes point at credentials by ID, so they must exist to link.
# The stubs hold no secrets; paste those in the editor afterwards.
copy_in credentials
docker compose exec -T n8n n8n import:credentials --separate --input=/tmp/credentials/

# Imported workflows arrive unpublished on purpose: publish each one by hand once its
# credentials are filled in, so a half-set-up workflow never goes live
copy_in workflows
docker compose exec -T n8n n8n import:workflow --separate --input=/tmp/workflows/
