#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
RUN="$(cd "$HERE/.." && pwd)"
COMPOSE=(docker compose -f "$RUN/compose/docker-compose.yml")

echo "Stopping fabric (volumes kept)..."
"${COMPOSE[@]}" down
echo "Fabric is down."
