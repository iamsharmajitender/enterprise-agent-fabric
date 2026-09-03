# Route quality

Per-route suites for **after start**: did **this** route do the right work in order?

Keyed by catalogue `eval_suite_id` (`{route_id}_tools`). Free-form Pattern 0/1 without a workflow keep `eval_suite_id` empty.

```bash
./agent-fabric-evals/route-quality/run.sh
# or:
./agent-fabric-plane/agent-data-plane/run-eval.sh --quality
```

Active suites (stack board): `duplicate_charge_review_tools`, `kyc_onboarding_tools`, `ticket_triage_tools`.
