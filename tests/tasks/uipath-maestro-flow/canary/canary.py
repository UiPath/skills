#!/usr/bin/env python3
"""Canary: standalone infra-health check for the Maestro Flow debug path.

Runs ``uip flow debug`` on Canary/Canary/ and asserts the fan-out/merge
flow's five plugin legs (coded agent, lowcode agent, RPA, API workflow,
Slack) each completed with the expected output. A failing leg pinpoints
whether the regression is infra (this task fails) or skill (this task
passes while the skill's own e2e fails).

Hardcoded inputs in Canary/Canary/Canary.flow:
  - countletters1                inputString = "car"     → output.count = 1
  - countlettersLowcodeAgent1    inputString = "berry"   → output.count = 2
  - rpaWorkflow1                 problemId   = 42        → output.title = "Coded Triangle Numbers"
  - apiWorkflow1                 name        = "tomasz"  → output.EstimatedAge ∈ [40, 60]
  - getChannelInfo1              id          = CLYMR02GK → output.topic.value contains "700 Bellevue way"
"""

import json
import os
import subprocess
import sys
import time
from typing import Any, Callable

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(HERE, "Canary", "Canary")
DEBUG_TIMEOUT = 780  # RPA cold-start alone can hit 5min; fan-out amplifies tail


def _die(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


class _Missing:
    def __repr__(self) -> str:
        return "<MISSING>"


_MISSING = _Missing()


def dig(obj: Any, *path: Any) -> Any:
    cur = obj
    for k in path:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return _MISSING
    return cur


def _eq(expected):
    return lambda a: None if a == expected else f"got {a!r}, expected {expected!r}"


def _int_in(lo, hi):
    def m(a):
        if not isinstance(a, int):
            return f"got {a!r}, expected int"
        if not (lo <= a <= hi):
            return f"got {a}, expected {lo}≤n≤{hi}"
        return None

    return m


def _contains_ci(needle):
    def m(a):
        if not isinstance(a, str):
            return f"got {a!r}, expected string"
        if needle.lower() not in a.lower():
            return f"{needle!r} not in {a[:120]!r}"
        return None

    return m


# (elementId, path into variables.globals, matcher, short formatter)
LEGS: list[
    tuple[str, tuple[str, ...], Callable[[Any], str | None], Callable[[Any], str]]
] = [
    (
        "countletters1",
        ("countletters1.output", "output", "count"),
        _eq(1),
        lambda v: f"count={v}",
    ),
    (
        "countlettersLowcodeAgent1",
        ("countlettersLowcodeAgent1.output", "count"),
        _eq(2),
        lambda v: f"count={v}",
    ),
    (
        "rpaWorkflow1",
        ("rpaWorkflow1.output", "title"),
        _eq("Coded Triangle Numbers"),
        lambda v: f"title={v!r}",
    ),
    (
        "apiWorkflow1",
        ("apiWorkflow1.output", "EstimatedAge"),
        _int_in(40, 60),
        lambda v: f"EstimatedAge={v}",
    ),
    (
        "getChannelInfo1",
        ("getChannelInfo1.output", "topic", "value"),
        _contains_ci("700 Bellevue way"),
        lambda v: f"topic[{len(v)}ch] contains '700 Bellevue way'",
    ),
]


def run_debug() -> dict:
    print(
        f"$ uip flow debug {PROJECT_DIR} --output json  (timeout={DEBUG_TIMEOUT}s)",
        flush=True,
    )
    t0 = time.monotonic()
    r = subprocess.run(
        ["uip", "flow", "debug", PROJECT_DIR, "--output", "json"],
        capture_output=True,
        text=True,
        timeout=DEBUG_TIMEOUT,
    )
    dt = time.monotonic() - t0

    try:
        resp: dict | None = json.loads(r.stdout)
    except json.JSONDecodeError:
        resp = None

    if r.returncode != 0:
        # The CLI writes the Failure JSON to stdout even on exit 1; stderr
        # only holds the "Tool factory already registered" warning and peer
        # chatter. Dump both so the real reason is visible.
        _die(
            f"uip flow debug exit {r.returncode} in {dt:.1f}s\n"
            f"--- stderr ---\n{r.stderr}"
            f"--- stdout ---\n{r.stdout}"
        )
    if resp is None:
        _die(f"could not parse debug JSON\n--- stdout ---\n{r.stdout}")
    if resp.get("Result") != "Success":
        _die(
            f"Result={resp.get('Result')!r}  Message={resp.get('Message')!r}\n"
            f"--- full response ---\n{json.dumps(resp, indent=2)}"
        )
    payload = resp.get("Data") or {}
    print(f"exit=0 in {dt:.1f}s  finalStatus={payload.get('finalStatus')}", flush=True)
    return payload


def main() -> int:
    payload = run_debug()
    globs = ((payload.get("variables") or {}).get("globals")) or {}
    statuses = {
        e.get("elementId"): e.get("status")
        for e in (payload.get("elementExecutions") or [])
        if e.get("elementId")
    }

    errors: list[str] = []
    if payload.get("finalStatus") != "Completed":
        errors.append(f"finalStatus != Completed")

    print()
    for eid, path, matcher, fmt in LEGS:
        st = statuses.get(eid, "<MISSING>")
        val = dig(globs, *path)
        if st != "Completed":
            print(f"  [FAIL] {eid:<28} status={st}")
            errors.append(f"{eid}: status={st}")
            continue
        if val is _MISSING:
            print(f"  [FAIL] {eid:<28} globals path missing: {path}")
            errors.append(f"{eid}: output path missing")
            continue
        err = matcher(val)
        if err:
            print(f"  [FAIL] {eid:<28} {err}")
            errors.append(f"{eid}: {err}")
        else:
            print(f"  [OK]   {eid:<28} {fmt(val)}")

    print()
    if errors:
        print(f"FAIL: {len(errors)} check(s) failed:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("OK: 5 plugin legs passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
