from app.graph import build_stub_graph


def test_langgraph_stub_is_on_classpath() -> None:
  graph = build_stub_graph()
  assert graph is not None
