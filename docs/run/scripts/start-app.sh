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
echo "Fabric is up. Front Door http://localhost:3005  Control Plane http://localhost:3006"
