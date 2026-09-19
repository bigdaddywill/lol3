# ChatGPT Session Swarm Protocol

## 1. Agent identity

Every session has a stable ID:

`PHANTOM-CHIEF`
`PHANTOM-BUILDER`
`PHANTOM-AUDITOR`
`PHANTOM-RESEARCHER`
`PHANTOM-REDTEAM`

A session must never impersonate another agent.

## 2. Message format

Each message is one immutable Markdown file under:

`swarm/inbox/<recipient>/<message-id>.md`

The filename must be unique.

Required header fields:

- message_id
- from
- to
- mission_id
- type
- created_at_utc
- in_reply_to
- priority
- status

Then:

`## Payload`

The payload must state the actual information, request, result, or disagreement.

Then:

`## Evidence`

Use repository paths, commit SHAs, test IDs, or URLs where applicable.

## 3. Message types

- `TASK` — do this work.
- `QUESTION` — answer this.
- `RESULT` — completed work.
- `EVIDENCE` — factual support.
- `CHALLENGE` — challenge an assumption/result.
- `BLOCKED` — cannot continue without something.
- `HANDOFF` — another agent should continue.
- `CHECKPOINT` — durable in-progress state.
- `DECISION_REQUEST` — needs integration-level decision.
- `DECISION` — recorded decision.

## 4. Evidence hierarchy

Prefer:

1. Runtime/test output
2. GitHub artifact or commit
3. Primary external source
4. Reproducible calculation
5. Reasoned inference

Do not present an inference as evidence.

## 5. Conversation behavior

Agents should be concise in their messages and detailed in repository artifacts.

A good swarm message answers:

- What happened?
- What did you inspect?
- What did you find?
- What remains uncertain?
- What should the next agent do?

## 6. Conflict handling

Disagreement is first-class.

An agent must send `CHALLENGE` rather than silently editing away another agent's conclusion.

The Chief resolves integration disputes by evidence, not by message count.

## 7. No false completion

A `RESULT` message is not a claim of victory.

Completion requires the declared verification evidence.

## 8. Session death

Before ending or losing context, a session should send:

`CHECKPOINT` with:
- current task
- completed work
- exact next step
- relevant files
- known failures
- unresolved questions

A new session can then resume.

## 9. Loop control

The Chief should prevent circular agent conversations.

Every work chain should have:
- a mission ID;
- a root task;
- a current owner;
- a next action;
- a stopping condition.

## 10. Human gate

External side effects that matter to the user remain human-controlled unless explicitly authorized.
