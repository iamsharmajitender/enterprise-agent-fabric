#!/usr/bin/env bash
# Routing + pin-lint gate (Data Plane JUnit). No Compose. No LLM.
set -euo pipefail
cd "$(dirname "$0")"
exec mvn test -Dtest=RoutingEvalTest,JobsEntitleEvalTest,CataloguePinLintTest
