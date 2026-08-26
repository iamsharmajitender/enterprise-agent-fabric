"""Helpers for fabric session_id shapes: chat-|job-|sub- + UUID."""

from __future__ import annotations


def is_jobs_session(session_id: str) -> bool:
    """True for top-level jobs and subagent freeze keys (incl. legacy job: prefix)."""
    sid = (session_id or "").strip()
    return sid.startswith(("job-", "sub-", "job:"))
