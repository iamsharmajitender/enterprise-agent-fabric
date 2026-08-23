#!/usr/bin/env bash
# Start a catalogue chat turn. Keyword classify, or a hint chip when keywords collide.
# Usage:
#   ./run-chat.sh --list
#   ./run-chat.sh <route_id>
#   ./run-chat.sh --mode 0|1|2|3
#   ./run-chat.sh --all
# Batch (--all / --mode) posts only; set WAIT=1 to poll each.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CATALOG="$HERE/chat/chats.json"
AFD="${AFD_URL:-http://localhost:3005}"
ACP="${ACP_URL:-http://localhost:3006}"
POLL_ATTEMPTS="${POLL_ATTEMPTS:-45}"
POLL_SLEEP="${POLL_SLEEP:-2}"
CREATE_ONLY="${CREATE_ONLY:-0}"
COMPOSE=(docker compose -f "$HERE/../compose/docker-compose.yml")

usage() {
  cat >&2 <<EOF
Usage: $0 [--list] [--all] [--mode N] [route_id]
Each run mints a new session_id and payload ids.

EOF
  exit 2
}

need() {
  if ! command -v "$1" >/dev/null; then
    echo "missing $1" >&2
    exit 1
  fi
}

list_chats() {
  python3 -c '
import json, sys
chats = json.load(open(sys.argv[1]))["chats"]
mode = sys.argv[2]
for chat in chats:
    if mode != "" and str(chat["autonomy_mode"]) != mode:
        continue
    claims = ",".join(chat.get("claims") or []) or "-"
    print("%s  %-18s  %-24s  %s" % (chat["autonomy_mode"], chat["label"], chat["route_id"], claims))
' "$CATALOG" "${1:-}"
}

chat_ids() {
  python3 -c '
import json, sys
chats = json.load(open(sys.argv[1]))["chats"]
mode = sys.argv[2]
for chat in chats:
    if mode != "" and str(chat["autonomy_mode"]) != mode:
        continue
    print(chat["route_id"])
' "$CATALOG" "${1:-}"
}

mint() {
  python3 -c '
import json, sys, uuid
catalog = json.load(open(sys.argv[1]))
route_id = sys.argv[2]
token = uuid.uuid4().hex[:12]
chat = next((row for row in catalog["chats"] if row["route_id"] == route_id), None)
if chat is None:
    raise SystemExit("unknown route_id: " + route_id)

def expand(node):
    if isinstance(node, str):
        return node.replace("{id}", token)
    if isinstance(node, dict):
        return {key: expand(value) for key, value in node.items()}
    if isinstance(node, list):
        return [expand(value) for value in node]
    return node

claims = {"sub": "jane", "emts": {claim: True for claim in chat.get("claims") or []}}
json.dump(
    {
        "route_id": route_id,
        "message": expand(chat.get("message") or ""),
        "expected_message": chat.get("expected_message"),
        "hint_contains": chat.get("hint_contains"),
        "prove": chat.get("prove"),
        "claims": claims,
        "autonomy_mode": chat["autonomy_mode"],
        "label": chat["label"],
        "token": token,
    },
    sys.stdout,
)
' "$CATALOG" "$1"
}

