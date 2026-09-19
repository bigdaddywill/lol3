# LOL3 Memory Index

## Memory architecture

SESSION SWARM
- swarm/README.md — session swarm overview.
- swarm/SESSION_BOOT.md — fresh-session boot card.
- swarm/PROTOCOL.md — message contract.
- swarm/ROUTER.md — role routing.
- swarm/board/BLACKBOARD.md — shared mission board.
- swarm/inbox/<agent>/ — immutable agent mailbox.

HOT
- HOT_STATE.md — current truth.
- RESTART.md — startup protocol.
- agent/STATE.json — current execution state.

WARM
- FACT_LEDGER.md — durable facts.
- agent/QUEUE.json — durable work queue.
- agent/LEDGER.md — in-flight execution history.
- agent/WORKER_CONTRACT.md — worker/resume protocol.
- DECISION_LEDGER.md — durable decisions.
- FAILURE_LEDGER.md — solved failures and prevention.

COLD
- CHAT_LOG.md — chronological history.
- PIPELINE_AUDIT_2026-09-19.md — detailed audit history.
- FINAL_AUDIT_2026-09-19.md — consolidated final evidence.
- BID_PIPELINE.md — pipeline contract.
- ARCHITECTURE.md, BENCHMARK_HISTORY.md, snapshots — deeper context.

## Retrieval strategy

Current status -> HOT_STATE only.
Session swarm status -> HOT_STATE + swarm/board/BLACKBOARD.md + relevant inbox.
Why a decision exists -> HOT_STATE + DECISION_LEDGER.
Whether something was tested or fixed -> HOT_STATE + FACT_LEDGER + FAILURE_LEDGER.
What happened historically -> CHAT_LOG.
What is being worked right now -> HOT_STATE + agent/STATE.json + agent/QUEUE.json.
Proof -> FACT_LEDGER + relevant audit/artifact.

Only HOT_STATE declares the current phase.

CHAT_LOG is archival history, not current truth.

Spin evidence:
- context/MEMORY_SPIN_RESULT.md
- GitHub memory audit run 35423030637: SUCCESS
