# LOL3 ChatGPT Session Swarm

GitHub is the shared nervous system for a swarm of independent ChatGPT sessions.

## What this is

Each ChatGPT conversation becomes a named agent. Agents do not need to share context windows.

They communicate through versioned GitHub artifacts:

- `swarm/agents/` — agent identities and roles.
- `swarm/inbox/` — durable messages addressed to a specific agent.
- `swarm/board/` — shared mission state and evidence.
- `swarm/ROUTER.md` — routing and conversation rules.
- `swarm/PROTOCOL.md` — exact message protocol.
- `swarm/TRANSCRIPTS.md` — compact swarm-level history.

## The mental model

`ChatGPT Session A`
       |
       | message/evidence
       v
`GitHub`
       ^
       | message/evidence
       |
`ChatGPT Session B`

GitHub is not merely storage. It is the synchronization boundary.

## Recommended swarm

- `PHANTOM-CHIEF` — decomposes missions and integrates results.
- `PHANTOM-BUILDER` — implements code.
- `PHANTOM-AUDITOR` — tries to break the work and finds defects.
- `PHANTOM-RESEARCHER` — gathers external evidence.
- `PHANTOM-REDTEAM` — attacks assumptions and proposed designs.

These are roles, not personalities. Any ChatGPT session can assume any role.

## How a new session joins

1. Read `context/HOT_STATE.md`.
2. Read `swarm/ROUTER.md`.
3. Read your agent profile under `swarm/agents/`.
4. Read your inbox.
5. Read `swarm/board/BLACKBOARD.md`.
6. Claim or receive work.
7. Send durable messages instead of relying on conversation history.
8. Before leaving, write a checkpoint/result message.

## Critical limitation

The protocol can coordinate independent ChatGPT sessions, but the available tooling does not give one ChatGPT session a native API to create or control other ChatGPT UI conversations. The sessions must exist separately and connect to the same GitHub repo.

That limitation does not weaken the protocol: the swarm's state, messages, evidence, and checkpoints survive session boundaries.

## Goal

Make the session boundary irrelevant to collaboration.

A session can disappear. Another can continue from GitHub.
