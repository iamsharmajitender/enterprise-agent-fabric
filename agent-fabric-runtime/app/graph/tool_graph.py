from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.agents.jobs_client import JobsPort
from app.agents.prefetch import PREFETCH_SLOT_ID, PrefetchPort, is_prefetch_stage
from app.graph.branch import branch_slot_key, resolve_branch_target
from app.graph.llm import LlmPort
from app.graph.stage_runner import run_stage
from app.graph.state import GraphState, slots
from app.tools.invoker import ToolInvoker


def _stage_key(tool: dict[str, Any]) -> str:
    return str(tool.get("workflow_stage_id") or tool.get("id") or "")


def _expects_prefetch_pack(tools: list[dict[str, Any]]) -> bool:
    return any(str(tool.get("id") or "") == PREFETCH_SLOT_ID for tool in tools)


def _node_name(tool: dict[str, Any], index: int) -> str:
    raw = str(tool.get("id") or f"tool_{index}")
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in raw)
    return f"{cleaned}_{index}"


def _branch_index(tools: list[dict[str, Any]]) -> int | None:
    for index, tool in enumerate(tools):
        branch = tool.get("branch")
        if isinstance(branch, dict) and branch:
            return index
    return None


def _make_stage_node(
    name: str,
    tool: dict[str, Any],
    index: int,
    invoker: ToolInvoker,
    llm: LlmPort | None,
    *,
    retrieval: dict[str, Any] | None,
    prefetch: PrefetchPort | None,
    catalogue: Any,
    expects_prefetch: bool,
    on_stage: Callable[[int, str, GraphState], None] | None,
    jobs: JobsPort | None = None,
) -> Callable[[GraphState], GraphState]:
    def node(state: GraphState) -> GraphState:
        output = run_stage(
            tool,
            state,
            invoker,
            llm,
            retrieval=retrieval,
            prefetch=prefetch,
            catalogue=catalogue,
            expects_prefetch=expects_prefetch,
            jobs=jobs,
        )
        if on_stage is not None:
            merged: GraphState = {**state, **output}
            if is_prefetch_stage(tool, retrieval):
                slot_map = merged.get("slots") if isinstance(merged.get("slots"), dict) else {}
                emitted = False
                for key in slot_map:
                    key_s = str(key)
                    if key_s.startswith(f"{tool.get('id') or 'prefetch'}:"):
                        on_stage(index, key_s, merged)
                        emitted = True
                if not emitted:
                    on_stage(index, str(tool.get("id") or name), merged)
            else:
                on_stage(index, str(tool.get("id") or name), merged)
        return output

    return node


def build_tool_graph(
    tools: list[dict[str, Any]],
    invoker: ToolInvoker,
    llm: LlmPort | None = None,
    on_stage: Callable[[int, str, GraphState], None] | None = None,
    retrieval: dict[str, Any] | None = None,
    prefetch: PrefetchPort | None = None,
    catalogue: Any = None,
    *,
    start_index: int = 0,
    jobs: JobsPort | None = None,
):
    """Compile a LangGraph from hydrated tools; branch stages pick the next node from slots."""
    full_tools = tools
    if start_index:
        tools = tools[start_index:]
    expects_prefetch = _expects_prefetch_pack(tools)
    builder = StateGraph(GraphState)
    if not tools:

        def empty(state: GraphState) -> GraphState:
            return {"result": ""}

        builder.add_node("empty", empty)
        builder.add_edge(START, "empty")
        builder.add_edge("empty", END)
        return builder.compile()

    nodes: list[tuple[str, dict[str, Any], str]] = []
    for index, tool in enumerate(tools):
        name = _node_name(tool, index)
        stage_id = _stage_key(tool)
        bound = dict(tool)
        bound["_graph_index"] = start_index + index
        bound["_graph_tools"] = full_tools
        nodes.append((name, bound, stage_id))
        builder.add_node(
            name,
            _make_stage_node(
                name,
                bound,
                start_index + index,
                invoker,
                llm,
                retrieval=retrieval,
                prefetch=prefetch,
                catalogue=catalogue,
                expects_prefetch=expects_prefetch,
                on_stage=on_stage,
                jobs=jobs,
            ),
        )

    stage_to_node = {stage_id: node_name for node_name, _tool, stage_id in nodes if stage_id}
    branch_at = _branch_index(tools)
    if branch_at is None:
        previous = START
        for node_name, _tool, _stage_id in nodes:
            builder.add_edge(previous, node_name)
            previous = node_name
        builder.add_edge(previous, END)
        return builder.compile()

    branch_tool = nodes[branch_at][1]
    branch_map = branch_tool.get("branch")
    if not isinstance(branch_map, dict):
        raise RuntimeError("branch stage missing branch map")
    slot_key = branch_slot_key(branch_tool)
    branch_targets = {str(value) for value in branch_map.values()}
    merge_at = None
    for index in range(branch_at + 1, len(nodes)):
        if nodes[index][2] not in branch_targets:
            merge_at = index
            break
    if merge_at is None:
        raise RuntimeError("branch workflow missing merge stage after branch targets")

    previous = START
    for index in range(branch_at):
        builder.add_edge(previous, nodes[index][0])
        previous = nodes[index][0]
    builder.add_edge(previous, nodes[branch_at][0])

    branch_node_name = nodes[branch_at][0]
    route_map = {
        stage_to_node[target]: stage_to_node[target]
        for target in branch_targets
        if target in stage_to_node
    }
    if len(route_map) != len(branch_targets):
        missing = sorted(branch_targets - set(route_map))
        raise RuntimeError(f"branch targets missing from graph: {missing}")

    def route_branch(state: GraphState) -> str:
        slot_body = slots(state).get(slot_key) or {}
        if not isinstance(slot_body, dict):
            slot_body = {}
        target_stage = resolve_branch_target(branch_map, slot_body)
        return stage_to_node[target_stage]

    builder.add_conditional_edges(branch_node_name, route_branch, route_map)

    merge_node_name = nodes[merge_at][0]
    for target in branch_targets:
        builder.add_edge(stage_to_node[target], merge_node_name)

    previous = merge_node_name
    for index in range(merge_at + 1, len(nodes)):
        builder.add_edge(previous, nodes[index][0])
        previous = nodes[index][0]
    builder.add_edge(previous, END)
    return builder.compile()
