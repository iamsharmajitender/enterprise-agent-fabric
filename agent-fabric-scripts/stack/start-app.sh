#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
RUN="$(cd "$HERE/.." && pwd)"
ROOT="$(cd "$RUN/.." && pwd)"
COMPOSE=(docker compose -f "$RUN/docker-compose/docker-compose.yml")
PROJECT_NAME="$(awk '/^name:/{print $2; exit}' "$RUN/docker-compose/docker-compose.yml" | tr '[:upper:]' '[:lower:]')"
POSTGRES_VOLUME="${PROJECT_NAME}_postgres_data"
STAMP_FILE="$RUN/docker-compose/.flyway-content.sha"
# Local seed DBs: editing an already-applied V1 is normal. Auto-wipe Postgres when that happens.
AUTO_WIPE="${FABRIC_AUTO_WIPE_ON_FLYWAY_MISMATCH:-1}"

# An LGTM started outside this Compose project keeps the container name and blocks `up`.
# Also clear pre-rename leftovers (project was agent-fabric; Compose lowercases project names).
for leftover in "${PROJECT_NAME}-otel-lgtm-1" agent-fabric-otel-lgtm-1; do
  if docker inspect "$leftover" >/dev/null 2>&1; then
    project="$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "$leftover" 2>/dev/null || true)"
    if [[ -z "${project}" ]]; then
      echo "Removing leftover unlabeled ${leftover}..."
      docker rm -f "$leftover" >/dev/null
    fi
  fi
done

