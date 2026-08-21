#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
COMPOSE=(docker compose -f "$HERE/docker-compose.yml")

echo "Stopping fabric (volumes kept)..."
"${COMPOSE[@]}" down
echo "Fabric is down."
