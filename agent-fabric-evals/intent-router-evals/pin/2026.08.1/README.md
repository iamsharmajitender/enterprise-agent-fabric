# Pin / hydrate (suite version 2026.08.1)

No JSON cases here — only [`pin-suite.json`](pin-suite.json). This version labels the **catalogue cut** that pin checks assume.

| Gate | Where |
| --- | --- |
| Catalogue pin lint | `CataloguePinLintTest` in `agent-data-plane` (in-process) |
| Compose smoke | `WAIT=1 ./docs/run/dummy-request/run-job.sh --all` |

Routing labels stay under `../routing/`. Fail-closed prove: retire ACR `fee_explain@2026.08.1` → jobs POST `HYDRATE_FAILED`; reload with `./docs/run/scripts/seed-db.sh`.
