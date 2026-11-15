#!/usr/bin/env python3
"""Locate emitted ``.flow`` files and run ``uip maestro flow validate``.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/validate_flow.py
    python3 $REFERENCE_DIR/validate_flow.py <Sol>/<Project>/<Project>.flow [...]
    python3 $REFERENCE_DIR/validate_flow.py --no-warnings [<path> ...]

With no arguments the flows are discovered (below). Pass explicit paths when a
brownfield fixture ships a second Flow project next to the one under test, which
discovery would rightly refuse as ambiguous. ``--no-warnings`` also fails a flow
that validates with ``Data.Warnings`` set.

Why this exists — a hardcoded ``<Name>/<Name>/<Name>.flow`` path in a success
criterion is brittle: ``uip maestro flow init <Name>`` scaffolds a
``<Name>Solution/`` wrapper directory, so the real path is
``<Name>Solution/<Name>/<Name>.flow`` — not ``<Name>/<Name>/<Name>.flow``.
The hardcoded command then fails with "File not found" even though the flow
itself is valid (observed on skill-flow-loop-multiply: criterion scored 0.0
purely on the path, while the flow validated fine when addressed correctly).

Discovery prefers the lone ``project.uiproj`` whose manifest declares
``ProjectType="Flow"`` and validates every flow under it. If no project exists,
it accepts one unambiguous root-level SDK emit instead. Exit 0 iff every selected
file validates; otherwise propagate the failing exit code.

Timeouts are budgeted here rather than left to the harness. ``flow validate``
refreshes the node manifest from the tenant on every invocation, so its wall
time is network-bound and bimodal — see :data:`_ATTEMPTS`. Left unbudgeted, a
stall runs past the criterion timeout, the harness SIGKILLs the shell, and the
report shows exit -1 with an empty stdout: no indication of which file stalled,
or that the flow itself was fine. This module self-terminates inside the
criterion budget instead, with a diagnosable message.
"""

from __future__ import annotations

import json
import re
import os
import subprocess
import sys
import time

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from flow_check import STUDIO_WEB_FLOW_FILE, find_flow_files, flow_file_is_named  # noqa: E402

# The criterion budget to self-terminate inside. coder_eval exports only
# TASK_DIR to a criterion's command, not the criterion's own timeout, so there
# is nothing authoritative to read yet — :data:`_BUDGET_ENV` is the proposed
# contract and stays inert until the harness sets it, at which point this needs
# no change. Until then the default mirrors the task YAMLs by hand, and
# :func:`_budget_seconds` announces what it resolved so a drift shows up in the
# criterion output instead of silently costing the retry.
_BUDGET_ENV = "CODER_EVAL_COMMAND_TIMEOUT"
_DEFAULT_BUDGET_SECONDS = 180

# Reserved for interpreter start, project discovery, and writing the failure
# message. Without it the last attempt can end exactly as the harness fires.
_BUDGET_HEADROOM_SECONDS = 20

# `flow validate` has no `--timeout` flag of its own — unlike `flow debug`,
# which self-terminates with a parseable envelope. The subprocess cap is the
# only guard, so an overrun is reported from here.
#
# Two attempts, not three: the stall is a hung tenant manifest fetch inside
# `ManifestClient.getManifest` (~3.3k dynamic nodes, measured 8-14s typical and
# 60-67s on the tail), and a second cold call clears it. A third would only eat
# budget that the first two already need.
_ATTEMPTS = 2
_BACKOFF_SECONDS = 5.0

# Below this an attempt cannot outlast even a typical manifest fetch, so
# spending the remaining budget on it just converts a readable timeout into a
# misleading one.
_MIN_ATTEMPT_SECONDS = 30


def _budget_seconds() -> int:
    """The criterion budget, from the harness if it says, else the default.

    A malformed or non-positive value is treated as absent rather than trusted:
    a zero budget would refuse every attempt and report exhaustion for a flow
    nobody ever tried to validate.
    """
    raw = os.environ.get(_BUDGET_ENV, "").strip()
    try:
        budget = int(float(raw))
    except ValueError:
        budget = 0
    if budget <= 0:
        if raw:
            print(
                f"note: ignoring {_BUDGET_ENV}={raw!r}; using "
                f"{_DEFAULT_BUDGET_SECONDS}s",
                file=sys.stderr,
            )
        return _DEFAULT_BUDGET_SECONDS
    return budget


def _as_text(raw: bytes | str | None) -> str:
    """Decode captured child output. ``subprocess.TimeoutExpired`` carries it as
    bytes even under ``text=True``, unlike ``CompletedProcess``."""
    if raw is None:
        return ""
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace")
    return raw


def _attempt_cap(remaining: float, attempts_left: int) -> float:
    """Seconds to allow one attempt, so the retries after it still fit.

    Splitting what is left rather than pre-dividing the budget per file lets a
    fast file hand its unused share to a slow one.
    """
    return max(_MIN_ATTEMPT_SECONDS, remaining / attempts_left)


_CANONICAL_LAYOUT_WARNING = "does not match canonical layout"
"""The warning `flow validate` gives a ``.flow`` not named after its project directory."""
_WARNING_COUNT = re.compile(r"^\s*(\d+) warning\(s\):\s*$")
"""The header line of a ``Data.Warnings`` string: how many ``- `` items follow."""


