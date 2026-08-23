#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
RUN="$(cd "$HERE/.." && pwd)"
DELETE_SQL="$HERE/delete-seed-data.sql"
CREATE_SQL="$HERE/create-seed-data.sql"
COMPOSE=(docker compose -f "$RUN/compose/docker-compose.yml")

for sql in "$DELETE_SQL" "$CREATE_SQL"; do
  if [[ ! -f "$sql" ]]; then
    echo "missing $sql" >&2
    exit 1
  fi
done

echo "Deleting then loading catalogue seed in acr and adp..."
"${COMPOSE[@]}" exec -T postgres psql -U fabric -d afd -v ON_ERROR_STOP=1 -f - < "$DELETE_SQL"
"${COMPOSE[@]}" exec -T postgres psql -U fabric -d afd -v ON_ERROR_STOP=1 -f - < "$CREATE_SQL"
echo "Catalogue seed reloaded."
