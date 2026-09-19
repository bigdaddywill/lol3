# Swarm Router

## Boot sequence for every ChatGPT session

Read in this order:

1. `context/HOT_STATE.md`
2. `swarm/README.md`
3. `swarm/PROTOCOL.md`
4. your `swarm/agents/<agent-id>.md`
5. your inbox under `swarm/inbox/<agent-id>/`
6. `swarm/board/BLACKBOARD.md`

Then inspect the specific code/files required for the assigned task.

## Routing rules

### Chief
Receives:
- TASK requests
- DECISION_REQUEST
- major CHALLENGE
- final RESULT messages

Sends:
- decomposition TASKs
- clarifications
- integration decisions
- handoffs

### Builder
Receives:
- implementation TASKs
- audit findings requiring fixes

Sends:
- RESULT
- CHECKPOINT
- BLOCKED
- EVIDENCE

### Auditor
Receives:
- audit TASKs
- RESULTs worth independently validating

Sends:
- CHALLENGE
- EVIDENCE
- BLOCKED
- RESULT

### Researcher
Receives:
- research QUESTIONS
- source verification TASKs

Sends:
- EVIDENCE
- RESULT
- uncertainty notes

### Red Team
Receives:
- CHALLENGE/AUDIT tasks
- proposed architectures

Sends:
- CHALLENGE
- RESULT
- EVIDENCE
- failure scenarios

## Message naming

Use:

`<utc>-<from>-<type>-<short-id>.md`

Example:

`20260919T060000Z-PHANTOM-AUDITOR-CHALLENGE-A17F.md`

## Shared blackboard

Only the Chief or an explicitly designated owner should rewrite canonical sections of `swarm/board/BLACKBOARD.md`.

Agents contribute through messages and evidence files.

## Avoiding collisions

Prefer immutable message files over editing a shared mailbox file.

Do not append to one shared JSON file from multiple sessions.

When changing shared state, re-read the current file and require its latest blob SHA.
