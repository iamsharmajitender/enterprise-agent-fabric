#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
RUN="$(cd "$HERE/.." && pwd)"
DELETE_SQL="$HERE/sql/delete-seed-data.sql"
COMPOSE=(docker compose -f "$RUN/docker-compose/docker-compose.yml")

[[ -f "$DELETE_SQL" ]] || { echo "missing $DELETE_SQL" >&2; exit 1; }

echo "Deleting all application data from afd, adp, ar_shared, ar_custom, acr, and audit..."
"${COMPOSE[@]}" exec -T postgres psql -U fabric -d afd -v ON_ERROR_STOP=1 -f - < "$DELETE_SQL"
echo "All application data deleted from every fabric database."
