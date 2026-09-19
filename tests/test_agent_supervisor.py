from tools.agent_supervisor import (
    claim_next_task,
    checkpoint,
    fail,
    finish,
    recover_stale_leases,
    validate_queue,
    validate_state,
)


def blank_state():
    return {
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


def ready_task(task_id="T1", priority=1):
    return {
        "id": task_id,
        "title": "test task",
        "state": "READY",
        "priority": priority,
        "created_at": "2026-01-01T00:00:00Z",
        "checkpoint": None,
        "attempts": 0,
    }


def test_valid_empty_state_and_queue():
    state = blank_state()
    queue = {"schema_version": 1, "tasks": []}
    assert validate_state(state) == []
    assert validate_queue(queue) == []


def test_claim_checkpoint_and_finish(monkeypatch):
    state = blank_state()
    queue = {"schema_version": 1, "tasks": [ready_task()]}

    task = claim_next_task(state, queue, "worker-a")
    assert task["id"] == "T1"
    assert state["phase"] == "RUNNING"

    checkpoint(state, queue, "T1", "worker-a", "half done")
    assert queue["tasks"][0]["checkpoint"] == "half done"

    finish(state, queue, "T1", "worker-a", "verified")
    assert queue["tasks"][0]["state"] == "COMPLETE"
    assert state["active_task_id"] is None


def test_failed_task_can_retry():
    state = blank_state()
    queue = {"schema_version": 1, "tasks": [ready_task()]}

    claim_next_task(state, queue, "worker-a")
    fail(state, queue, "T1", "worker-a", "temporary issue", retry=True)

    assert queue["tasks"][0]["state"] == "READY"
    assert state["last_error"] == "temporary issue"


def test_stale_lease_is_recovered():
    state = blank_state()
    queue = {
        "schema_version": 1,
        "tasks": [{
            **ready_task("STALE"),
            "state": "RUNNING",
            "worker_id": "dead",
            "lease_expires_at": "2000-01-01T00:00:00Z",
            "attempts": 1,
        }],
    }

    assert recover_stale_leases(state, queue) == 1
    assert queue["tasks"][0]["state"] == "READY"
    assert state["recovery_count"] == 1


def test_priority_is_respected():
    state = blank_state()
    queue = {
        "schema_version": 1,
        "tasks": [ready_task("LOW", 1), ready_task("HIGH", 10)],
    }
    task = claim_next_task(state, queue, "worker-a")
    assert task["id"] == "HIGH"
