#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REMOVE_SQL="$HERE/remove.sql"
RUN="$(cd "$HERE/../../.." && pwd)"
COMPOSE=(docker compose -f "$RUN/docker-compose/docker-compose.yml")

[[ -f "$REMOVE_SQL" ]] || { echo "missing $REMOVE_SQL" >&2; exit 1; }

echo "Removing route pack $(basename "$HERE")..."
"${COMPOSE[@]}" exec -T postgres psql -U fabric -d afd -v ON_ERROR_STOP=1 -f - < "$REMOVE_SQL"
echo "Route pack $(basename "$HERE") removed."
