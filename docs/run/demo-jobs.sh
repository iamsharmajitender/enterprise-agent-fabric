#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
BODY="$ROOT/docs/contracts/jobs-start.json"
CANNED='Fee of $42 is the monthly account charge.'
AFD="${AFD_URL:-http://localhost:3005}"
CLAIMS='{"sub":"jane","emts":{"accounts:read":true}}'
AUTH=(-H 'Authorization: Bearer stub' -H "X-Stub-Claims: ${CLAIMS}" -H 'Content-Type: application/json')

if [[ ! -f "$BODY" ]]; then
  echo "missing $BODY" >&2
  exit 1
fi

if ! curl -sf "${AFD}/health" >/dev/null; then
  echo "Front Door is not up at ${AFD}/health" >&2
  exit 1
fi

post_job() {
  local tmp
  tmp="$(mktemp)"
  local code
  code="$(curl -s -o "$tmp" -w '%{http_code}' "${AUTH[@]}" -d @"$BODY" "${AFD}/v1/jobs")"
  if [[ "$code" != "202" ]]; then
    echo "POST /v1/jobs expected 202, got ${code}: $(cat "$tmp")" >&2
    rm -f "$tmp"
    exit 1
  fi
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["correlation_id"])' "$tmp"
  rm -f "$tmp"
}

echo "POST /v1/jobs (fee_explain)..."
first="$(post_job)"
echo "correlation_id=${first}"

echo "POST /v1/jobs again (same idempotency_key)..."
second="$(post_job)"
if [[ "$first" != "$second" ]]; then
  echo "idempotency failed: ${first} vs ${second}" >&2
  exit 1
fi

status_tmp="$(mktemp)"
trap 'rm -f "$status_tmp"' EXIT
echo "GET /v1/jobs/${first} until completed..."
for _ in $(seq 1 30); do
  code="$(curl -s -o "$status_tmp" -w '%{http_code}' \
    -H 'Authorization: Bearer stub' -H "X-Stub-Claims: ${CLAIMS}" \
    "${AFD}/v1/jobs/${first}")"
  if [[ "$code" == "200" ]] && python3 -c "
import json,sys
body=json.load(open(sys.argv[1]))
msg=(body.get('result') or {}).get('message')
sys.exit(0 if body.get('status')=='completed' and msg==sys.argv[2] else 1)
" "$status_tmp" "$CANNED"; then
    echo "jobs completed: ${CANNED}"
    exit 0
  fi
  sleep 0.3
done

echo "GET /v1/jobs/${first} did not complete with canned message: $(cat "$status_tmp")" >&2
exit 1
