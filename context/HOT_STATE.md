# LOL3 Hot State

updated: 2026-09-19
repo: bigdaddywill/lol3
branch: main

## MISSION
Maintain the LOL3 swarm/control-plane experiments with durable GitHub context, evidence-first audits, and resumable coordination.

## CURRENT PHASE
PHANTOM_20_REAL_NUMBER_CHECKPOINT_SWARM

## ACTIVE SWARM MISSION
- mission_id: PHANTOM-20-REAL-NUMBER-001
- GitHub issue bus: #2
- target_sms_raw: 3059278198
- Target is preserved exactly; workers must not guess, normalize, truncate, or replace it.
- 20 role-specialized sessions are launched through `.github/workflows/20-phone-swarm-checkpoint.yml`; the hardened version requires two-way peer consumption.
- Communication channel: GitHub issue #2 comments.
- Durable mission files: `swarm/mission-20/MISSION.md`, `swarm/mission-20/ROLES.md`.
- Worker implementation: `tools/phone_swarm_worker.py`.

## SAFE EXECUTION BOUNDARY
- Agents may research provider rules, inspect signup paths, use isolated browser sessions, detect CAPTCHA/anti-bot checkpoints, communicate, and produce a final human handoff.
- The automation does NOT create third-party phone accounts, submit identity data, bypass CAPTCHA/anti-bot controls, or send the final SMS.
- Overall experiment is not successful until the user confirms receipt of the SMS after any human-controlled final step.

## CURRENT PROVIDER EVIDENCE
- TextFree currently advertises a free, dialable U.S./Canadian number and free calling/texting; its official site says the free number stays active with use at least every 30 days.
- TextFree's free tier does not include verification-code support; Plus adds that feature.
- TextFree currently says new accounts are created through the app and that service is for U.S./Canadian residents while physically in those countries.
- TextNow and Talkatone remain alternate candidates to be rechecked by the swarm.
These are externally verified findings and must be rechecked in-run for current accuracy.

## ACTIVE AUDIT RULE
No victory claim until:
1. 20/20 worker evidence is observed and integrated;
2. cross-agent communication is evidenced;
3. browser/provider findings are audited for contradictions;
4. final handoff state is explicit;
5. no unresolved defects or suggestions remain in the implementation;
6. user confirms receipt of the final SMS after any human-controlled action.

## 48-SESSION HISTORY
The earlier 48-worker infrastructure proof remains historical evidence. Its last known hardened state used a 15-second worker hold; its corrected concurrency result had not yet been persisted at the time of this state rewrite. Do not treat the provisional overlap=1 measurement as final concurrency evidence.

## LONG-TERM MEMORY
- `context/FACT_LEDGER.md`
- `context/DECISION_LEDGER.md`
- `context/FAILURE_LEDGER.md`
- `context/RESTART.md`
- `context/CHAT_LOG.md`
- `context/BENCHMARK_HISTORY.md`
- `context/ARCHITECTURE.md`
- `agent/QUEUE.json`
- `agent/STATE.json`
- `agent/LEDGER.md`

Update this file only from verified reality.