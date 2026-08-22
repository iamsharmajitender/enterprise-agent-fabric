#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
RUN="$(cd "$HERE/.." && pwd)"
DELETE_SQL="$RUN/seed/delete-seed-data.sql"
CREATE_SQL="$RUN/seed/create-seed-data.sql"
LIFECYCLE_SQL="$RUN/seed/create-lifecycle-seed-data.sql"
COMPOSE=(docker compose -f "$RUN/compose/docker-compose.yml")

for sql in "$DELETE_SQL" "$CREATE_SQL" "$LIFECYCLE_SQL"; do
  if [[ ! -f "$sql" ]]; then
    echo "missing $sql" >&2
    exit 1
  fi
done

echo "Deleting then loading teaching seed plus lifecycle cuts in acr and adp..."
"${COMPOSE[@]}" exec -T postgres psql -U fabric -d afd -v ON_ERROR_STOP=1 -f - < "$DELETE_SQL"
"${COMPOSE[@]}" exec -T postgres psql -U fabric -d afd -v ON_ERROR_STOP=1 -f - < "$CREATE_SQL"
"${COMPOSE[@]}" exec -T postgres psql -U fabric -d afd -v ON_ERROR_STOP=1 -f - < "$LIFECYCLE_SQL"
echo "Teaching and lifecycle seed reloaded."
