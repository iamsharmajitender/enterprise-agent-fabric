#!/usr/bin/env bash
# Routing + pin-lint gate (Data Plane JUnit). No Compose. No LLM.
set -euo pipefail
cd "$(dirname "$0")"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
In-process routing + pin-lint gate. Jane's turn does not run this.

  ./agent-data-plane/run-eval.sh

Runs:
  RoutingEvalTest          chat golden set
  JobsEntitleEvalTest      jobs entitle golden set
  CataloguePinLintTest     catalogue pin lint

Fixtures and playbook: src/test/resources/eval/README.md

Dummy --all is slice-2 Compose smoke (pin/hydrate), not this gate:
  WAIT=1 ./docs/run/dummy-request/run-job.sh --all
EOF
  exit 0
fi

exec mvn test -Dtest=RoutingEvalTest,JobsEntitleEvalTest,CataloguePinLintTest
