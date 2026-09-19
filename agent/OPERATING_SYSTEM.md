# LOL3 Persistent Executor Brain

## Purpose

The memory layer preserves knowledge. This layer preserves **work in motion**.

It is designed so a worker can operate in bounded slices for hours or days without requiring one chat session to remain alive.

## Core model

`CHAT/MODEL` -> `TASK QUEUE` -> `WORK SLICE` -> `CHECKPOINT` -> `GIT` -> `NEXT SLICE`

GitHub is the durable control plane:
- `agent/QUEUE.json` = what needs doing.
- `agent/STATE.json` = what is happening now.
- `agent/LEDGER.md` = append-only operational history.
- `context/HOT_STATE.md` = project truth.
- `context/*_LEDGER.md` = durable reasoning/history.

## Work-slice contract

A worker MUST:
1. Claim one task.
2. Acquire a lease with a deadline.
3. Record a checkpoint before expensive work.
4. Emit another checkpoint after every meaningful unit.
5. Finish, fail, or release the task explicitly.
6. Persist important state before the slice exits.

A slice MUST be bounded. A dead worker must never leave the task permanently locked.

## Recovery contract

If a task lease is older than its lease deadline:
- mark the previous worker attempt stale;
- increment the recovery counter;
- return the task to READY unless its retry budget is exhausted;
- preserve the previous checkpoint and error.

Recovery is deterministic. No work is silently discarded.

## No fake progress

The system distinguishes:
- READY
- RUNNING
- BLOCKED
- COMPLETE
- FAILED

A task is not considered complete because code exists. Completion requires the task's declared verification evidence.

## Worker boundary

The brain does not assume a particular model or runtime.

A worker may be:
- a local 3B model on an always-on machine;
- a self-hosted GitHub runner;
- a cloud runner;
- a future model/tool driver.

The worker only needs to implement the task protocol.

This is deliberate: the same brain can survive a process restart, model swap, machine swap, or chat-session boundary.

## Human safety gate

External communications remain human-controlled. The persistent executor may prepare drafts, queues, audits, and recommendations, but it must not silently send outbound messages.

## Multi-day operation

GitHub-hosted jobs are bounded, so multi-day operation is achieved through **many resumable slices**, not one immortal process. GitHub documents a 6-hour maximum for hosted jobs and scheduled workflows can run as frequently as every 5 minutes. A self-hosted runner can keep the worker process alive for longer, subject to its own limits and credential lifetime.

The important invariant is:

**time does not equal state. State lives in GitHub.**

## Cold resume

A fresh worker should read:
1. `context/HOT_STATE.md`
2. `context/FACT_LEDGER.md`
3. `context/DECISION_LEDGER.md`
4. `context/FAILURE_LEDGER.md`
5. `context/RESTART.md`
6. `agent/QUEUE.json`
7. `agent/STATE.json`
8. the active task's latest checkpoint

That is enough to resume without replaying the whole chat.
