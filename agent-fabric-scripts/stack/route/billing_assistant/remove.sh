#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
RUN="$(cd "$HERE/../../.." && pwd)"
COMPOSE=(docker compose -f "$RUN/docker-compose/docker-compose.yml")

apply_sql() {
  echo "Loading $(basename "$1")..."
  "${COMPOSE[@]}" exec -T postgres psql -U fabric -d afd -v ON_ERROR_STOP=1 -f - < "$1"
}

apply_sql "$HERE/remove.sql"
echo "Route pack billing_assistant removed."
