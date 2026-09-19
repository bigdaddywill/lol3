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