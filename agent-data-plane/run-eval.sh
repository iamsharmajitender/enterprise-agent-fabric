#!/usr/bin/env bash
# Eval wrappers. Default = intent-router only (E1–E13). --quality = E14. --all = both.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"

usage() {
  cat <<'EOF'
Eval gates (in-process ADP JUnit). Jane's turn does not run these.

  ./agent-data-plane/run-eval.sh              intent-router (routing / jobs-entitle / pin)
  ./agent-data-plane/run-eval.sh --quality   route-quality (tool-sequence / E14)
  ./agent-data-plane/run-eval.sh --all       both, sequentially

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
