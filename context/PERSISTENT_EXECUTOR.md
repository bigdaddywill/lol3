# Persistent Executor Brain

## What changed

LOL3 now separates two problems:

1. **Memory:** what the system knows.
2. **Execution state:** what the system is currently doing.

The memory architecture already solved the first problem. The persistent executor layer addresses the second.

## New control files

- `agent/QUEUE.json` — durable work queue.
- `agent/STATE.json` — active worker state, lease, checkpoint, and recovery counters.
- `agent/LEDGER.md` — operational event history.
- `tools/agent_supervisor.py` — task/lease/checkpoint state machine.
- `.github/workflows/agent-brain-audit.yml` — watchdog/self-test.

## Why this matters

A multi-day task must be sliced into bounded units. A single chat session or GitHub-hosted job should never be treated as the source of truth.

A future worker can:
- claim a task;
- work for a bounded slice;
- checkpoint;
- persist results;
- exit;
- restart later;
- detect and recover stale work;
- continue from the last checkpoint.

That removes the biggest failure mode of long autonomous work: **losing the exact point of progress when the runtime dies.**

## What this does not magically do

It does not make a chat session itself immortal.

An actual multi-day autonomous worker still needs an execution engine running somewhere, such as a self-hosted runner or another always-on machine/process. The brain is designed so swapping that worker does not lose the mission state.

## Target architecture

`Phantom / model`
      |
      v
`QUEUE`
      |
      v
`worker slice`
      |
      +--> checkpoint
      |
      +--> evidence
      |
      v
`STATE + LEDGER`
      |
      v
`Git commit`
      |
      v
`next slice`

## Non-negotiable invariants

- No silent loss of progress.
- No stale lease blocking the queue forever.
- No completion without evidence.
- No automatic outbound sending.
- No rewriting current truth to fit an old assumption.
