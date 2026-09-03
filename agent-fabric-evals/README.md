# Agent Fabric evals

CI answer keys kept **outside** Data Plane. ADP only runs the thin JUnit harness and mounts this tree as test resources.

| Folder | Gate |
| --- | --- |
| [`intent-router-evals/`](intent-router-evals/) | Chat routing, jobs entitle, catalogue pin lint |
| [`route-quality/`](route-quality/) | Per-route tool/stage order (`eval_suite_id`) |

```bash
./agent-fabric-plane/agent-data-plane/run-eval.sh              # intent-router
./agent-fabric-plane/agent-data-plane/run-eval.sh --quality   # route-quality
./agent-fabric-plane/agent-data-plane/run-eval.sh --all       # both
```

Not on the hot path. Compose `--all` is pin/hydrate smoke, not routing labels.
