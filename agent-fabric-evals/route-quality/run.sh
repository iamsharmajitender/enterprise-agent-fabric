#!/usr/bin/env bash
# Route-quality gate (E14): tool-sequence suites under this tree.
# Does not run intent-router (routing / jobs-entitle / pin).
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO/agent-data-plane"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
In-process route-quality eval gate (tool / stage order). Jane's turn does not run this.

  ./agent-fabric-evals/route-quality/run.sh

Also:
  ./agent-data-plane/run-eval.sh --quality

Intent-router gate (separate):
  ./agent-fabric-evals/intent-router-evals/run.sh
  ./agent-data-plane/run-eval.sh

Fixtures: agent-fabric-evals/route-quality/routes/<suite_id>/<version>/
Task: docs/tasks/eval-todo.md (E14)
EOF
  exit 0
fi

exec mvn test -Dtest=RouteQualityEvalTest
