# LOL3 Current State

## Identity
- User: Ghost
- Assistant/project handle: Phantom
- Repository: bigdaddywill/lol3
- Default branch: main

## Current phase
FINALIZED_FOR_CURRENT_CONCRETE_INDIANA_SCOPE

## Mission
Maintain the audited bid-to-outreach automation system and use GitHub as durable external working memory.

## Verified production state
- Contractor workbook: Spanish_cleaned_after_152_on_Leads_Magnet.xlsx
- Sheet: On Leads Magnet
- 264 contractor rows loaded
- 1 duplicate removed
- 2 missing business names recovered
- 0 unidentifiable rows
- Indiana Concrete/Masonry contractors in the production pool: Percrete and Carr Construction
- 39 current INDOT contracts parsed
- 25 current concrete-relevant INDOT bids retained
- 8 historical reference-email bids retained as fixture/provenance only
- 50 current bid/contractor pairings
- 50 email-ready
- 50 SMS-ready
- 0 validation errors
- Every outbound record is HUMAN_REVIEW_REQUIRED

## Matching contract
Concrete mode requires:
1. documented Concrete or Masonry contractor category
2. concrete-relevant bid evidence
3. same-state bid and contractor
4. verified open deadline

HMA-only and pavement-marking-only opportunities are excluded.

## Source health
Required: INDOT current regular letting — healthy in final audit.
Optional: SAB and Public Purchase — degraded/empty results are recorded and excluded rather than creating phantom bids.

## Audit truth
- Production audit 35422565481: SUCCESS
- Standalone smoke 35422611533: SUCCESS
- Smoke suite: 17/17 tests
- Final artifact: 10578650088
- Artifact SHA-256: 73b49ec60b4b624faab382701fa5bd8ed5546273e46f45b743b288172068eccc
- Audited source head: f8f768ba97534e7cddca9013598bae5c0af86a8c

## Memory system
Boot with:
- context/MEMORY_INDEX.md
- context/HOT_STATE.md
- context/FACT_LEDGER.md
- context/DECISION_LEDGER.md
- context/FAILURE_LEDGER.md
- context/RESTART.md

Deep evidence lives in:
- context/FINAL_AUDIT_2026-09-19.md
- context/PIPELINE_AUDIT_2026-09-19.md
- context/CHAT_LOG.md

## Active TODO
None for the defined current scope.

A new user request creates a new phase. HOT_STATE must be updated only from verified results.
