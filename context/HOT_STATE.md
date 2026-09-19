# LOL3 Hot State

updated: 2026-09-19
repo: bigdaddywill/lol3
branch: main

## MISSION
Build and maintain the bid-to-outreach automation system while preserving durable context in GitHub.

## CURRENT PHASE
FINALIZED_FOR_CURRENT_CONCRETE_INDIANA_SCOPE

The current production path is complete and audited. Older "next step" notes elsewhere are historical unless HOT_STATE changes.

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

## AUDIT TRUTH
- Production audit 35422565481: SUCCESS.
- Standalone smoke 35422611533: SUCCESS, 17/17 tests.
- Final production artifact 10578650088.
- Artifact SHA-256 73b49ec60b4b624faab382701fa5bd8ed5546273e46f45b743b288172068eccc.
- Audited source head f8f768ba97534e7cddca9013598bae5c0af86a8c.

## ACTIVE TODO
None for this defined scope.

A new user request creates a new phase. Update this file only from verified reality.

## MEMORY SYSTEM SELF-TEST
- Memory audit run 35423030637: SUCCESS.
- Cold-start reconstruction: PASS.
- Boot set: HOT_STATE -> FACT_LEDGER -> DECISION_LEDGER -> FAILURE_LEDGER -> RESTART.
- The memory audit caught and fixed two internal audit bugs during the spin.
- Spin result: context/MEMORY_SPIN_RESULT.md
