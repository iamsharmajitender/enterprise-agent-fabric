#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
CANNED='Fee of $42 is the monthly account charge.'
MESSAGE='Why was I charged $42?'
AFD="${AFD_URL:-http://localhost:3005}"
ACP="${ACP_URL:-http://localhost:3006}"
CLAIMS='{"sub":"jane","emts":{"accounts:read":true}}'
AUTH=(-H 'Authorization: Bearer stub' -H "X-Stub-Claims: ${CLAIMS}" -H 'Content-Type: application/json')
COMPOSE=(docker compose -f "$HERE/docker-compose.yml")

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

need() {
  if ! command -v "$1" >/dev/null; then
    echo "missing $1" >&2
    exit 1
  fi
}

need curl
need python3

if ! curl -sf "${AFD}/health" >/dev/null; then
  echo "Front Door is not up at ${AFD}/health" >&2
  exit 1
fi

echo "Reloading seed (idempotent)..."
"$HERE/seed-db.sh"

assert_fr5() {
  python3 -c '
import json, sys
forbidden = {"route_id", "run_id", "agent_client_id", "confidence", "router_layer"}
def walk(node):
    if isinstance(node, dict):
        keys = set(node)
        leak = keys & forbidden
        if leak:
            raise SystemExit("FR-5 leak " + ",".join(sorted(leak)))
        for value in node.values():
            walk(value)
    elif isinstance(node, list):
        for value in node:
            walk(value)
walk(json.load(open(sys.argv[1])))
' "$1"
}

echo "Control Plane GET eligible..."
code="$(curl -s -o "$tmp" -w '%{http_code}' "${ACP}/api/eligible?channel=web")"
if [[ "$code" != "200" ]]; then
  echo "Control Plane GET /api/eligible expected 200, got ${code}: $(cat "$tmp")" >&2
  exit 1
fi
python3 -c '
import json, sys
body = json.load(open(sys.argv[1]))
ids = [row.get("route_id") for row in body.get("routes") or []]
if "fee_explain" not in ids:
    raise SystemExit("eligible did not include fee_explain: " + ",".join(str(i) for i in ids))
' "$tmp"

echo "Control Plane GET catalogue fee_explain@2026.08.1..."
code="$(curl -s -o "$tmp" -w '%{http_code}' \
  "${ACP}/api/routes/fee_explain?route_version=2026.08.1")"
if [[ "$code" != "200" ]]; then
  echo "Control Plane GET /api/routes/fee_explain expected 200, got ${code}: $(cat "$tmp")" >&2
  exit 1
fi
python3 -c '
import json, sys
body = json.load(open(sys.argv[1]))
if body.get("route_id") != "fee_explain" or body.get("route_version") != "2026.08.1":
    raise SystemExit("unexpected catalogue row: " + json.dumps(body))
' "$tmp"

echo "GET /v1/assistant/hints..."
code="$(curl -s -o "$tmp" -w '%{http_code}' \
  -H 'Authorization: Bearer stub' -H "X-Stub-Claims: ${CLAIMS}" \
  "${AFD}/v1/assistant/hints")"
if [[ "$code" != "200" ]]; then
  echo "GET /v1/assistant/hints expected 200, got ${code}: $(cat "$tmp")" >&2
  exit 1
fi
assert_fr5 "$tmp"

echo "POST /v1/assistant/turns..."
code="$(curl -s -o "$tmp" -w '%{http_code}' "${AUTH[@]}" \
  -d "{\"message\":$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$MESSAGE")}" \
  "${AFD}/v1/assistant/turns")"
if [[ "$code" != "200" ]]; then
  echo "POST /v1/assistant/turns expected 200, got ${code}: $(cat "$tmp")" >&2
  exit 1
fi
assert_fr5 "$tmp"
python3 -c '
import json, sys
body = json.load(open(sys.argv[1]))
if body.get("status") != "accepted" or not str(body.get("session_id") or "").startswith("sess-"):
    raise SystemExit("turn was not accepted: " + json.dumps(body))
print(body["session_id"])
' "$tmp" > "${tmp}.sid"
session_id="$(cat "${tmp}.sid")"
rm -f "${tmp}.sid"
echo "session_id=${session_id}"

echo "GET /v1/assistant/sessions/${session_id}/events until completed..."
completed=0
for _ in $(seq 1 30); do
  code="$(curl -s -o "$tmp" -w '%{http_code}' \
    -H 'Authorization: Bearer stub' -H "X-Stub-Claims: ${CLAIMS}" \
    "${AFD}/v1/assistant/sessions/${session_id}/events")"
  if [[ "$code" == "200" ]] && python3 -c '
import json, sys
body = json.load(open(sys.argv[1]))
sys.exit(0 if body.get("status") == "completed" and body.get("message") == sys.argv[2] else 1)
' "$tmp" "$CANNED"; then
    assert_fr5 "$tmp"
    echo "chat completed: ${CANNED}"
    completed=1
    break
  fi
  sleep 0.3
done
if [[ "$completed" != "1" ]]; then
  echo "events did not complete with canned message: $(cat "$tmp")" >&2
  exit 1
fi

assert_row() {
  local db="$1"
  local sql="$2"
  local label="$3"
  local got
  got="$("${COMPOSE[@]}" exec -T postgres psql -U fabric -d "$db" -tAc "$sql" | tr -d '[:space:]')"
  if [[ "$got" != "1" ]]; then
    echo "missing ${label} in ${db} (got '${got}')" >&2
    exit 1
  fi
}

echo "Asserting four databases..."
assert_row afd \
  "SELECT 1 FROM frontdoor.freeze WHERE session_id = '${session_id}' AND route_id = 'fee_explain' AND correlation_id IS NOT NULL LIMIT 1" \
  "freeze row for ${session_id}"
assert_row adp \
  "SELECT 1 FROM dataplane.routes WHERE route_id = 'fee_explain' AND route_version = '2026.08.1' LIMIT 1" \
  "fee_explain catalogue row"
assert_row ar \
  "SELECT 1 FROM runtime.runs WHERE session_id = '${session_id}' AND jsonb_array_length(hydrated_tools) > 0 LIMIT 1" \
  "run pin with hydrated_tools"
assert_row acr \
  "SELECT 1 FROM registry.capabilities WHERE id = 'account_fee_lookup' AND version = '1.0.0' AND status = 'published' LIMIT 1" \
  "account_fee_lookup@1.0.0"
assert_row acr \
  "SELECT 1 FROM registry.manifests WHERE manifest_id = 'fee_explain' AND manifest_version = '2026.08.1' AND status = 'published' LIMIT 1" \
  "fee_explain@2026.08.1 manifest"

echo "demo-chat-turn ok"
