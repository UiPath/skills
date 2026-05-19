"""Shared helpers for pre_run seed scripts.

Conventions:
- All seeds work from CWD (the sandbox tempdir for a task).
- All seeds read/write seed.json — generate the per-run uuid8 on first invocation, reuse thereafter.
- All seeds append to created-resources.jsonl so post_run can clean up.
- task_id read from TASK_ID env var (set by coder_eval per task) with safe fallback."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

SEED_FILE = "seed.json"
SHARED_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = SHARED_DIR.parent.parent.parent / "fixtures"


def task_id() -> str:
    """Short, lowercase, hyphenated task_id for naming. Falls back to 'e2e' if env not set."""
    raw = os.environ.get("TASK_ID") or os.environ.get("CODER_EVAL_TASK_ID") or "e2e"
    return raw.lower().replace("_", "-")[:40]


def load_or_init_seed() -> dict:
    """Load seed.json, or initialize with a fresh uuid8 if it doesn't exist."""
    p = Path(SEED_FILE)
    if p.is_file():
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            pass
    seed = {
        "uuid8": uuid.uuid4().hex[:8],
        "task_id": task_id(),
    }
    p.write_text(json.dumps(seed, indent=2))
    return seed


def save_seed(seed: dict) -> None:
    """Persist seed.json after mutation."""
    Path(SEED_FILE).write_text(json.dumps(seed, indent=2))


def naming_prefix(seed: dict) -> str:
    """Return the per-run prefix used by every seeded resource: e2e-<task_id>-<uuid8>."""
    return f"e2e-{seed['task_id']}-{seed['uuid8']}"


def uip_json(*args: str, timeout: int = 60, check: bool = True) -> dict:
    """Run `uip ... --output json` and return parsed JSON.

    Args:
        *args: command parts (e.g., "or", "folders", "create", "name", "--description", "...")
        timeout: subprocess timeout in seconds
        check: if True, raise on non-success Result; if False, return the envelope anyway.

    Returns:
        The full JSON envelope (Result, Code, Data, ...) or {} on parse failure.
    """
    cmd = ["uip", *args, "--output", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if not result.stdout.strip():
        if check and result.returncode != 0:
            raise RuntimeError(
                f"uip {' '.join(args)} produced no output (exit {result.returncode}): {result.stderr.strip()[:300]}"
            )
        return {}
    try:
        envelope = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"uip {' '.join(args)} returned non-JSON output: {e}: {result.stdout[:300]}"
        )
    if check and envelope.get("Result") != "Success":
        raise RuntimeError(
            f"uip {' '.join(args)} failed: Result={envelope.get('Result')!r}, "
            f"Code={envelope.get('Code')!r}, Message={envelope.get('Message')!r}"
        )
    return envelope


def log(msg: str) -> None:
    """Stderr log with seed: prefix so messages stand out in coder_eval transcripts."""
    print(f"seed: {msg}", file=sys.stderr)
