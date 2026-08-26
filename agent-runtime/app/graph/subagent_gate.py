"""Pause parent runs until kind=agent subagent jobs finish (join), then resume."""

from __future__ import annotations

import time
from typing import Any, Protocol


class SubagentWaiting(Exception):
    """Raised when a join=true subagent job was started and the parent must pause."""

    def __init__(
        self,
        *,
        stage_id: str,
        gate_index: int,
        resume_index: int,
        subagent_ids: list[str],
        state: dict[str, Any],
        resume_loop_step: int | None = None,
    ) -> None:
        self.stage_id = stage_id
        self.gate_index = gate_index
        self.resume_index = resume_index
        self.subagent_ids = list(subagent_ids)
        self.state = state
        self.resume_loop_step = resume_loop_step
        super().__init__(f"subagent waiting for join at {stage_id!r}: {self.subagent_ids}")


class JobsStatusPort(Protocol):
    def status(self, correlation_id: str) -> dict[str, Any]: ...


def join_enabled(pinned: dict[str, Any], invoke: dict[str, Any]) -> bool:
    """True when this kind=agent capability should pause the parent until the subagent finishes."""
    if pinned.get("join") is True:
        return True
    return invoke.get("join") is True


def subagent_result_present(slots: dict[str, Any], stage_id: str) -> bool:
    """True when the stage slot already holds a joined subagent result."""
    body = slots.get(stage_id)
    if not isinstance(body, dict):
        return False
    status = str(body.get("status") or "").lower()
    return status in {"completed", "failed"} and "result" in body


def parse_subagent_packet(body: dict[str, Any] | None) -> list[dict[str, Any]] | None:
    """Extract a subagent resume packet; empty / human-gate shaped bodies stay paused."""
    if not isinstance(body, dict) or not body:
        return None
    raw = body.get("subagents")
    if not isinstance(raw, list) or not raw:
        return None
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            return None
        corr = str(item.get("correlation_id") or "").strip()
        status = str(item.get("status") or "").strip().lower()
        if not corr or status not in {"completed", "failed"}:
            return None
        out.append(
            {
                "correlation_id": corr,
                "status": status,
                "result": item.get("result"),
            }
        )
    return out


def merge_subagent_packet(
    slots: dict[str, Any],
    stage_id: str,
    packet: list[dict[str, Any]],
) -> dict[str, Any]:
    """Merge joined subagent results into the stage slot (supports one or many ids)."""
    merged = dict(slots)
    prior = merged.get(stage_id) if isinstance(merged.get(stage_id), dict) else {}
    prior = dict(prior) if isinstance(prior, dict) else {}
    if len(packet) == 1:
        item = packet[0]
        prior.update(
            {
                "correlation_id": item["correlation_id"],
                "status": item["status"],
                "result": item.get("result"),
            }
        )
    else:
        prior["status"] = "completed" if all(p["status"] == "completed" for p in packet) else "failed"
        prior["subagents"] = packet
        prior["result"] = {p["correlation_id"]: p.get("result") for p in packet}
    merged[stage_id] = prior
    return merged


def poll_subagents(
    jobs: JobsStatusPort,
    subagent_ids: list[str],
    *,
    interval_s: float = 0.5,
    timeout_s: float = 120.0,
) -> list[dict[str, Any]]:
    """Poll AFD/AR job status until every subagent is terminal or timeout."""
    if not subagent_ids:
        return []
    deadline = time.monotonic() + max(0.1, timeout_s)
    pending = set(subagent_ids)
    done: dict[str, dict[str, Any]] = {}
    while pending:
        if time.monotonic() > deadline:
            raise TimeoutError(f"subagent join timed out waiting for {sorted(pending)}")
        for corr in list(pending):
            body = jobs.status(corr)
            status = str(body.get("status") or "").lower()
            if status in {"completed", "failed"}:
                done[corr] = {
                    "correlation_id": corr,
                    "status": status,
                    "result": body.get("result"),
                }
                pending.discard(corr)
        if pending:
            time.sleep(interval_s)
    return [done[corr] for corr in subagent_ids]
