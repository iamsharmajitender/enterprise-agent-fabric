#!/usr/bin/env bash
# Start a teaching-catalogue job with a fresh idempotency_key and payload ids.
# Usage:
#   ./run-job.sh --list
#   ./run-job.sh <route_id>
#   ./run-job.sh --mode 0|1|2|3
#   ./run-job.sh --all
#   ./run-job.sh --check-idempotency <route_id>
# Batch (--all / --mode) posts only; set WAIT=1 to poll each.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CATALOG="$HERE/jobs.json"
AFD="${AFD_URL:-http://localhost:3005}"
POLL_ATTEMPTS="${POLL_ATTEMPTS:-45}"
POLL_SLEEP="${POLL_SLEEP:-2}"
CREATE_ONLY="${CREATE_ONLY:-0}"

usage() {
  cat >&2 <<EOF
Usage: $0 [--list] [--all] [--mode N] [--check-idempotency] [route_id]
Each run mints a new idempotency_key, correlation_id (from Front Door), and payload ids.
EOF
  exit 2
}

need() {
  if ! command -v "$1" >/dev/null; then
    echo "missing $1" >&2
    exit 1
  fi
}

list_jobs() {
  python3 -c '
import json, sys
jobs = json.load(open(sys.argv[1]))["jobs"]
mode = sys.argv[2]
for job in jobs:
    if mode != "" and str(job["autonomy_mode"]) != mode:
        continue
    claims = ",".join(job.get("claims") or []) or "-"
    print("%s  %-18s  %-24s  %s" % (job["autonomy_mode"], job["label"], job["route_id"], claims))
' "$CATALOG" "${1:-}"
}

job_ids() {
  python3 -c '
import json, sys
jobs = json.load(open(sys.argv[1]))["jobs"]
mode = sys.argv[2]
for job in jobs:
    if mode != "" and str(job["autonomy_mode"]) != mode:
        continue
    print(job["route_id"])
' "$CATALOG" "${1:-}"
}

mint() {
  python3 -c '
import json, sys, uuid
catalog = json.load(open(sys.argv[1]))
route_id = sys.argv[2]
token = uuid.uuid4().hex[:12]
job = next((row for row in catalog["jobs"] if row["route_id"] == route_id), None)
if job is None:
    raise SystemExit("unknown route_id: " + route_id)

def expand(node):
    if isinstance(node, str):
        return node.replace("{id}", token)
    if isinstance(node, dict):
        return {key: expand(value) for key, value in node.items()}
    if isinstance(node, list):
        return [expand(value) for value in node]
    return node

body = {
    "route_id": route_id,
    "idempotency_key": f"job-{route_id}:{token}",
    "payload": expand(job.get("payload") or {}),
}
claims = {"sub": "jane", "emts": {claim: True for claim in job.get("claims") or []}}
json.dump(
    {
        "body": body,
        "claims": claims,
        "autonomy_mode": job["autonomy_mode"],
        "label": job["label"],
        "token": token,
    },
    sys.stdout,
)
' "$CATALOG" "$1"
}

post_job() {
  local payload_file="$1"
  local claims_json="$2"
  local tmp
  tmp="$(mktemp)"
  local code
  code="$(curl -s -o "$tmp" -w '%{http_code}' \
    -H 'Authorization: Bearer stub' \
    -H "X-Stub-Claims: ${claims_json}" \
    -H 'Content-Type: application/json' \
    -d @"$payload_file" \
    "${AFD}/v1/jobs")"
  if [[ "$code" != "202" ]]; then
    echo "POST /v1/jobs expected 202, got ${code}: $(cat "$tmp")" >&2
    rm -f "$tmp"
    return 1
  fi
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["correlation_id"])' "$tmp"
  rm -f "$tmp"
}

