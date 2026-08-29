#!/usr/bin/env python3
"""Post catalogue chat turns to Front Door and poll until done."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CATALOG = HERE / "chats.json"
AFD = os.environ.get("AFD_URL", "http://localhost:3005").rstrip("/")
POLL_ATTEMPTS = int(os.environ.get("POLL_ATTEMPTS", "45"))
POLL_SLEEP = float(os.environ.get("POLL_SLEEP", "2"))
STRICT_MESSAGE = os.environ.get("STRICT_MESSAGE", "0") == "1"

FORBIDDEN_FR5 = frozenset(
    {"route_id", "run_id", "agent_client_id", "confidence", "router_layer"}
)


def catalog_key(row: dict[str, Any]) -> str:
    return row.get("id") or row["route_id"]


def load_catalog() -> list[dict[str, Any]]:
    data = json.loads(CATALOG.read_text())
    return data["chats"]


def filter_chats(chats: list[dict[str, Any]], mode: str | None) -> list[dict[str, Any]]:
    if not mode:
        return chats
    return [chat for chat in chats if str(chat["autonomy_mode"]) == mode]


def assert_fr5(node: Any) -> None:
    if isinstance(node, dict):
        leak = set(node) & FORBIDDEN_FR5
        if leak:
            sys.exit(f"FR-5 leak {','.join(sorted(leak))}")
        for value in node.values():
            assert_fr5(value)
    elif isinstance(node, list):
        for value in node:
            assert_fr5(value)


def expand(node: Any, token: str) -> Any:
    if isinstance(node, str):
        return node.replace("{id}", token)
    if isinstance(node, dict):
        return {key: expand(value, token) for key, value in node.items()}
    if isinstance(node, list):
        return [expand(value, token) for value in node]
    return node


def mint(chat_id: str) -> dict[str, Any]:
    chat = next((row for row in load_catalog() if catalog_key(row) == chat_id), None)
    if chat is None:
        sys.exit(f"unknown chat id: {chat_id}")
    token = uuid.uuid4().hex[:12]
    claims = {"sub": "jane", "emts": {claim: True for claim in chat.get("claims") or []}}
    return {
        "id": catalog_key(chat),
        "route_id": chat["route_id"],
        "message": expand(chat.get("message") or "", token),
        "expected_message": chat.get("expected_message"),
        "expected_status": chat.get("expected_status") or "completed",
        "claims": claims,
        "autonomy_mode": chat["autonomy_mode"],
        "label": chat["label"],
        "token": token,
    }


def http_json(
    method: str,
    path: str,
    *,
    claims: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> tuple[int, Any]:
    headers = {"Authorization": "Bearer stub"}
    if claims is not None:
        headers["X-Stub-Claims"] = json.dumps(claims, separators=(",", ":"))
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(f"{AFD}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            payload = json.load(resp)
            return resp.status, payload
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        try:
            payload = json.loads(detail)
        except json.JSONDecodeError:
            payload = detail
        return exc.code, payload


def list_chats(mode: str | None) -> None:
    for chat in filter_chats(load_catalog(), mode):
        key = catalog_key(chat)
        claims = ",".join(chat.get("claims") or []) or "-"
        print(f"{chat['autonomy_mode']}  {chat['label']:<18}  {key:<28}  {claims}")


def post_turn(claims: dict[str, Any], message: str) -> str:
    code, body = http_json(
        "POST",
        "/v1/assistant/turns",
        claims=claims,
        body={"message": message},
    )
    if code != 200:
        sys.exit(f"POST /v1/assistant/turns expected 200, got {code}: {body}")
    assert_fr5(body)
    status = body.get("status")
    session_id = body.get("session_id") or ""
    if status != "accepted" or not session_id.startswith("chat-"):
        sys.exit(f"turn was not accepted: {json.dumps(body)}")
    return session_id


def poll_events(
    session_id: str,
    claims: dict[str, Any],
    expected_message: str | None,
    expected_status: str,
) -> None:
    terminal = {expected_status, "failed"}
    if expected_status == "completed":
        terminal.add("completed")

    for _ in range(POLL_ATTEMPTS):
        code, body = http_json(
            "GET",
            f"/v1/assistant/sessions/{session_id}/events",
            claims=claims,
        )
        status = (body.get("status") or "") if code == 200 else ""
        if code == 200 and status in terminal:
            assert_fr5(body)
            message = body.get("message") or ""
            print(f"status={status}")
            print("result:", message or json.dumps(body))
            if status != expected_status:
                sys.exit(f"chat did not reach {expected_status}: status={status}")
            if (
                expected_status == "completed"
                and expected_message
                and message != expected_message
            ):
                if STRICT_MESSAGE:
                    sys.exit(
                        f"chat message mismatch: expected {expected_message!r} got {message!r}"
                    )
                print(
                    "chat message drift (non-fatal unless STRICT_MESSAGE=1): "
                    f"expected {expected_message!r} got {message!r}",
                    file=sys.stderr,
                )
            return
        time.sleep(POLL_SLEEP)
    sys.exit(f"poll timeout for {session_id}: {json.dumps(body)}")


def run_one(chat_id: str, *, create_only: bool) -> None:
    row = mint(chat_id)
    claims = row["claims"]
    print(
        f"chat_id={chat_id}  route_id={row['route_id']}  "
        f"autonomy={row['autonomy_mode']} ({row['label']})"
    )
    print(f"token={row['token']}")
    print(f"message={row['message']}")

    print(f"POST /v1/assistant/turns ({row['route_id']})...")
    session_id = post_turn(claims, row["message"])
    print(f"session_id={session_id}")

    if create_only:
        return

    expected_status = row["expected_status"]
    print(f"GET /v1/assistant/sessions/{session_id}/events until {expected_status} or failed...")
    poll_events(session_id, claims, row.get("expected_message"), expected_status)


def ensure_front_door() -> None:
    try:
        urllib.request.urlopen(f"{AFD}/health")
    except OSError as exc:
        sys.exit(f"Front Door is not up at {AFD}/health: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Post catalogue chat turns to Front Door and poll until done."
    )
    parser.add_argument("--list", "-l", action="store_true", help="List chats from chats.json")
    parser.add_argument("--all", action="store_true", help="Run every chat in chats.json")
    parser.add_argument("--mode", metavar="N", help="Filter by autonomy_mode (0-3)")
    parser.add_argument("--create-only", action="store_true", help="Post turn only; do not poll")
    parser.add_argument("chat_id", nargs="?", help="chats.json id (or route_id when id is omitted)")
    args = parser.parse_args()

    if not CATALOG.is_file():
        sys.exit(f"missing {CATALOG}")

    if args.mode and args.mode not in {"0", "1", "2", "3"}:
        parser.error("--mode must be 0-3")

    if args.list or (not args.chat_id and not args.all and not args.mode):
        list_chats(args.mode)
        return

    ensure_front_door()

    if args.chat_id:
        run_one(args.chat_id, create_only=args.create_only)
        return

    if args.all or args.mode:
        create_only = args.create_only
        if not create_only and os.environ.get("WAIT", "0") != "1":
            create_only = True
        for chat in filter_chats(load_catalog(), args.mode):
            print("----")
            run_one(catalog_key(chat), create_only=create_only)
        return

    parser.print_usage()
    sys.exit(2)


if __name__ == "__main__":
    main()
