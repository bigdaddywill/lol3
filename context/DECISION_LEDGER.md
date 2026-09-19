# LOL3 Decision Ledger

D001 — GitHub is external working memory.
Reason: sessions have finite working context; GitHub survives boundaries and provides versioned evidence.
Status: ACTIVE

D002 — HOT_STATE is current truth; CHAT_LOG is history.
Reason: fresh sessions should not need to replay the entire transcript.
Status: ACTIVE

D003 — Evidence before confidence.
Reason: code existing or CI being green is not enough; runtime behavior and artifacts must be checked.
Status: ACTIVE

D004 — Same-state is a hard match gate in the current production flow.
Reason: prior audit exposed out-of-state false positives.
Status: ACTIVE

D005 — Concrete relevance is explicit, not generic substring similarity.
Reason: generic terms like construction, and, stone, HMA, and markings created false positives.
Status: ACTIVE

D006 — Historical digest data is fixture/provenance only.
Reason: old deadlines must never become false current opportunities.
Status: ACTIVE

D007 — Required and optional source health are distinct.
Reason: procurement sources can be dynamic, empty, authenticated, or degraded.
Status: ACTIVE

D008 — Human send gate remains mandatory.
Reason: qualification and final outreach approval remain human-controlled.
Status: ACTIVE

D009 — Audit artifacts are first-class evidence.
Reason: reproducibility, debugging, and cross-session continuity.
Status: ACTIVE

D010 — Execution state is separate from project memory.
Reason: multi-day work needs durable task ownership, checkpoints, leases, and recovery independent of a chat session.
Status: ACTIVE

D011 — Long-running work uses bounded resumable slices.
Reason: GitHub-hosted jobs are time-bounded; persisted checkpoints let work continue across many worker lifetimes.
Status: ACTIVE

D012 — Independent ChatGPT sessions communicate through immutable GitHub messages.
Reason: separate conversations have separate context windows; GitHub provides a durable synchronization boundary without requiring shared live memory.
Status: ACTIVE

D013 — Swarm roles are explicit and evidence is routed by role.
Reason: chief integration, building, auditing, research, and red-team work have different failure modes and should be independently represented.
Status: ACTIVE
