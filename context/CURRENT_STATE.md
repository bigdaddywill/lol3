# LOL3 Current State

## Identity
- User: Ghost
- Assistant/project handle: Phantom
- Repository: bigdaddywill/lol3
- Default branch: main
- Visibility: public
- Permissions: admin / maintain / push

## Mission
Continue the AI/automation work in lol3, preserve durable context, inspect the Grok workspace and spreadsheet, then build/refine/benchmark the actual system represented by those artifacts.

## Uploaded artifacts
1. Bs0DhhjMBGFJgTHV-grok-workspace.zip
   Latest commit: d1bd76fb81caa7f160a4c13873eaa9b96eedb378
2. Spanish_cleaned_after_152_on_Leads_Magnet.xlsx
   Latest commit: 69d7f1404d87ddfe6a4be2e74793127f32dceaf8

## Current repository history
No LOL3 application code has been found yet; the visible history currently consists of the two artifact uploads above.

## Inherited LOL2 architecture
- Qwen 3B commander
- separate Qwen 3B subordinate/auditor
- real Gemini Web through Playwright/Chromium
- two fresh browser passes per audit
- screenshots and SHA-256 hashes
- PASS / REVISE gate
- commander revision after REVISE
- failed integrity checks block shipment
- 7B excluded for speed
- live progress and durable GitHub context

## Important Windows context
Ghost's Windows repo path was C:\Users\ghost\Downloads\lol2\lol2-main.
Python 3.12.10 was available.
llama.cpp was installed through WinGet.
llama-server.exe was located under the WinGet package directory.
The launcher reached 'Starting commander 3B...' and 'Starting independent auditor 3B...' but startup was unusually slow and empty log output had not yet been diagnosed when focus moved to lol3.

## Immediate next steps
1. Materialize and extract the Grok workspace if possible.
2. Inventory its files and implementation.
3. Inspect the XLSX with the spreadsheet tooling.
4. Map the intended workflow and data flow.
5. Audit Grok's implementation for correctness, performance, and gaps.
6. Build/refine lol3 from the strongest verified pieces.
7. Add tests, live status, and benchmark harnesses.
8. Persist all results here.

## BID PIPELINE IMPLEMENTATION UPDATE — 2026-09-19
- Confirmed repo file `hi` is a readable TSV contractor export; parsed 263 contractor records.
- Confirmed 13 Concrete & Masonry contractors overall and 2 in Indiana: Percrete and Carr Construction.
- Built `pipeline/bid_pipeline.py` for EML digest parsing, contractor normalization, evidence-based matching, bid invitation/email/SMS generation, and a dependency-free URL fetch adapter.
- Added 5 regression tests and GitHub Actions smoke coverage.
- First audit caught two defects (display text lowercasing and missing company name), both fixed.
- Second audit caught a material false-positive class: out-of-state trade matches. Added a strict state gate and digest-subject state fallback; all selected matches are now state-consistent.
- Successful smoke run: 35421452945 at commit 254f33afed6806c23467d11172b51ae391d54579.
- Detailed audit: `context/PIPELINE_AUDIT_2026-09-19.md`.
- Production status: reference pipeline functional; live source-specific scraping and geographic/service-area verification remain next-stage work.


## LIVE SOURCE UPDATE — 2026-09-19
- Added `pipeline/live_sources.py` with an Indiana Armory Board adapter and regression fixture.
- Added live source validation to the smoke workflow.
- Diagnostic run showed the public SAB endpoint returned a 620-byte valid HTML shell with `No Bids Posted at This Time`; browser-like headers did not change that.
- The gate was corrected to treat an explicitly verified empty source as a valid scrape result instead of falsely declaring a parser failure.
- Final smoke run `35421618318` at commit `ca19e382edd822a5ff63b4749ad18472564bbb93` passed all 6 tests, reference E2E, output invariants, live source check, and artifact upload.


## FINAL PRODUCTION STATE — 2026-09-19

LOL3 is finalized for the audited Concrete/Indiana production path.

Audited source commit: `f8f768ba97534e7cddca9013598bae5c0af86a8c`
Final documentation-freeze commit: `5a11b22fa331b149b4b79466a00a0751c32fd5eb`

Final verified gates:
- Production audit run `35422565481`: SUCCESS
- Standalone smoke run `35422611533`: SUCCESS
- Final smoke suite: 17/17 tests
- Final production artifact: 50 email-ready + 50 SMS-ready current bid/contractor pairs

Current live sourcing:
- Required INDOT source: 39 current contracts parsed.
- Concrete relevance filter retained 25 current INDOT bids.
- Historical Aug. 23 digest fixture retained for provenance but excluded from current outreach because its deadlines are closed.
- SAB is optional/degraded in the Actions environment and is excluded rather than trusted when its response is not parseable.
- Public Purchase is optional.

Current contractor source:
- 264 rows loaded from On Leads Magnet.
- 1 duplicate removed.
- 2 missing business names recovered from alternate identity fields.
- 0 unidentifiable rows.
- 2 Indiana Concrete/Masonry contractors are in the final production candidate pool: Percrete and Carr Construction.

Final matching contract:
- trade focus is concrete
- contractor category must document Concrete or Masonry
- bid must contain concrete-relevant scope evidence
- bid and contractor must share state
- open deadline is required before email/SMS readiness

Final outreach contract:
- 50 current pairings
- 50 email-ready
- 50 SMS-ready
- 0 validation errors
- human send gate remains `HUMAN_REVIEW_REQUIRED`
- no unsupported licensing/certification/insurance/prequalification claims

Final durable audit: `context/FINAL_AUDIT_2026-09-19.md`
