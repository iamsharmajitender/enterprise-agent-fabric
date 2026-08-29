from typing import Any


def branch_slot_key(pinned: dict[str, Any]) -> str:
    """Slot id written by the stage that owns a workflow branch."""
    return str(pinned.get("id") or "")


def branch_choice(slot: dict[str, Any], branch: dict[str, str]) -> str:
    """Map a stage slot body to one of the branch keys. Fail closed when unknown."""
    if not branch:
        raise RuntimeError("branch map is empty")
    allowed = {str(key).strip().lower(): str(key) for key in branch}
    for field in ("risk", "risk_tier", "branch", "level", "tier"):
        raw = slot.get(field)
        if raw is None:
            continue
        token = str(raw).strip().lower()
        if token in allowed:
            return allowed[token]
    for value in slot.values():
        if isinstance(value, str):
            token = value.strip().lower()
            if token in allowed:
                return allowed[token]
    known = ", ".join(sorted(branch))
    raise RuntimeError(f"branch slot has no known key among {known}")


def resolve_branch_target(branch: dict[str, str], slot: dict[str, Any]) -> str:
    """Return the next workflow stage id from a branch map and slot body."""
    choice = branch_choice(slot, branch)
    for key, target in branch.items():
        if str(key) == choice:
            return str(target)
    raise RuntimeError(f"branch key {choice!r} has no target")
