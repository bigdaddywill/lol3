# LOL3 Bid Pipeline Audit — 2026-09-19

## Implementation
Commit: \`254f33afed6806c23467d11172b51ae391d54579\`

Files:
- \`pipeline/bid_pipeline.py\`
- \`pipeline/__init__.py\`
- \`tests/test_bid_pipeline.py\`
- \`.github/workflows/bid-pipeline-smoke.yml\`
- \`README.md\`

## Verified source inventory
The repo's \`hi\` contractor export was parsed directly:
- 263 contractor records
- 13 Concrete & Masonry records
- 2 Concrete & Masonry records in Indiana
- Indiana Concrete & Masonry examples verified: Percrete and Carr Construction

Reference EML:
- 8 bid cards parsed
- Digest subject supplies the default market state when a card's Place field omits the state
- Original source score is preserved as \`score_source\`; it is not reused as LOL3's contractor score

## Automated audit
GitHub Actions workflow:
\`LOL3 bid pipeline smoke\`

Workflow run:
- run id: 35421452945
- head: 254f33afed6806c23467d11172b51ae391d54579
- conclusion: success

Passed steps:
1. Python 3.12 setup
2. 5/5 unit tests
3. Reference 8-bid end-to-end pipeline
4. Output invariants: 8 bids, 263 contractors, complete outreach objects
5. Artifact upload

## Semantic audit of produced artifact
State gate:
- Every selected contractor had state IN for an IN bid.
- No out-of-state contractor was retained after the state-gate fix.

Matches:
- Overlay Phase 2 — City of Columbus #26-10: Carr Construction, Percrete
- Bike and Pedestrian Facilities — Marquette Greenway: Carr Construction, Percrete
- Pavement Patching — LaPorte District: Carr Construction, Percrete
- Small Structure Replacement — Reinforced Concrete Boxes: Carr Construction, Percrete
- Camp Atterbury Covered Training Area Facility: Carr Construction, Percrete, Carrillos Construction, DND Construction
- Camp Atterbury 2026 Paving: Carr Construction, Percrete
- CGHS Renovations Package 2 — General Trades: Carr Construction, Percrete, Carrillos Construction, DND Construction
- Muscatatuck Building 5114 Maintenance and Repair: Carr Construction, Percrete, Carrillos Construction, DND Construction

Score pattern:
- Carr Construction and Percrete: 95 = 55 trade + 25 state + 10 scope + 5 email readiness
- Carrillos Construction and DND Construction: 58 = 28 general-building trade + 25 state + 0 scope + 5 email readiness

The 58-point matches are intentionally retained as medium-confidence building/general-trade fits rather than represented as proven concrete specialists.

## Safety / factuality audit
- No generated message states that a contractor is licensed, certified, prequalified, insured, or otherwise qualified unless the contractor source documents it.
- Qualification requirements from the bid source are preserved as unverified contractor facts.
- Every selected match has explicit score components and reasons.
- Source URL, bid deadline, scope, and location are propagated into outreach.
- Human approval remains the send gate.

## Important boundary
This is a functional reference-digest ingestion and matching system, not yet a production fleet of live source-specific scrapers. \`scrape_url()\` exists as a dependency-free HTTP adapter, but live procurement sites still need source-specific adapters and extraction tests.

## Next engineering target
Replace broad HTML/digest ingestion with adapters for the actual bid sources and add:
- source-specific freshness/open-status verification
- city/county distance or contractor service-area constraints
- richer trade/scope ontology
- deduplication across sources
- contact/channel validation
- persistent bid/contractor/message status tracking
- benchmark labels for match precision/recall


## LIVE SOURCE AUDIT UPDATE — 2026-09-19

### Indiana Armory Board adapter
- Adapter: `pipeline/live_sources.py`
- Endpoint: `https://www.in.gov/apps/sab/bidsystem/sab_bviewer`
- Parser fixture test: PASS.
- Live GitHub Actions run: `35421618318`
- Live result: PASS.
- The endpoint returned its real bid-posting table shell and explicitly reported `No Bids Posted at This Time` during the live run.
- This was initially treated as a parser failure; diagnostics established that the source was returning an empty current board, not malformed HTML or a bot/WAF response.
- The live smoke gate now distinguishes a valid empty source from an unexpected empty/invalid response.

### Final smoke status
Run `35421618318` at commit `ca19e382edd822a5ff63b4749ad18472564bbb93` completed successfully.
- Unit tests: PASS (6/6)
- Reference 8-bid E2E: PASS
- Output invariants: PASS
- Live Indiana Armory Board scrape: PASS
- Artifact upload: PASS

### Current boundary
The reference matching/outreach pipeline is verified end-to-end. One live public source adapter is verified and can correctly report a live empty board. The larger production scraper fleet still needs additional source adapters and a discovery strategy for sources whose public pages require authentication, dynamic sessions, or other access conditions.
