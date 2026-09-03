#!/usr/bin/env bash
# Route-quality gate: tool-sequence suites under this tree.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO/agent-fabric-plane/agent-data-plane"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
In-process route-quality eval gate (tool / stage order).

  ./agent-fabric-evals/route-quality/run.sh
  ./agent-fabric-plane/agent-data-plane/run-eval.sh --quality
EOF
  exit 0
fi

exec mvn test -Dtest=RouteQualityEvalTest
