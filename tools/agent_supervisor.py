#!/usr/bin/env python3
"""Persistent executor state machine for LOL3.

This module intentionally does not embed a specific LLM. It provides the
durable task/lease/checkpoint protocol that any worker can use.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / "agent"
STATE_PATH = AGENT_DIR / "STATE.json"
QUEUE_PATH = AGENT_DIR / "QUEUE.json"
LEDGER_PATH = AGENT_DIR / "LEDGER.md"

VALID_PHASES = {"IDLE", "RUNNING", "BLOCKED", "COMPLETE", "FAILED"}
VALID_TASK_STATES = {"READY", "RUNNING", "BLOCKED", "COMPLETE", "FAILED"}

DEFAULT_LEASE_SECONDS = 15 * 60


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat().replace("+00:00", "Z") if dt else None


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        tmp_path.replace(path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def append_ledger(event: str, task_id: str | None, worker_id: str | None,
                  detail: str = "") -> None:
    stamp = iso(now_utc())
    line = f"- {stamp} | task={task_id or '-'} | worker={worker_id or '-'} | {event}"
    if detail:
        line += f" | {detail}"
    ledger_path = Path(os.environ.get("LOL3_LEDGER_PATH", str(LEDGER_PATH)))
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def validate_state(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if state.get("schema_version") != 1:
        errors.append("STATE schema_version must be 1")
    if state.get("phase") not in VALID_PHASES:
        errors.append("STATE phase is invalid")
    if state.get("slice_count", 0) < 0:
        errors.append("STATE slice_count cannot be negative")
    if state.get("recovery_count", 0) < 0:
        errors.append("STATE recovery_count cannot be negative")
    return errors


def validate_queue(queue: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if queue.get("schema_version") != 1:
        errors.append("QUEUE schema_version must be 1")
    if not isinstance(queue.get("tasks"), list):
        errors.append("QUEUE tasks must be a list")
        return errors

    seen: set[str] = set()
    for index, task in enumerate(queue["tasks"]):
        prefix = f"task[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{prefix} must be an object")
            continue
        task_id = task.get("id")
        if not task_id:
            errors.append(f"{prefix} missing id")
        elif task_id in seen:
            errors.append(f"duplicate task id: {task_id}")
        else:
            seen.add(task_id)

        if task.get("state") not in VALID_TASK_STATES:
            errors.append(f"{prefix} has invalid state")
        if not task.get("title"):
            errors.append(f"{prefix} missing title")
    return errors


def recover_stale_leases(state: dict[str, Any], queue: dict[str, Any]) -> int:
    recovered = 0
    now = now_utc()
    for task in queue["tasks"]:
        if task.get("state") != "RUNNING":
            continue
        lease = parse_iso(task.get("lease_expires_at"))
        if not lease or lease >= now:
            continue

        task["state"] = "READY"
        task["worker_id"] = None
        task["lease_expires_at"] = None
        task["attempts"] = int(task.get("attempts", 0)) + 1
        task["last_recovery_at"] = iso(now)
        task["last_error"] = "stale lease recovered"

        state["recovery_count"] = int(state.get("recovery_count", 0)) + 1
        state["active_task_id"] = None
        state["worker_id"] = None
        state["lease_expires_at"] = None
        state["phase"] = "IDLE"

        append_ledger("STALE_LEASE_RECOVERED", task.get("id"), None)
        recovered += 1

    return recovered


def claim_next_task(state: dict[str, Any], queue: dict[str, Any],
                    worker_id: str, lease_seconds: int = DEFAULT_LEASE_SECONDS) -> dict[str, Any] | None:
    recover_stale_leases(state, queue)

    ready = [t for t in queue["tasks"] if t.get("state") == "READY"]
    if not ready:
        state["phase"] = "IDLE"
        state["active_task_id"] = None
        state["worker_id"] = None
        state["lease_expires_at"] = None
        state["last_heartbeat_at"] = iso(now_utc())
        return None

    ready.sort(key=lambda t: (-int(t.get("priority", 0)), t.get("created_at", ""), t["id"]))
    task = ready[0]

    now = now_utc()
    task["state"] = "RUNNING"
    task["worker_id"] = worker_id
    task["lease_expires_at"] = iso(now + timedelta(seconds=lease_seconds))
    task["attempts"] = int(task.get("attempts", 0)) + 1
    task["last_started_at"] = iso(now)

    state["phase"] = "RUNNING"
    state["active_task_id"] = task["id"]
    state["worker_id"] = worker_id
    state["lease_expires_at"] = task["lease_expires_at"]
    state["last_heartbeat_at"] = iso(now)
    state["last_checkpoint_at"] = iso(now)
    state["last_checkpoint"] = task.get("checkpoint")
    state["slice_count"] = int(state.get("slice_count", 0)) + 1

    append_ledger("CLAIM", task["id"], worker_id, task.get("title", ""))
    return task


def checkpoint(state: dict[str, Any], queue: dict[str, Any], task_id: str,
               worker_id: str, detail: str) -> None:
    for task in queue["tasks"]:
        if task.get("id") == task_id:
            if task.get("state") != "RUNNING" or task.get("worker_id") != worker_id:
                raise RuntimeError("checkpoint rejected: worker does not own running task")
            now = now_utc()
            task["checkpoint"] = detail
            task["last_checkpoint_at"] = iso(now)
            task["lease_expires_at"] = iso(now + timedelta(seconds=DEFAULT_LEASE_SECONDS))
            state["last_checkpoint_at"] = iso(now)
            state["last_checkpoint"] = detail
            state["lease_expires_at"] = task["lease_expires_at"]
            state["last_heartbeat_at"] = iso(now)
            append_ledger("CHECKPOINT", task_id, worker_id, detail)
            return
    raise KeyError(f"unknown task: {task_id}")


def finish(state: dict[str, Any], queue: dict[str, Any], task_id: str,
           worker_id: str, result: str) -> None:
    for task in queue["tasks"]:
        if task.get("id") == task_id:
            if task.get("state") != "RUNNING" or task.get("worker_id") != worker_id:
                raise RuntimeError("finish rejected: worker does not own running task")
            now = now_utc()
            task["state"] = "COMPLETE"
            task["result"] = result
            task["completed_at"] = iso(now)
            task["lease_expires_at"] = None
            task["worker_id"] = None
            state["phase"] = "COMPLETE"
            state["active_task_id"] = None
            state["worker_id"] = None
            state["lease_expires_at"] = None
            state["last_heartbeat_at"] = iso(now)
            state["last_checkpoint_at"] = iso(now)
            state["last_checkpoint"] = result
            append_ledger("COMPLETE", task_id, worker_id, result)
            return
    raise KeyError(f"unknown task: {task_id}")


def fail(state: dict[str, Any], queue: dict[str, Any], task_id: str,
         worker_id: str, error: str, retry: bool = True) -> None:
    for task in queue["tasks"]:
        if task.get("id") == task_id:
            if task.get("state") != "RUNNING" or task.get("worker_id") != worker_id:
                raise RuntimeError("fail rejected: worker does not own running task")
            now = now_utc()
            task["state"] = "READY" if retry else "FAILED"
            task["last_error"] = error
            task["last_failed_at"] = iso(now)
            task["lease_expires_at"] = None
            task["worker_id"] = None
            state["phase"] = "IDLE" if retry else "FAILED"
            state["active_task_id"] = None
            state["worker_id"] = None
            state["lease_expires_at"] = None
            state["last_error"] = error
            state["last_heartbeat_at"] = iso(now)
            append_ledger("FAIL_RETRY" if retry else "FAIL_TERMINAL", task_id, worker_id, error)
            return
    raise KeyError(f"unknown task: {task_id}")


def self_test() -> None:
    for path in (STATE_PATH, QUEUE_PATH, LEDGER_PATH):
        if not path.exists():
            raise AssertionError(f"missing executor file: {path}")

    state = load_json(STATE_PATH)
    queue = load_json(QUEUE_PATH)

    errors = validate_state(state) + validate_queue(queue)
    if errors:
        raise AssertionError("; ".join(errors))

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        old_ledger_override = os.environ.get("LOL3_LEDGER_PATH")
        os.environ["LOL3_LEDGER_PATH"] = str(tmp_path / "ledger.md")
        test_state = {
            "schema_version": 1,
            "phase": "IDLE",
            "active_task_id": None,
            "worker_id": None,
            "lease_expires_at": None,
            "last_heartbeat_at": None,
            "last_checkpoint_at": None,
            "last_checkpoint": None,
            "slice_count": 0,
            "recovery_count": 0,
            "last_error": None,
            "safe_stop": False,
        }
        test_queue = {
            "schema_version": 1,
            "tasks": [{
                "id": "SELFTEST-001",
                "title": "executor protocol self-test",
                "state": "READY",
                "priority": 100,
                "created_at": "2026-01-01T00:00:00Z",
                "checkpoint": None,
                "attempts": 0,
            }]
        }

        claimed = claim_next_task(test_state, test_queue, "selftest", lease_seconds=900)
        assert claimed and claimed["state"] == "RUNNING"
        checkpoint(test_state, test_queue, "SELFTEST-001", "selftest", "checkpoint survives")
        finish(test_state, test_queue, "SELFTEST-001", "selftest", "complete survives")

        assert test_queue["tasks"][0]["state"] == "COMPLETE"
        assert test_state["active_task_id"] is None

        stale_state = dict(test_state)
        stale_queue = {
            "schema_version": 1,
            "tasks": [{
                "id": "SELFTEST-STALE",
                "title": "stale lease recovery",
                "state": "RUNNING",
                "priority": 1,
                "created_at": "2026-01-01T00:00:00Z",
                "worker_id": "dead-worker",
                "lease_expires_at": "2000-01-01T00:00:00Z",
                "attempts": 1,
            }]
        }
        recovered = recover_stale_leases(stale_state, stale_queue)
        assert recovered == 1
        assert stale_queue["tasks"][0]["state"] == "READY"
        assert stale_state["recovery_count"] == 1

        if old_ledger_override is None:
            os.environ.pop("LOL3_LEDGER_PATH", None)
        else:
            os.environ["LOL3_LEDGER_PATH"] = old_ledger_override

    print("AGENT_BRAIN_SELF_TEST: PASS")


def cmd_claim(worker_id: str) -> None:
    state = load_json(STATE_PATH)
    queue = load_json(QUEUE_PATH)
    errors = validate_state(state) + validate_queue(queue)
    if errors:
        raise SystemExit("VALIDATION_ERROR: " + "; ".join(errors))
    task = claim_next_task(state, queue, worker_id)
    save_json(STATE_PATH, state)
    save_json(QUEUE_PATH, queue)
    if task:
        print(json.dumps(task, indent=2))
    else:
        print("NO_READY_TASK")


def cmd_self_test() -> None:
    self_test()


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    claim_parser = sub.add_parser("claim")
    claim_parser.add_argument("--worker-id", default=os.environ.get("AGENT_WORKER_ID", "worker"))
    sub.add_parser("self-test")
    args = parser.parse_args()

    if args.command == "claim":
        cmd_claim(args.worker_id)
    elif args.command == "self-test":
        cmd_self_test()


if __name__ == "__main__":
    main()
