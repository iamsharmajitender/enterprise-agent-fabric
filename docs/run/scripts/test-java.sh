#!/usr/bin/env bash
# Run Java unit tests for Fabric services (Compose image builds skip tests).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
fail=0
for mod in agent-capability-registry agent-data-plane agent-front-door agent-audit-data-plane; do
  echo "==> mvn test $mod"
  if ! (cd "$ROOT/$mod" && mvn -q -B test); then
    echo "FAILED: $mod" >&2
    fail=1
  fi
done
exit "$fail"
