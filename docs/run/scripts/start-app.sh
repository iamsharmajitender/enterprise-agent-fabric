#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
RUN="$(cd "$HERE/.." && pwd)"
COMPOSE=(docker compose -f "$RUN/compose/docker-compose.yml")

# An LGTM started outside this Compose project keeps the container name and blocks `up`.
if docker inspect agent-fabric-otel-lgtm-1 >/dev/null 2>&1; then
  project="$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' agent-fabric-otel-lgtm-1 2>/dev/null || true)"
  if [[ -z "${project}" ]]; then
    echo "Removing leftover unlabeled agent-fabric-otel-lgtm-1..."
    docker rm -f agent-fabric-otel-lgtm-1 >/dev/null
  fi
fi

echo "Starting fabric in the background..."
"${COMPOSE[@]}" up --build -d
"${COMPOSE[@]}" ps

flyway_checksum_failed() {
  local svc
  for svc in agent-data-plane agent-capability-registry agent-front-door; do
    if "${COMPOSE[@]}" logs --no-color --tail 200 "$svc" 2>/dev/null \
      | grep -q "Migration checksum mismatch"; then
      echo "$svc Flyway checksum mismatch (a migration already applied was edited)." >&2
      echo "Control Plane will show Catalogue read failed (502) until Postgres is wiped." >&2
      echo "Recover with:" >&2
      echo "  docker compose -f docs/run/compose/docker-compose.yml down -v" >&2
      echo "  ./docs/run/scripts/start-app.sh" >&2
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
      return 1
    fi
    sleep 2
  done
  echo "$label did not become healthy on $url" >&2
  return 1
}

wait_healthy http://127.0.0.1:3007/health "Data Plane"
wait_healthy http://127.0.0.1:3009/health "Capability Registry"
echo "Fabric is up. Front Door http://localhost:3005  Control Plane http://localhost:3006"
