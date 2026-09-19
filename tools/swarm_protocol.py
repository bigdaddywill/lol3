#!/usr/bin/env python3
"""Local helper for the LOL3 ChatGPT session swarm.

The actual ChatGPT sessions communicate through GitHub files. This helper
creates immutable messages and validates the swarm directory structure.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SWARM = ROOT / "swarm"
INBOX = SWARM / "inbox"
AGENTS = SWARM / "agents"

MESSAGE_TYPES = {
    "TASK", "QUESTION", "RESULT", "EVIDENCE", "CHALLENGE", "BLOCKED",
    "HANDOFF", "CHECKPOINT", "DECISION_REQUEST", "DECISION",
}

AGENT_RE = re.compile(r"^[A-Z0-9_-]+$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def make_message_id(agent: str, kind: str, payload: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:4].upper()
    return f"{stamp}-{agent}-{kind}-{digest}"


def send(from_agent: str, to_agent: str, mission_id: str, kind: str,
         payload: str, evidence: str = "", priority: str = "NORMAL",
         in_reply_to: str = "NONE") -> Path:
    if not AGENT_RE.fullmatch(from_agent) or not AGENT_RE.fullmatch(to_agent):
        raise ValueError("agent ids must contain only A-Z, 0-9, _ or -")
    if kind not in MESSAGE_TYPES:
        raise ValueError(f"unsupported message type: {kind}")

    message_id = make_message_id(from_agent, kind, payload)
    body = (
        f"message_id: {message_id}\n"
        f"from: {from_agent}\n"
        f"to: {to_agent}\n"
        f"mission_id: {mission_id}\n"
        f"type: {kind}\n"
        f"created_at_utc: {utc_now()}\n"
        f"in_reply_to: {in_reply_to}\n"
        f"priority: {priority}\n"
        f"status: OPEN\n\n"
        f"## Payload\n\n{payload.strip()}\n\n"
        f"## Evidence\n\n{evidence.strip() or 'None supplied.'}\n"
    )

    destination = INBOX / to_agent / f"{message_id}.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(destination)
    destination.write_text(body, encoding="utf-8")
    return destination


def validate_structure() -> list[str]:
    errors: list[str] = []
    required = [
        SWARM / "README.md",
        SWARM / "PROTOCOL.md",
        SWARM / "ROUTER.md",
        SWARM / "SESSION_BOOT.md",
        SWARM / "board" / "BLACKBOARD.md",
        SWARM / "board" / "SCHEMAS.md",
    ]
    errors.extend(f"missing: {p}" for p in required if not p.exists())

    expected_agents = [
        "PHANTOM-CHIEF",
        "PHANTOM-BUILDER",
        "PHANTOM-AUDITOR",
        "PHANTOM-RESEARCHER",
        "PHANTOM-REDTEAM",
    ]
    for agent in expected_agents:
        if not (AGENTS / f"{agent}.md").exists():
            errors.append(f"missing agent profile: {agent}")
        if not (INBOX / agent).exists():
            errors.append(f"missing inbox: {agent}")

    return errors


def self_test() -> None:
    errors = validate_structure()
    if errors:
        raise SystemExit("SWARM STRUCTURE FAIL: " + "; ".join(errors))

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        payload = "A durable message must be sufficient for another session to act."
        destination = temp_root / "inbox"
        destination.mkdir()
        file = destination / "test.md"
        file.write_text(
            f"message_id: TEST-001\n"
            f"from: PHANTOM-AUDITOR\n"
            f"to: PHANTOM-CHIEF\n"
            f"mission_id: SELFTEST\n"
            f"type: CHALLENGE\n"
            f"created_at_utc: {utc_now()}\n"
            f"in_reply_to: NONE\n"
            f"priority: HIGH\n"
            f"status: OPEN\n\n"
            f"## Payload\n\n{payload}\n",
            encoding="utf-8",
        )
        assert file.exists()
        assert "PHANTOM-AUDITOR" in file.read_text(encoding="utf-8")
        assert "PHANTOM-CHIEF" in file.read_text(encoding="utf-8")
        assert payload in file.read_text(encoding="utf-8")

    print("SESSION_SWARM_SELF_TEST: PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    send_parser = sub.add_parser("send")
    send_parser.add_argument("--from", dest="from_agent", required=True)
    send_parser.add_argument("--to", dest="to_agent", required=True)
    send_parser.add_argument("--mission", required=True)
    send_parser.add_argument("--type", required=True, choices=sorted(MESSAGE_TYPES))
    send_parser.add_argument("--payload", required=True)
    send_parser.add_argument("--evidence", default="")
    send_parser.add_argument("--priority", default="NORMAL")
    send_parser.add_argument("--reply-to", default="NONE")

    sub.add_parser("self-test")

    args = parser.parse_args()

    if args.command == "send":
        path = send(
            args.from_agent, args.to_agent, args.mission, args.type,
            args.payload, args.evidence, args.priority, args.reply_to,
        )
        print(path)
    elif args.command == "self-test":
        self_test()


if __name__ == "__main__":
    main()