assert_fr5() {
  python3 -c '
import json, sys
forbidden = {"route_id", "run_id", "agent_client_id", "confidence", "router_layer"}
def walk(node):
    if isinstance(node, dict):
        leak = set(node) & forbidden
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

prove_control_plane() {
  local route_id="$1"
  local route_version="$2"
  local tmp
  tmp="$(mktemp)"
  echo "Control Plane GET eligible..."
  local code
  code="$(curl -s -o "$tmp" -w '%{http_code}' "${ACP}/api/eligible?channel=web")"
  if [[ "$code" != "200" ]]; then
    echo "Control Plane GET /api/eligible expected 200, got ${code}: $(cat "$tmp")" >&2
    rm -f "$tmp"
    return 1
  fi
  python3 -c '
import json, sys
body = json.load(open(sys.argv[1]))
ids = [row.get("route_id") for row in body.get("routes") or []]
if sys.argv[2] not in ids:
    raise SystemExit("eligible did not include " + sys.argv[2] + ": " + ",".join(str(i) for i in ids))
' "$tmp" "$route_id"

  echo "Control Plane GET catalogue ${route_id}@${route_version}..."
  code="$(curl -s -o "$tmp" -w '%{http_code}' \
    "${ACP}/api/routes/${route_id}?route_version=${route_version}")"
  if [[ "$code" != "200" ]]; then
    echo "Control Plane GET /api/routes/${route_id} expected 200, got ${code}: $(cat "$tmp")" >&2
    rm -f "$tmp"
    return 1
  fi
  python3 -c '
import json, sys
body = json.load(open(sys.argv[1]))
if body.get("route_id") != sys.argv[2] or body.get("route_version") != sys.argv[3]:
    raise SystemExit("unexpected catalogue row: " + json.dumps(body))
' "$tmp" "$route_id" "$route_version"
  rm -f "$tmp"
}

prove_databases() {
  local session_id="$1"
  local route_id="$2"
  local prove_json="$3"
  local route_version capability_id capability_version
  route_version="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["route_version"])' "$prove_json")"
  capability_id="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["capability_id"])' "$prove_json")"
  capability_version="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["capability_version"])' "$prove_json")"

  assert_row() {
    local db="$1"
    local sql="$2"
    local label="$3"
    local got
    got="$("${COMPOSE[@]}" exec -T postgres psql -U fabric -d "$db" -tAc "$sql" | tr -d '[:space:]')"
    if [[ "$got" != "1" ]]; then
      echo "missing ${label} in ${db} (got '${got}')" >&2
      return 1
    fi
  }

  echo "Asserting four databases..."
  assert_row afd \
    "SELECT 1 FROM frontdoor.freeze WHERE session_id = '${session_id}' AND route_id = '${route_id}' AND correlation_id IS NOT NULL LIMIT 1" \
    "freeze row for ${session_id}"
  assert_row adp \
    "SELECT 1 FROM dataplane.routes WHERE route_id = '${route_id}' AND route_version = '${route_version}' LIMIT 1" \
    "${route_id} catalogue row"
  assert_row ar \
    "SELECT 1 FROM runtime.runs WHERE session_id = '${session_id}' AND jsonb_array_length(hydrated_tools) > 0 LIMIT 1" \
    "run pin with hydrated_tools"
  assert_row acr \
    "SELECT 1 FROM registry.capabilities WHERE id = '${capability_id}' AND version = '${capability_version}' AND status = 'published' LIMIT 1" \
    "${capability_id}@${capability_version}"
  assert_row acr \
    "SELECT 1 FROM registry.manifests WHERE manifest_id = '${route_id}' AND manifest_version = '${route_version}' AND status = 'published' LIMIT 1" \
    "${route_id}@${route_version} manifest"
}

pick_hint() {
  local hints_file="$1"
  local needle="$2"
  python3 -c '
import json, sys
body = json.load(open(sys.argv[1]))
needle = sys.argv[2].lower()
for hint in body.get("hints") or []:
    label = str(hint.get("label") or "")
    if needle in label.lower():
        print(hint["hint_id"])
        raise SystemExit(0)
raise SystemExit("no hint matching %r in %s" % (sys.argv[2], json.dumps(body)))
' "$hints_file" "$needle"
}

post_turn() {
  local claims_json="$1"
  local body_file="$2"
  local tmp
  tmp="$(mktemp)"
  local code
  code="$(curl -s -o "$tmp" -w '%{http_code}' \
    -H 'Authorization: Bearer stub' \
    -H "X-Stub-Claims: ${claims_json}" \
    -H 'Content-Type: application/json' \
    -d @"$body_file" \
    "${AFD}/v1/assistant/turns")"
  if [[ "$code" != "200" ]]; then
    echo "POST /v1/assistant/turns expected 200, got ${code}: $(cat "$tmp")" >&2
    rm -f "$tmp"
    return 1
  fi
  assert_fr5 "$tmp"
  python3 -c '
import json, sys
body = json.load(open(sys.argv[1]))
status = body.get("status")
if status != "accepted" or not str(body.get("session_id") or "").startswith("sess-"):
    raise SystemExit("turn was not accepted: " + json.dumps(body))
print(body["session_id"])
' "$tmp"
  rm -f "$tmp"
}

poll_events() {
  local session_id="$1"
  local claims_json="$2"
  local expected="${3:-}"
  local status_tmp
  status_tmp="$(mktemp)"
  local code
  for _ in $(seq 1 "$POLL_ATTEMPTS"); do
    code="$(curl -s -o "$status_tmp" -w '%{http_code}' \
      -H 'Authorization: Bearer stub' \
      -H "X-Stub-Claims: ${claims_json}" \
      "${AFD}/v1/assistant/sessions/${session_id}/events")"
    if [[ "$code" == "200" ]] && python3 -c '
import json, sys
body = json.load(open(sys.argv[1]))
status = body.get("status") or ""
sys.exit(0 if status in {"completed", "failed"} else 1)
' "$status_tmp"; then
      assert_fr5 "$status_tmp"
      python3 -c '
import json, sys
body = json.load(open(sys.argv[1]))
status = body.get("status")
msg = body.get("message") or ""
print(f"status={status}")
if msg:
    print("result:", msg)
else:
    print("result:", json.dumps(body))
' "$status_tmp"
      local st msg
      st="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("status") or "")' "$status_tmp")"
      msg="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("message") or "")' "$status_tmp")"
      rm -f "$status_tmp"
      if [[ "$st" != "completed" ]]; then
        echo "chat did not complete: status=${st}" >&2
        return 1
      fi
      if [[ -n "$expected" && "$msg" != "$expected" ]]; then
        echo "chat message mismatch: expected ${expected@Q} got ${msg@Q}" >&2
        return 1
      fi
      return 0
    fi
    sleep "$POLL_SLEEP"
  done
  echo "poll timeout for ${session_id}: $(cat "$status_tmp")" >&2
  rm -f "$status_tmp"
  return 1
}

run_one() {
  local route_id="$1"
  local minted
  minted="$(mint "$route_id")"
  local claims_json message expected hint_contains prove token autonomy label
  claims_json="$(python3 -c 'import json,sys; print(json.dumps(json.loads(sys.argv[1])["claims"], separators=(",",":")))' "$minted")"
  message="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["message"])' "$minted")"
  expected="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("expected_message") or "")' "$minted")"
  hint_contains="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1]).get("hint_contains") or "")' "$minted")"
  prove="$(python3 -c 'import json,sys; p=json.loads(sys.argv[1]).get("prove"); print("" if p is None else json.dumps(p))' "$minted")"
  token="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["token"])' "$minted")"
  autonomy="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["autonomy_mode"])' "$minted")"
  label="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["label"])' "$minted")"

  echo "route_id=${route_id}  autonomy=${autonomy} (${label})"
  echo "token=${token}"
  echo "message=${message}"

  if [[ -n "$prove" ]]; then
    local route_version
    route_version="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["route_version"])' "$prove")"
    prove_control_plane "$route_id" "$route_version"
  fi

  local session_id="" hint_id=""
  local hints_tmp
  hints_tmp="$(mktemp)"
  if [[ -n "$hint_contains" || -n "$prove" ]]; then
    echo "GET /v1/assistant/hints..."
    local code
    code="$(curl -s -o "$hints_tmp" -w '%{http_code}' \
      -H 'Authorization: Bearer stub' -H "X-Stub-Claims: ${claims_json}" \
      "${AFD}/v1/assistant/hints")"
    if [[ "$code" != "200" ]]; then
      echo "GET /v1/assistant/hints expected 200, got ${code}: $(cat "$hints_tmp")" >&2
      rm -f "$hints_tmp"
      return 1
    fi
    assert_fr5 "$hints_tmp"
    if [[ -n "$hint_contains" ]]; then
      hint_id="$(pick_hint "$hints_tmp" "$hint_contains")"
      session_id="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["session_id"])' "$hints_tmp")"
    fi
  fi
  rm -f "$hints_tmp"

  local body_tmp
  body_tmp="$(mktemp)"
  python3 -c '
import json, sys
body = {"message": sys.argv[1]}
if sys.argv[2]:
    body["session_id"] = sys.argv[2]
if sys.argv[3]:
    body["hint_id"] = sys.argv[3]
json.dump(body, open(sys.argv[4], "w"))
' "$message" "$session_id" "$hint_id" "$body_tmp"

  echo "POST /v1/assistant/turns (${route_id})..."
  session_id="$(post_turn "$claims_json" "$body_tmp")"
  rm -f "$body_tmp"
  echo "session_id=${session_id}"

  if [[ "$CREATE_ONLY" == "1" ]]; then
    return 0
  fi

  echo "GET /v1/assistant/sessions/${session_id}/events until completed or failed..."
  poll_events "$session_id" "$claims_json" "$expected"

  if [[ -n "$prove" ]]; then
    prove_databases "$session_id" "$route_id" "$prove"
  fi
}

need curl
need python3

if [[ ! -f "$CATALOG" ]]; then
  echo "missing $CATALOG" >&2
  exit 1
fi

LIST=0
ALL=0
MODE=""
ROUTE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --list|-l) LIST=1 ;;
    --all) ALL=1 ;;
    --mode)
      shift
      MODE="${1:-}"
      [[ "$MODE" =~ ^[0-3]$ ]] || usage
      ;;
    --create-only) CREATE_ONLY=1 ;;
    -h|--help) usage ;;
    --*) usage ;;
    *)
      if [[ -n "$ROUTE" ]]; then
        usage
      fi
      ROUTE="$1"
      ;;
  esac
  shift
done

if [[ "$LIST" == "1" || ( -z "$ROUTE" && "$ALL" != "1" && -z "$MODE" ) ]]; then
  list_chats "$MODE"
  exit 0
fi

if ! curl -sf "${AFD}/health" >/dev/null; then
  echo "Front Door is not up at ${AFD}/health" >&2
  exit 1
fi

if [[ -n "$ROUTE" ]]; then
  run_one "$ROUTE"
  exit 0
fi

if [[ "$ALL" == "1" || -n "$MODE" ]]; then
  if [[ "${WAIT:-0}" != "1" ]]; then
    CREATE_ONLY=1
  fi
  while IFS= read -r route_id; do
    echo "----"
    run_one "$route_id"
  done < <(chat_ids "$MODE")
  exit 0
fi

usage
