# LOL3 Failure Ledger

F001 — Display text was lowercased.
Root cause: matching normalization was reused for display.
Fix: separate display cleaning from normalization.
Status: SOLVED

F002 — Contractor company was missing from outreach.
Root cause: template used only first name.
Fix: company personalization + output checks.
Status: SOLVED

F003 — Out-of-state contractor false positives.
Root cause: trade fit was allowed without geographic gating.
Fix: hard same-state gate + regression test.
Status: SOLVED

F004 — Generic category substring false positives.
Root cause: noisy vocabularies and raw substring matching.
Fix: stopwords removed; strict Concrete mode.
Status: SOLVED

F005 — HMA / pavement-marking false positives.
Root cause: overly broad infrastructure vocabulary.
Fix: removed broad pavement terms; added negative tests.
Status: SOLVED

F006 — INDOT deadlines disappeared from live records.
Root cause: PDF extraction did not reliably retain letting header.
Fix: authoritative letting-page date/time is the deadline baseline.
Status: SOLVED

F007 — Smoke CI missed Python dependencies.
Root cause: workflow ran tests without requirements.txt.
Fix: install dependencies before tests.
Status: SOLVED

F008 — Durable context contained stale active blockers.
Root cause: context was append-heavy with no hot/warm/cold hierarchy.
Fix: memory architecture upgrade with HOT_STATE and ledgers.
Status: SOLVED BY MEMORY UPGRADE

F009 — Long work was previously session-bound.
Root cause: durable memory existed, but no durable representation of in-flight work, ownership, checkpoints, or stale-worker recovery.
Fix: persistent executor with queue, lease, checkpoint, watchdog, and recovery protocol.
Status: SOLVED BY EXECUTOR LAYER; END-TO-END WORKER TEST PENDING