flyway_content_sha() {
  local dirs=(
    "$ROOT/agent-fabric-front-door/src/main/resources/db/migration"
    "$ROOT/agent-fabric-capability-registry/src/main/resources/db/migration"
    "$ROOT/agent-fabric-plane/agent-data-plane/src/main/resources/db/migration"
    "$ROOT/agent-front-door/src/main/resources/db/migration"
    "$ROOT/agent-capability-registry/src/main/resources/db/migration"
    "$ROOT/agent-data-plane/src/main/resources/db/migration"
  )
  local existing=() d
  for d in "${dirs[@]}"; do
    [[ -d "$d" ]] || continue
    existing+=("$d")
  done
  if [[ ${#existing[@]} -eq 0 ]]; then
    echo "start-app.sh: no Flyway migration dirs under $ROOT" >&2
    return 1
  fi
  # Hash file contents (paths excluded) so renames alone do not force a wipe.
  find "${existing[@]}" -type f -name '*.sql' -print0 2>/dev/null \
    | LC_ALL=C sort -z \
    | xargs -0 cat \
    | shasum -a 256 \
    | awk '{print $1}'
}

reset_postgres_volume() {
  echo "Resetting Postgres volume (${POSTGRES_VOLUME}) so Flyway can re-apply migrations..."
  echo "(LGTM volume kept.)"
  "${COMPOSE[@]}" down --remove-orphans
  docker volume rm "$POSTGRES_VOLUME" >/dev/null 2>&1 || true
}

save_flyway_stamp() {
  mkdir -p "$(dirname "$STAMP_FILE")"
  flyway_content_sha >"$STAMP_FILE"
}

maybe_reset_postgres_for_flyway_edits() {
  [[ "$AUTO_WIPE" == "1" ]] || return 0
  local now old
  now="$(flyway_content_sha)"
  if [[ ! -f "$STAMP_FILE" ]]; then
    return 0
  fi
  old="$(tr -d '[:space:]' <"$STAMP_FILE")"
  if [[ "$old" == "$now" ]]; then
    return 0
  fi
  if ! docker volume inspect "$POSTGRES_VOLUME" >/dev/null 2>&1; then
    return 0
  fi
  echo "Flyway SQL changed since last healthy start — wiping Postgres so edited migrations re-apply."
  reset_postgres_volume
}

bring_up() {
  echo "Starting fabric in the background..."
  # --remove-orphans: renamed services (e.g. agent-fabric-mocks → agent-mocks) otherwise keep port binds.
  "${COMPOSE[@]}" up --build -d --remove-orphans
  ensure_postgres_databases
  "${COMPOSE[@]}" ps
}

# init-postgres.sql runs only on an empty volume. When we add a DB later (e.g. audit),
# existing volumes never pick it up — create missing DBs idempotently after Postgres is up.
ensure_postgres_databases() {
  local db
  echo "Ensuring Postgres app databases exist (adp, ar_shared, ar_custom, acr, audit)…"
  for _ in $(seq 1 30); do
    if "${COMPOSE[@]}" exec -T postgres pg_isready -U fabric -d afd >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  for db in adp ar_shared ar_custom acr audit; do
    "${COMPOSE[@]}" exec -T postgres \
      psql -U fabric -d afd -v ON_ERROR_STOP=1 \
      -c "SELECT 'ok' FROM pg_database WHERE datname = '${db}'" 2>/dev/null \
      | grep -q ok \
      || "${COMPOSE[@]}" exec -T postgres \
        psql -U fabric -d afd -v ON_ERROR_STOP=1 \
        -c "CREATE DATABASE ${db};"
  done
  # AADP may have crash-looped before audit existed; restart once DBs are ready.
  "${COMPOSE[@]}" up -d --no-deps agent-audit-data-plane >/dev/null 2>&1 || true
}

flyway_checksum_failed() {
  local svc
  for svc in agent-data-plane agent-capability-registry agent-front-door agent-audit-data-plane; do
    if "${COMPOSE[@]}" logs --no-color --tail 400 "$svc" 2>/dev/null \
      | grep -Eq "Migration checksum mismatch|FlywayValidateException|database \"audit\" does not exist"; then
      return 0
    fi
  done
  return 1
}

wait_healthy() {
  local url="$1"
  local label="$2"
  local i
  for i in $(seq 1 45); do
    if curl -sf --max-time 2 "$url" >/dev/null; then
      return 0
    fi
    if flyway_checksum_failed; then
      return 2
    fi
    sleep 2
  done
  echo "$label did not become healthy on $url" >&2
  return 1
}

wait_stack_healthy() {
  wait_healthy http://127.0.0.1:3007/health "Data Plane" || return $?
  wait_healthy http://127.0.0.1:3009/health "Capability Registry" || return $?
  wait_healthy http://127.0.0.1:3012/health "Audit Data Plane" || return $?
  return 0
}

print_manual_flyway_recovery() {
  echo "Flyway checksum mismatch (a migration already applied was edited)." >&2
  echo "Control Plane will show Catalogue read failed (502) until Postgres is wiped." >&2
  echo "Recover with:" >&2
  echo "  docker compose -f agent-fabric-scripts/docker-compose/docker-compose.yml down" >&2
  echo "  docker volume rm ${POSTGRES_VOLUME}" >&2
  echo "  ./agent-fabric-scripts/stack/start-app.sh" >&2
  echo "Or set FABRIC_AUTO_WIPE_ON_FLYWAY_MISMATCH=1 (default) and re-run start-app.sh." >&2
}

maybe_reset_postgres_for_flyway_edits
bring_up

rc=0
wait_stack_healthy || rc=$?

if [[ "$rc" -eq 2 ]]; then
  if [[ "$AUTO_WIPE" == "1" ]]; then
    echo "Flyway checksum mismatch detected — auto-recovering once."
    reset_postgres_volume
    bring_up
    rc=0
    wait_stack_healthy || rc=$?
    if [[ "$rc" -eq 2 ]]; then
      echo "Flyway still failing after Postgres reset." >&2
      print_manual_flyway_recovery
      exit 1
    fi
  else
    print_manual_flyway_recovery
    exit 1
  fi
fi

if [[ "$rc" -ne 0 ]]; then
  exit "$rc"
fi

save_flyway_stamp
CONTROL_PLANE_URL="http://localhost:3006"
echo "Fabric is up. Front Door http://localhost:3005  Chat/Jobs scratchpad http://localhost:3014  Control Plane ${CONTROL_PLANE_URL}"
echo "Audit Control Plane http://localhost:3013  (data plane :3012). Seed routes: ./agent-fabric-scripts/stack/add-seed-data.sh"
echo "Java unit tests: ./agent-fabric-scripts/stack/test-java.sh"
if command -v open >/dev/null 2>&1; then
  open "${CONTROL_PLANE_URL}"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "${CONTROL_PLANE_URL}" >/dev/null 2>&1 || true
fi
