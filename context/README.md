# LOL3 Durable Context

This folder is the external working memory for Phantom + Ghost.

## Fast boot

Read:
1. context/HOT_STATE.md
2. context/FACT_LEDGER.md
3. context/DECISION_LEDGER.md
4. context/FAILURE_LEDGER.md
5. context/RESTART.md

That is the default working set. Do not reread the whole chat unless needed.

## Memory layers

HOT
- HOT_STATE.md
- RESTART.md

WARM
- FACT_LEDGER.md
- DECISION_LEDGER.md
- FAILURE_LEDGER.md

COLD
- CHAT_LOG.md
- PIPELINE_AUDIT_2026-09-19.md
- FINAL_AUDIT_2026-09-19.md
- BID_PIPELINE.md
- ARCHITECTURE.md
- BENCHMARK_HISTORY.md
- session snapshots

## Truth hierarchy

1. Directly verified repository/runtime/artifact evidence.
2. HOT_STATE for the current phase.
3. Fact/decision/failure ledgers for durable continuity.
4. Chronological chat history for historical context.

Never allow an old chat entry to override a newer verified result.

## Audit discipline

Do not claim completion because code exists or CI is green. Inspect:
- runtime behavior
- logs/traces
- produced artifacts
- semantic correctness
- failure paths
- reproducibility
- user-facing output

## Current production status

The audited Concrete/Indiana bid-to-outreach path is finalized for its current scope.

See:
- context/HOT_STATE.md
- context/FINAL_AUDIT_2026-09-19.md

## Memory self-test

Run:
`python tools/memory_audit.py`

The GitHub memory audit also runs in CI and validates that the compact boot memory is internally consistent and free of stale active blockers.
