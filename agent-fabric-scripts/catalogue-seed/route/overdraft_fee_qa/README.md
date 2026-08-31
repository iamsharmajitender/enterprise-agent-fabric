# overdraft_fee_qa

Route id: `overdraft_fee_qa` · version `2026.08.1` · Pattern 0 (prompt + prefetch, one-shot).

Answers grounded overdraft fee questions from `fee-schedule` and `product-disclosure` corpora. Account types in the mock data: Everyday, Business, Corporate, Student, Premier.

| File | Contract | Database |
| --- | --- | --- |
| [`corpora.sql`](corpora.sql) | Corpus gateway URLs | `adp.dataplane.corpora` |
| [`prompt.sql`](prompt.sql) | Host prompt | `adp.dataplane.prompt_packs` |
| [`route.sql`](route.sql) | Route pin | `adp.dataplane.routes` |
| [`retrieval.sql`](retrieval.sql) | Prefetch policy | `adp.dataplane.retrieval` |
| [`intent.sql`](intent.sql) | `/overdraft` command | `adp.dataplane.intent_rules` |

Mock corpora live under [`agent-fabric-mocks/tools/data/corpora/`](../../../../agent-fabric-mocks/tools/data/corpora/).

```bash
./add.sh
```

Then open [http://localhost:3014/chat](http://localhost:3014/chat) and run `overdraft_fee_qa` (set `FABRIC_LLM_STUB=1` on Runtime for stub LLM).

Remove: `./remove.sh`

Example utterance: *What is the overdraft fee on our Everyday account?*
