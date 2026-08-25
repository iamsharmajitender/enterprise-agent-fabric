# agent-fabric-evals

Platform/CI eval fixtures for Enterprise Agent Fabric. **Not** on decide / pin / start / loop.

| Folder | What |
| --- | --- |
| [`intent-router-evals/`](intent-router-evals/README.md) | Decide board: routing, jobs entitle, pin lint gate |
| [`route-quality/`](route-quality/README.md) | After start — Pattern 2 tool-sequence (`*_tools`); `./route-quality/run.sh` or `run-eval.sh --quality` |

```bash
./agent-fabric-evals/intent-router-evals/run.sh
./agent-fabric-evals/route-quality/run.sh
# or ./agent-data-plane/run-eval.sh [--quality|--all]
```

Task lists: [`docs/tasks/eval-plan.md`](../docs/tasks/eval-plan.md), [`docs/tasks/eval-todo.md`](../docs/tasks/eval-todo.md).
