#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
exec "$(cd "$HERE/../.." && pwd)/add-seed-data.sh" "$(basename "$HERE")"
