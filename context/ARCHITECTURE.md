# LOL3 Architecture

## Status
Architecture is not final. The Grok workspace must be inspected before design decisions become authoritative.

## Candidate inherited architecture from LOL2
USER TASK
  -> 3B COMMANDER
  -> independent 3B SUBORDINATE
  -> Playwright / Chromium
  -> Gemini Web
  -> Gemini responses + screenshots + hashes
  -> PASS / REVISE audit
  -> commander revision
  -> final gated answer

## LOL3 requirements
- No fake browser or tool claims.
- No fabricated external verification.
- Real evidence for browser audits.
- Separate commander and subordinate processes.
- Audits independently inspectable.
- Failed integrity checks block shipment.
- Live status exposes operational stages, not hidden chain-of-thought.
- Performance matters; do not repeat expensive passes when a cheaper design preserves the assurance property.

## Pending
Audit the Grok workspace before finalizing model choice, prompt strategy, data ingestion, spreadsheet transformations, memory model, benchmark design, UI, or deployment.