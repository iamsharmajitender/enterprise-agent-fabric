#!/usr/bin/env bash
# Intent-router gate: routing + jobs-entitle + pin-lint.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO/agent-fabric-plane/agent-data-plane"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
In-process intent-router eval gate. Jane's turn does not run this.

  ./agent-fabric-evals/intent-router-evals/run.sh

Dummy --all is pin/hydrate Compose smoke, not routing labels:
  WAIT=1 ./agent-fabric-scripts/route-runs/run-job.sh --all
EOF
  exit 0
fi

exec mvn test -Dtest=RoutingEvalTest,JobsEntitleEvalTest,CataloguePinLintTest
