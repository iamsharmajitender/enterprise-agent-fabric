#!/usr/bin/env bash
# Intent-router gate: routing + jobs-entitle + pin-lint. Fixtures in this tree (versioned).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO/agent-data-plane"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
In-process intent-router eval gate. Jane's turn does not run this.

  ./agent-fabric-evals/intent-router-evals/run.sh

Suites (see active.json in this folder):
  RoutingEvalTest          routing/<version>/cases/*.json
  JobsEntitleEvalTest      jobs-entitle/<version>/cases/*.json
  CataloguePinLintTest     pin/<version>/pin-suite.json (catalogue cut)

Fixtures: agent-fabric-evals/intent-router-evals/
Task list: docs/tasks/eval-todo.md

Dummy --all is pin/hydrate Compose smoke, not routing labels:
  WAIT=1 ./docs/run/dummy-request/run-job.sh --all
EOF
  exit 0
fi

exec mvn test -Dtest=RoutingEvalTest,JobsEntitleEvalTest,CataloguePinLintTest
