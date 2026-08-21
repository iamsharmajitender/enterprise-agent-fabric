#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
COMPOSE=(docker compose -f "$HERE/docker-compose.yml")

echo "Starting fabric in the background..."
"${COMPOSE[@]}" up --build -d
"${COMPOSE[@]}" ps
echo "Fabric is up. Front Door http://localhost:3005  Control Plane http://localhost:3006"
