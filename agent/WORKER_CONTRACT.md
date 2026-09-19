# LOL3 Worker Contract

This is the contract between an execution runtime and the persistent brain.

## Start a slice

```bash
python tools/agent_supervisor.py claim --worker-id <unique-worker-id>
```

If it returns `NO_READY_TASK`, the worker is idle.

If it returns a task, keep the returned `task.id` and checkpoint frequently.

## Checkpoint

```bash
python tools/agent_supervisor.py checkpoint \
  --task-id <task-id> \
  --worker-id <unique-worker-id> \
  --detail "exactly what is complete and what remains"
```

Checkpoint text must be sufficient for a fresh worker to continue without replaying the previous process.

## Complete

```bash
python tools/agent_supervisor.py finish \
  --task-id <task-id> \
  --worker-id <unique-worker-id> \
  --result "verification evidence and final state"
```

## Fail

Temporary failure:

```bash
python tools/agent_supervisor.py fail \
  --task-id <task-id> \
  --worker-id <unique-worker-id> \
  --error "what failed and why"
```

Terminal failure:

```bash
python tools/agent_supervisor.py fail \
  --task-id <task-id> \
  --worker-id <unique-worker-id> \
  --error "terminal reason" \
  --no-retry
```

## Persistence

After changing `agent/STATE.json`, `agent/QUEUE.json`, or `agent/LEDGER.md`, the worker must persist the change to Git.

A recommended single-worker cycle is:

1. pull/rebase latest `main`;
2. claim;
3. commit the claim;
4. do bounded work;
5. checkpoint;
6. commit the checkpoint;
7. repeat;
8. finish/fail;
9. commit final state.

A rejected Git push means the worker lost the optimistic concurrency race. It must pull/rebase, re-read state, and never assume its claim survived.

## Resume

After process or machine death:

1. pull `main`;
2. read `context/HOT_STATE.md`;
3. read `agent/QUEUE.json`;
4. read `agent/STATE.json`;
5. continue from the active task's checkpoint;
6. run the watchdog if a lease is stale.

The worker must never "start from memory" when durable state exists.

## Long-running behavior

The worker should prefer many short, auditable slices over one giant operation. A 30-hour mission is therefore a sequence of independently recoverable slices, not a 30-hour fragile process.

The model/runtime can change between slices. The mission survives.
