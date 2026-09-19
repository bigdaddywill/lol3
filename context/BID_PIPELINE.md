# Bid-to-Outreach Pipeline

## Target flow
SCRAPE BIDS -> NORMALIZE BID -> MATCH AGAINST SPANISH CONTRACTORS -> SELECT/ROUTE CONTRACTORS -> GENERATE BID INVITATION -> GENERATE EMAIL -> GENERATE FOLLOW-UP SMS -> TRACK STATUS

## Inputs
- Bid sources: configurable website/source adapters rather than one hard-coded scraper.
- Bid fields: project name, owner/GC, location, trade, scope, bid due date, project start, project type, plans/specs URL, contact name/email/phone when available, source URL, source timestamp.
- Contractor source: Spanish_cleaned_after_152_on_Leads_Magnet.xlsx.
- Outreach reference: the user's Gmail email/thread, which must be inspected before copying its wording, offer structure, sender identity, or CTA.

## Matching logic to implement after the workbook is accessible
1. Normalize contractor names, cities/states, trades, licenses/capabilities, service areas, and contact channels.
2. Normalize bid trade/scope and location.
3. Score matches using explicit fields, not fuzzy name similarity alone.
4. Require explainable match reasons for every selected contractor.
5. Do not invent missing contractor facts.
6. Produce a shortlist with match score/reasons and a confidence flag.

## Outreach outputs
- Bid invitation: concise project-specific invitation with scope/location/due date and required response fields.
- Email: generated from the real reference email once it is supplied/accessed.
- Follow-up SMS: short, direct, non-duplicate reminder tied to the same bid.
- Store generated artifacts with the bid ID and contractor ID so every message is auditable.

## Guardrails
- No email/SMS sending automatically until recipient/channel data and message are validated.
- Never expose unsupported contractor qualifications.
- Keep source URLs and extraction timestamps.
- Preserve original bid text where possible for auditability.
- Human approval can remain the final send gate.

## Current blocker
The Gmail connector is currently disabled by admin, so the target email cannot be inspected from this environment. The spreadsheet and Grok ZIP are present in GitHub, but their binary contents have not yet been materialized into an inspectable runtime file.

## Next verified work
- Obtain the reference email text/thread through an accessible source.
- Materialize the contractor workbook.
- Inspect workbook sheets, headers, row count, and sample records with the spreadsheet tooling.
- Build the scraper/matcher against the actual schema.
- Benchmark matching quality and message correctness on representative bid cases.

## Reference email audit — exact Gmail export

Source file:
`[Concrete _ Indiana] 8 open bids last 14 days — nearest deadline Aug 25, 2026.eml`

Email metadata:
- From: elyohason@gmail.com
- To: Aaronverlinde@gmail.com
- Date: Aug 23, 2026
- Subject: [Concrete / Indiana] 8 open bids last 14 days — nearest deadline Aug 25, 2026

The email is an HTML digest, not a single bid invitation. Its reusable structure is:
1. Market header: state + trade.
2. Digest summary: count of open bids, recency window, nearest deadline, and narrative observations.
3. Repeated bid cards.
4. Each card contains:
   - bid type/source label
   - numeric score
   - project title
   - source/listing URL
   - concise scope/fit summary
   - agency
   - solicitation/contract
   - posted date
   - deadline
   - NAICS
   - set-aside / qualification requirement
   - location
   - POC name/title/email/phone
   - "Why this matched" explanation
   - Open listing CTA
5. Footer cites source families and summarizes common qualification requirements.

Eight example cards visible in the reference:
- Overlay Phase 2 — City of Columbus #26-10
- Bike and Pedestrian Facilities — Marquette Greenway
- Pavement Patching — LaPorte District
- Small Structure Replacement — Reinforced Concrete Boxes
- Camp Atterbury Covered Training Area Facility
- Camp Atterbury 2026 Paving
- CGHS Renovations Package 2 — General Trades
- Muscatatuck Building 5114 Maintenance and Repair

Important product insight:
The digest does more than scrape. It applies a domain-specific relevance judgment such as "confirm concrete pay items", "cleanest sidewalk/trail fit", "commercial building slab/foundation", "Division 03 concrete", or "possible concrete floor/sidewalk/pad repair". Those explanations should become explicit, auditable matching reasons in the new pipeline.

The score should be treated as a derived ranking signal, not as a fact from the source listing. The implementation must expose the dimensions contributing to it and preserve the raw source evidence.

### Proposed end-to-end output

For each new bid:
`bid_source -> normalized_bid -> matched_contractors -> bid_invitation -> email -> follow_up_sms -> status`

The email generator should mirror the reference digest's factual discipline while changing the unit of output from a market digest to a contractor-specific opportunity.

