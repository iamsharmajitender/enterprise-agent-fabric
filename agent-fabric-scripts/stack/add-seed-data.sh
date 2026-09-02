#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
RUN="$(cd "$HERE/.." && pwd)"
ROUTE_ROOT="$HERE/route"
DELETE_SQL="$HERE/sql/delete-seed-data.sql"
COMPOSE=(docker compose -f "$RUN/docker-compose/docker-compose.yml")
ROUTE_SQL_ORDER=(corpora capability manifest prompt route retrieval memory workflow intent)

apply_sql() {
  echo "Loading $(basename "$1")..."
  "${COMPOSE[@]}" exec -T postgres psql -U fabric -d afd -v ON_ERROR_STOP=1 -f - < "$1"
}

apply_pack() {
  local dir="$1" name sql found=0
  [[ -d "$dir" ]] || { echo "missing route pack: $dir" >&2; return 1; }
  for name in "${ROUTE_SQL_ORDER[@]}"; do
    sql="$dir/$name.sql"
    [[ -f "$sql" ]] || continue
    found=1
    apply_sql "$sql"
  done
  [[ "$found" -eq 1 ]] || { echo "no .sql files in $dir" >&2; return 1; }
}

wipe_all() {
  [[ -f "$DELETE_SQL" ]] || { echo "missing $DELETE_SQL" >&2; exit 1; }
  echo "Deleting all application data from afd, adp, ar, acr, and audit..."
  apply_sql "$DELETE_SQL"
}

CLEAN=0
if [[ "${1:-}" == "--clean" ]]; then
  CLEAN=1
  shift
fi

route_id="${1:-}"

if [[ -n "$route_id" ]]; then
  if [[ "$CLEAN" -eq 1 ]]; then
    wipe_all
  fi
  echo "Loading route pack $route_id..."
  apply_pack "$ROUTE_ROOT/$route_id"
  echo "Route pack $route_id loaded."
  exit 0
fi

packs=()
shopt -s nullglob
for dir in "$ROUTE_ROOT"/*/; do
  files=("$dir"*.sql)
  [[ ${#files[@]} -gt 0 ]] && packs+=("${dir%/}")
done
shopt -u nullglob

if [[ ${#packs[@]} -eq 0 ]]; then
  echo "no route packs under $ROUTE_ROOT (need at least one .sql file per route)" >&2
  exit 1
fi

echo "Deleting then adding all routes and catalogue seed data..."
wipe_all

for dir in "${packs[@]}"; do
  echo "---- $(basename "$dir") ----"
  apply_pack "$dir"
done
echo "All routes and catalogue seed data loaded."
