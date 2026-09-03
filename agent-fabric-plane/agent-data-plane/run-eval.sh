#!/usr/bin/env bash
# Eval wrappers. Default = intent-router only. --quality = E14. --all = both.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"

usage() {
  cat <<'EOF'
Eval gates (in-process ADP JUnit). Jane's turn does not run these.

  ./agent-fabric-plane/agent-data-plane/run-eval.sh              intent-router
  ./agent-fabric-plane/agent-data-plane/run-eval.sh --quality   route-quality
  ./agent-fabric-plane/agent-data-plane/run-eval.sh --all       both

Direct:
  ./agent-fabric-evals/intent-router-evals/run.sh
  ./agent-fabric-evals/route-quality/run.sh
EOF
}

case "${1:-}" in
  -h|--help)
    usage
    exit 0
    ;;
  --quality)
    exec "$REPO/agent-fabric-evals/route-quality/run.sh"
    ;;
  --all)
    "$REPO/agent-fabric-evals/intent-router-evals/run.sh"
    exec "$REPO/agent-fabric-evals/route-quality/run.sh"
    ;;
  "")
    exec "$REPO/agent-fabric-evals/intent-router-evals/run.sh"
    ;;
  *)
    echo "unknown option: $1" >&2
    usage >&2
    exit 1
    ;;
esac
