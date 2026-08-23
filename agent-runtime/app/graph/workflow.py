from collections.abc import Callable
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.graph.llm import LlmPort
from app.tools.invoker import ToolInvoker


class GraphState(TypedDict, total=False):
    result: str
    goal: dict[str, Any]
    notes: list[str]


# Catalogue llm_role values: none (HTTP), query_formulation (LLM then HTTP),
# classify/synthesis (LLM, skip HTTP).
_LLM_ONLY_ROLES = frozenset({"classify", "synthesis"})
_KNOWN_LLM_ROLES = frozenset({"none", "query_formulation"}) | _LLM_ONLY_ROLES


def _node_name(tool: dict[str, Any], index: int) -> str:
    """LangGraph node id from capability id plus stage index."""
    raw = str(tool.get("id") or f"tool_{index}")
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in raw)
    return f"{cleaned}_{index}"


def _message(body: dict[str, Any]) -> str:
    """Pull a human-readable string from a tool HTTP body."""
    return str(body.get("text") or body.get("message") or "")


def _user_blob(goal: dict[str, Any], notes: list[str]) -> str:
    """Build the LLM user message from the goal and prior stage notes."""
    lines = [f"goal: {goal}"]
    if notes:
        lines.append("prior stage outputs:")
        lines.extend(f"- {note}" for note in notes)
    return "\n".join(lines)


def _llm_role(raw: Any) -> str:
    """Normalize llm_role; reject values the graph does not implement."""
    role = str(raw or "none").strip() or "none"
    if role not in _KNOWN_LLM_ROLES:
        raise RuntimeError(f"unknown llm_role {role!r}")
    return role


def _mapping(value: Any) -> dict[str, Any]:
    """Treat a non-dict as empty so stage fields stay optional."""
    return value if isinstance(value, dict) else {}


def _run_stage(
    pinned: dict[str, Any],
    state: GraphState,
    invoker: ToolInvoker,
    llm: LlmPort | None,
) -> GraphState:
    """Run one hydrated capability: LLM-only, LLM-then-HTTP, HTTP, or no-op."""
    invoke = _mapping(pinned.get("invoke"))
    goal = _mapping(state.get("goal"))
    notes = list(state.get("notes") or [])
    role = _llm_role(pinned.get("llm_role"))
    prompt = str(pinned.get("llm_prompt") or "")
    payload = dict(goal)
    if role in _LLM_ONLY_ROLES:
        if llm is None:
            raise RuntimeError(f"llm required for {role}")
        text = llm.complete(prompt, _user_blob(goal, notes))
        notes.append(text)
        return {"result": text, "notes": notes}
    if role == "query_formulation":
        if llm is None:
            raise RuntimeError("llm required for query_formulation")
        payload["query"] = llm.complete(prompt, _user_blob(goal, notes))
    if str(pinned.get("kind") or "") == "agent":
        text = "agent skipped (child jobs POST not wired)"
        notes.append(text)
        return {"result": text, "notes": notes}
    url = str(invoke.get("url") or "")
    if not url:
        result = notes[-1] if notes else str(state.get("result") or "")
        return {"result": result, "notes": notes}
    text = _message(invoker.call(invoke, payload))
    notes.append(text)
    return {"result": text, "notes": notes}


def build_tool_graph(
    tools: list[dict[str, Any]],
    invoker: ToolInvoker,
    llm: LlmPort | None = None,
    on_stage: Callable[[int, str, GraphState], None] | None = None,
):
    """Compile a linear LangGraph: one node per hydrated tool, in order."""
    builder = StateGraph(GraphState)
    if not tools:

        def empty(state: GraphState) -> GraphState:
            """No tools: complete with an empty result."""
            return {"result": ""}

        builder.add_node("empty", empty)
        builder.add_edge(START, "empty")
        builder.add_edge("empty", END)
        return builder.compile()

    previous = START
    for index, tool in enumerate(tools):
        name = _node_name(tool, index)

        def node(
            state: GraphState,
            pinned: dict[str, Any] = tool,
            step: int = index,
        ) -> GraphState:
            """Execute this stage; `pinned` / `step` are bound per loop iteration."""
            output = _run_stage(pinned, state, invoker, llm)
            if on_stage is not None:
                merged: GraphState = {**state, **output}
                on_stage(step, str(pinned.get("id") or name), merged)
            return output

        builder.add_node(name, node)
        builder.add_edge(previous, name)
        previous = name
    builder.add_edge(previous, END)
    return builder.compile()
