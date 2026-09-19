# LOL3 Hot State

updated: 2026-09-19
executor_layer_updated: 2026-09-19
session_swarm_layer_updated: 2026-09-19
repo: bigdaddywill/lol3
branch: main

## MISSION
Build and maintain the bid-to-outreach automation system while preserving durable context in GitHub.

## CURRENT PHASE
CHATGPT_48_SESSION_COORDINATION_PROOF

The 48-worker coordination proof is the active swarm mission. The deterministic worker body is intentionally separate from the later model-driven agent layer.

## CURRENT FLOW
LIVE BID SOURCES -> NORMALIZE -> TRADE RELEVANCE -> STATE GATE -> OPEN-DEADLINE GATE -> MATCH SCORE/REASONS -> BID INVITATION -> EMAIL -> FOLLOW-UP SMS -> TRACKING -> HUMAN SEND GATE

## VERIFIED FACTS
- Contractor workbook: Spanish_cleaned_after_152_on_Leads_Magnet.xlsx
- Sheet: On Leads Magnet
- 264 contractor rows loaded; 1 duplicate removed; 2 missing business names recovered; 0 unidentifiable.
- Indiana Concrete/Masonry production contractors: Percrete and Carr Construction.
- Mode: --states IN --trade concrete
- 39 current INDOT contracts parsed.
- 25 current concrete-relevant INDOT bids retained.
- 8 historical reference-email bids are fixture/provenance only and are closed.
- 50 current bid/contractor pairings.
- 50 email-ready.
- 50 SMS-ready.
- 0 validation errors.
- Every outbound record is HUMAN_REVIEW_REQUIRED.

## HARD MATCHING GATES
1. Contractor category must document Concrete or Masonry.
2. Bid must contain concrete-relevant scope evidence.
3. Bid and contractor must share state.
4. Bid must have a verified open deadline.

HMA-only and pavement-marking-only opportunities are excluded from Concrete mode.

## SOURCE HEALTH
Required:
- INDOT current regular letting: healthy in final audit.

Optional:
- SAB: degraded/empty responses are recorded and excluded.
- Public Purchase Indianapolis: optional.

## CHATGPT SESSION SWARM TRUTH
- `swarm/README.md`: swarm architecture and limitation boundary.
- `swarm/PROTOCOL.md`: immutable message protocol.
- `swarm/ROUTER.md`: role routing and boot order.
- `swarm/SESSION_BOOT.md`: boot card for a fresh ChatGPT session.
- `swarm/agents/`: five predefined agent identities.
- `swarm/inbox/`: per-agent durable mailboxes.
- `swarm/board/BLACKBOARD.md`: shared swarm state.
- `tools/swarm_protocol.py`: local protocol validator/helper.
- `.github/workflows/session-swarm-audit.yml`: swarm CI self-test.
- Actual live multi-session ChatGPT handshake is not yet verified.

## PERSISTENT EXECUTOR TRUTH
- `agent/QUEUE.json`: durable task queue.
- `agent/STATE.json`: active task, worker lease, checkpoint, recovery counter.
- `agent/LEDGER.md`: operational event history.
- `tools/agent_supervisor.py`: claim/checkpoint/finish/fail/watchdog protocol.
- `.github/workflows/agent-brain-audit.yml`: scheduled watchdog + self-test.
- Worker runtime connection is not yet verified end-to-end; the current implementation is the durable control plane, not an immortal chat session.

## AUDIT TRUTH
- Production audit 35422565481: SUCCESS.
- Standalone smoke 35422611533: SUCCESS, 17/17 tests.
- Final production artifact 10578650088.
- Artifact SHA-256 73b49ec60b4b624faab382701fa5bd8ed5546273e46f45b743b288172068eccc.
- Audited source head f8f768ba97534e7cddca9013598bae5c0af86a8c.

## ACTIVE TODO
- Verify the corrected 48-session run whose source commit is the hardened workflow/mission state, not the earlier provisional run.
- Inspect the final 48-session evidence for count, identity, shared mission hash, runner platform, failure visibility, and provenance.
- Verify whether 48 jobs actually ran concurrently or were queued by the account's GitHub Actions concurrency ceiling.
- After the coordination proof is independently finalized, replace the deterministic worker body with real model-driven agents while preserving the same evidence/integration gates.

Update this file only from verified reality.

## 48-SESSION PROOF STATUS
- Provisional first run: GitHub Actions run 35424136351, source commit 2677dfdd, result PASS with 48/48 workers and one shared mission hash.
- That result is NOT canonical because the integrator failure-handling bug was discovered afterward.
- Hardened workflow commit: e08042fcc98d09c681dd83b1ee6200549e7f4eae.
- Hardened mission commit: 47141871175d72c3af5b82ee223a25d3705bec99.
- Corrected rerun is expected from the hardened mission push; its final persisted report must name the corrected source commit before it can replace the provisional result as canonical.

## MEMORY SYSTEM SELF-TEST
- Memory audit run 35423030637: SUCCESS.
- Cold-start reconstruction: PASS.
- Boot set: HOT_STATE -> FACT_LEDGER -> DECISION_LEDGER -> FAILURE_LEDGER -> RESTART.
- The memory audit caught and fixed two internal audit bugs during the spin.
- Spin result: context/MEMORY_SPIN_RESULT.md
