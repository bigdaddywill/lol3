# LOL3 Restart Protocol

## Cold start
Read:
1. HOT_STATE.md
2. FACT_LEDGER.md
3. DECISION_LEDGER.md
4. FAILURE_LEDGER.md
5. RESTART.md

Then recover:
- current phase
- verified facts
- last audit
- active TODO

Do not read the whole chat unless the task requires history.

## Warm start
1. Read HOT_STATE.
2. Read the ledger relevant to the request.
3. Inspect the repo files involved.
4. Inspect current CI/artifacts if behavior is involved.
5. Update HOT_STATE and the relevant ledger before ending.

## New phase
1. Change HOT_STATE to the new phase.
2. Record the decision.
3. Add the request/results to CHAT_LOG.
4. Preserve prior facts as historical.
5. Audit the change.
6. Update HOT_STATE from verified results only.

## Rules
- HOT_STATE is current truth.
- CHAT_LOG is archival.
- Never silently overwrite contradictions.
- Never delete a failed approach; record it in FAILURE_LEDGER.
- Never claim a capability because code exists; require runtime/test evidence.

The target is a two-minute cold start.
