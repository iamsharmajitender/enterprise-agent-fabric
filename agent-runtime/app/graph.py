from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class StubState(TypedDict):
  result: str


def emit_fee(state: StubState) -> StubState:
  return {"result": "Fee of $42 is the monthly account charge."}


def build_stub_graph():
  builder = StateGraph(StubState)
  builder.add_node("emit_fee", emit_fee)
  builder.add_edge(START, "emit_fee")
  builder.add_edge("emit_fee", END)
  return builder.compile()
