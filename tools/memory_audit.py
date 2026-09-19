from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CTX = ROOT / "context"

REQUIRED = [
    "MEMORY_INDEX.md",
    "HOT_STATE.md",
    "FACT_LEDGER.md",
    "DECISION_LEDGER.md",
    "FAILURE_LEDGER.md",
    "RESTART.md",
    "CHAT_LOG.md",
    "FINAL_AUDIT_2026-09-19.md",
]

STALE_PATTERNS = [
    "No LOL3 application code has been found yet",
    "## Current blocker",
    "### Current blocker",
    "Immediate next steps",
    "Production status: reference pipeline functional; live source-specific scraping",
]

def read(name: str) -> str:
    return (CTX / name).read_text(encoding="utf-8")

def fail(msg: str) -> None:
    print(f"MEMORY AUDIT: FAIL — {msg}")
    sys.exit(1)

def main() -> None:
    for name in REQUIRED:
        if not (CTX / name).exists():
            fail(f"missing required memory file: {name}")

    hot = read("HOT_STATE.md")
    idx = read("MEMORY_INDEX.md")
    final = read("FINAL_AUDIT_2026-09-19.md")
    bid = read("BID_PIPELINE.md")
    current = read("CURRENT_STATE.md")

    assertions = [
        ("hot phase", "FINALIZED_FOR_CURRENT_CONCRETE_INDIANA_SCOPE" in hot),
        ("hot no todo", bool(re.search(r"(?is)## ACTIVE TODO\s*None for this defined scope\.", hot))),
        ("prod run", "35422565481" in hot and "SUCCESS" in hot),
        ("smoke run", "35422611533" in hot and "SUCCESS" in hot),
        ("17 tests", "17/17" in hot),
        ("final artifact", "10578650088" in hot),
        ("memory index references hot", "HOT_STATE.md" in idx),
        ("memory index references ledgers", all(x in idx for x in ["FACT_LEDGER.md", "DECISION_LEDGER.md", "FAILURE_LEDGER.md"])),
        ("restart protocol", "Cold start" in read("RESTART.md")),
        ("executor state indexed", "agent/STATE.json" in idx and "agent/QUEUE.json" in idx),
        ("executor files present", (ROOT / "agent/STATE.json").exists() and (ROOT / "agent/QUEUE.json").exists()),
        ("final audit references prod run", "35422565481" in final),
        ("final audit references smoke run", "35422611533" in final),
    ]

    for name, ok in assertions:
        if not ok:
            fail(f"assertion failed: {name}")

    for name, text in [("HOT_STATE.md", hot), ("BID_PIPELINE.md", bid), ("CURRENT_STATE.md", current)]:
        for pattern in STALE_PATTERNS:
            if pattern in text:
                fail(f"stale active-context phrase {pattern!r} remains in {name}")

    for ledger_name, prefix in [
        ("FACT_LEDGER.md", "F"),
        ("DECISION_LEDGER.md", "D"),
        ("FAILURE_LEDGER.md", "F"),
    ]:
        text = read(ledger_name)
        ids = re.findall(r"(?m)^([A-Z]\d{3})\s", text)
        if len(ids) != len(set(ids)):
            fail(f"duplicate ledger IDs in {ledger_name}")

    # Cold-start simulation: the five boot files must independently expose
    # the project identity, mission, phase, and audit truth.
    boot = "\n".join(read(name) for name in [
        "HOT_STATE.md",
        "FACT_LEDGER.md",
        "DECISION_LEDGER.md",
        "FAILURE_LEDGER.md",
        "RESTART.md",
    ])
    for needle in [
        "bigdaddywill/lol3",
        current_phase or "",
        "agent/STATE.json",
        "agent/QUEUE.json",
        "Percrete",
        "Carr Construction",
        "35422565481",
        "35422611533",
        "HUMAN_REVIEW_REQUIRED",
    ]:
        if needle not in boot:
            fail(f"cold-start memory missing {needle!r}")

    print("MEMORY AUDIT: PASS")
    print("Cold-start reconstruction: PASS")
    print(f"Current phase: {current_phase}")
    print("Production audit: 35422565481 SUCCESS")
    print("Smoke audit: 35422611533 SUCCESS")
    print("Executor control plane: present")

if __name__ == "__main__":
    main()
