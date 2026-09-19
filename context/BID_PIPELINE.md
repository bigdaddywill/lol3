# Bid-to-Outreach Pipeline Contract

## Current production flow

LIVE BID SOURCES
-> NORMALIZE BID
-> TRADE RELEVANCE
-> STATE GATE
-> OPEN-DEADLINE GATE
-> MATCH SCORE / REASONS
-> BID INVITATION
-> EMAIL
-> FOLLOW-UP SMS
-> TRACKING
-> HUMAN SEND GATE

## Current audited scope

Trade: Concrete
Market: Indiana
Contractor source: Spanish_cleaned_after_152_on_Leads_Magnet.xlsx
Sheet: On Leads Magnet

## Contractor rules

A contractor is eligible for Concrete mode only when the documented category contains Concrete or Masonry.

Current Indiana production contractors:
- Percrete
- Carr Construction

Generic words such as construction, and, stone, or other broad substrings do not create trade evidence.

## Bid rules

A bid is eligible for Concrete mode only when its documented project/scope contains explicit concrete-relevant evidence.

HMA-only and pavement-marking-only opportunities are rejected.

A known bid state must equal contractor state.

A bid must have a verified open deadline before outreach is marked ready.

Historical source digests are fixtures/provenance. Their old deadlines do not establish current open status.

## Source policy

Required:
- Indiana Department of Transportation current regular letting.

Optional:
- Indiana State Armory Board.
- Public Purchase Indianapolis.

Optional source failure or degradation is recorded in source_health.json and excluded from matching. The system never invents bids to fill a gap.

## Outputs

- bids.json
- source_health.json
- contractor_audit.json
- outreach_queue.json
- manifest.json
- tracking JSONL

Each outbound queue record contains:
- bid evidence
- contractor evidence
- match score and reasons
- validation result
- generated invitation
- generated email
- follow-up SMS
- send gate
- message hash / tracking key

## Human gate

Generated email/SMS are never automatically sent.

Every current outbound record ends with:
HUMAN_REVIEW_REQUIRED

## Current audited result

- 39 current INDOT contracts parsed
- 25 current concrete-relevant INDOT bids retained
- 50 current contractor/bid pairings
- 50 email-ready
- 50 SMS-ready
- 0 validation errors

See context/FINAL_AUDIT_2026-09-19.md for evidence.