def _only_layout_warnings(warnings: str) -> bool:
    """True when the count header matches its items and every item is the canonical-layout warning.

    Any other line (another warning, a different bullet, a wrapped continuation) keeps the warnings.
    """
    lines = [line for line in warnings.splitlines() if line.strip()]
    count = _WARNING_COUNT.match(lines[0]) if lines else None
    items = lines[1:]
    return (
        count is not None
        and int(count.group(1)) == len(items) > 0
        and all(item.lstrip().startswith("- ") and _CANONICAL_LAYOUT_WARNING in item for item in items)
    )


def _warnings(stdout: str, flow: str) -> str:
    """``Data.Warnings`` of a ``flow validate --output json`` envelope, or ``""``.

    Output that is not a JSON envelope is reported as a warning, since a clean
    result cannot be read from it. For Studio Web's ``new.flow`` the
    canonical-layout warning is dropped: Studio Web always names the main file
    that, so the warning only says which host made the project.
    """
    try:
        envelope = json.loads(stdout)
    except ValueError:
        return f"no JSON envelope in stdout: {stdout.strip()[:500]!r}"
    data = envelope.get("Data") if isinstance(envelope, dict) else None
    warnings = data.get("Warnings") if isinstance(data, dict) else None
    if isinstance(warnings, str) and Path(flow).name == STUDIO_WEB_FLOW_FILE and _only_layout_warnings(warnings):
        print(f"note: ignoring the canonical-layout warning for Studio Web's {flow}", file=sys.stderr)
        return ""
    return json.dumps(warnings) if warnings else ""


def _validate(flow: str, deadline: float, budget: int, no_warnings: bool = False) -> int:
    """Validate one ``.flow``, retrying a stalled attempt. Returns its exit code.

    A non-zero exit is never retried: `flow validate` fails on schema and graph
    faults, which a second run reproduces exactly. Only a subprocess timeout —
    the hung manifest fetch — is worth another attempt.
    """
    for attempt in range(1, _ATTEMPTS + 1):
        remaining = deadline - time.monotonic()
        if remaining < _MIN_ATTEMPT_SECONDS:
            print(
                f"FAIL: {flow} — {budget}s criterion budget "
                f"exhausted before attempt {attempt} ({max(0.0, remaining):.0f}s left)",
                file=sys.stderr,
            )
            return 1

        try:
            result = subprocess.run(
                ["uip", "maestro", "flow", "validate", flow, "--output", "json"],
                capture_output=True,
                text=True,
                timeout=_attempt_cap(remaining, _ATTEMPTS - attempt + 1),
            )
        except subprocess.TimeoutExpired as exc:
            cap = _attempt_cap(remaining, _ATTEMPTS - attempt + 1)
            print(
                f"attempt {attempt}/{_ATTEMPTS} on {flow} exceeded {cap:.0f}s "
                "(tenant node-manifest refresh stalled)",
                file=sys.stderr,
            )
            if attempt == _ATTEMPTS:
                print(
                    f"FAIL: {flow} did not validate within "
                    f"{budget}s across {_ATTEMPTS} attempts. "
                    "The flow file itself may well be valid — this is the CLI's "
                    "manifest fetch, not a schema fault.\n"
                    f"stdout: {_as_text(exc.stdout)}\n"
                    f"stderr: {_as_text(exc.stderr)}",
                    file=sys.stderr,
                )
                return 1
            time.sleep(_BACKOFF_SECONDS)
            continue

        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        if result.returncode == 0 and no_warnings:
            warnings = _warnings(result.stdout, flow)
            if warnings:
                print(f"FAIL: {flow} validated with warnings: {warnings}", file=sys.stderr)
                return 1
        return result.returncode

    return 1  # unreachable; keeps the return type honest


def _studio_web_main_file(path: str) -> str:
    """``path``, or the ``new.flow`` beside it when ``path`` names a Flow project's main file.

    A task names the file the Node CLI writes (``<Sol>/<Name>/<Name>.flow``); Studio Web writes
    the same project's flow as ``<Sol>/<Name>/new.flow``.
    """
    if os.path.isfile(path) or not path.endswith(".flow"):
        return path
    project_dir, base = os.path.split(path)
    candidate = os.path.join(project_dir, STUDIO_WEB_FLOW_FILE)
    if os.path.isfile(candidate) and flow_file_is_named(candidate, base[: -len(".flow")]):
        return candidate
    return path


def main(paths: list[str] | None = None) -> int:
    no_warnings = "--no-warnings" in (paths or [])
    paths = [p for p in paths or [] if p != "--no-warnings"]
    if paths:
        paths = [_studio_web_main_file(p) for p in paths]
        missing = [p for p in paths if not os.path.isfile(p)]
        if missing:
            print(f"FAIL: flow file not found: {', '.join(missing)}", file=sys.stderr)
            return 1
        flows = list(paths)
    else:
        flows = find_flow_files()  # exits with its own message when nothing is found

    budget = _budget_seconds()
    deadline = time.monotonic() + max(
        _MIN_ATTEMPT_SECONDS, budget - _BUDGET_HEADROOM_SECONDS
    )

    rc = 0
    for flow in flows:
        # Flushed: on an overrun the harness discards this process's buffered
        # stdout, and this line is what names the file that stalled.
        print(f"Validating {flow}", flush=True)
        code = _validate(flow, deadline, budget, no_warnings)
        if code != 0:
            rc = code or 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