poll_job() {
  local correlation_id="$1"
  local claims_json="$2"
  local status_tmp
  status_tmp="$(mktemp)"
  local code
  for _ in $(seq 1 "$POLL_ATTEMPTS"); do
    code="$(curl -s -o "$status_tmp" -w '%{http_code}' \
      -H 'Authorization: Bearer stub' \
      -H "X-Stub-Claims: ${claims_json}" \
      "${AFD}/v1/jobs/${correlation_id}")"
    if [[ "$code" == "200" ]] && python3 -c '
import json, sys
body = json.load(open(sys.argv[1]))
status = body.get("status") or ""
sys.exit(0 if status in {"completed", "failed"} else 1)
' "$status_tmp"; then
      python3 -c '
import json, sys
body = json.load(open(sys.argv[1]))
status = body.get("status")
msg = (body.get("result") or {}).get("message") or body.get("message") or ""
print(f"status={status}")
if msg:
    print("result:", msg)
else:
    print("result:", json.dumps(body.get("result") or body))
' "$status_tmp"
      local st
      st="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("status") or "")' "$status_tmp")"
      rm -f "$status_tmp"
      if [[ "$st" != "completed" ]]; then
        echo "job did not complete: status=${st}" >&2
        return 1
      fi
      return 0
    fi
    sleep "$POLL_SLEEP"
  done
  echo "poll timeout for ${correlation_id}: $(cat "$status_tmp")" >&2
  rm -f "$status_tmp"
  return 1
}

run_one() {
  local route_id="$1"
  local check_idempotency="$2"
  local minted payload_tmp
  minted="$(mint "$route_id")"
  payload_tmp="$(mktemp)"
  python3 -c 'import json,sys; json.dump(json.loads(sys.argv[1])["body"], open(sys.argv[2],"w"))' "$minted" "$payload_tmp"
  local claims_json idempotency_key token autonomy label
  claims_json="$(python3 -c 'import json,sys; print(json.dumps(json.loads(sys.argv[1])["claims"], separators=(",",":")))' "$minted")"
  idempotency_key="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["body"]["idempotency_key"])' "$minted")"
  token="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["token"])' "$minted")"
  autonomy="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["autonomy_mode"])' "$minted")"
  label="$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["label"])' "$minted")"

  echo "route_id=${route_id}  autonomy=${autonomy} (${label})"
  echo "token=${token}"
  echo "idempotency_key=${idempotency_key}"
  python3 -c 'import json,sys; print("payload=", json.dumps(json.loads(sys.argv[1])["body"]["payload"]))' "$minted"

  echo "POST /v1/jobs (${route_id})..."
  local first second
  first="$(post_job "$payload_tmp" "$claims_json")"
  echo "correlation_id=${first}"

  if [[ "$check_idempotency" == "1" ]]; then
    echo "POST /v1/jobs again (same idempotency_key)..."
    second="$(post_job "$payload_tmp" "$claims_json")"
    if [[ "$first" != "$second" ]]; then
      echo "idempotency failed: ${first} vs ${second}" >&2
      rm -f "$payload_tmp"
      return 1
    fi
    echo "idempotency_ok=true"
  fi

  rm -f "$payload_tmp"
  if [[ "$CREATE_ONLY" != "1" ]]; then
    echo "GET /v1/jobs/${first} until completed or failed..."
    poll_job "$first" "$claims_json"
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
CHECK_IDEMPOTENCY=0
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
    --check-idempotency) CHECK_IDEMPOTENCY=1 ;;
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
  list_jobs "$MODE"
  exit 0
fi

if ! curl -sf "${AFD}/health" >/dev/null; then
  echo "Front Door is not up at ${AFD}/health" >&2
  exit 1
fi

if [[ -n "$ROUTE" ]]; then
  run_one "$ROUTE" "$CHECK_IDEMPOTENCY"
  exit 0
fi

if [[ "$ALL" == "1" || -n "$MODE" ]]; then
  if [[ "${WAIT:-0}" != "1" ]]; then
    CREATE_ONLY=1
  fi
  while IFS= read -r route_id; do
    echo "----"
    run_one "$route_id" 0
  done < <(job_ids "$MODE")
  exit 0
fi

usage
