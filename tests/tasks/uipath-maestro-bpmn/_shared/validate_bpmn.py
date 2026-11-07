#!/usr/bin/env python3
"""Locate emitted ``.bpmn`` files and run ``uip maestro bpmn validate`` on every one.

Usage (from a task's run_command, cwd = sandbox root):

    python3 $REFERENCE_DIR/_shared/validate_bpmn.py [--budget SECONDS]

Plays the role ``uipath-maestro-flow/_shared/validate_flow.py`` plays for the
flow suite. Exit 0 iff at least one file was found and EVERY selected file
validates; otherwise exit 1 after naming the failing file.

Why not ``for f in $(find …); do validate && exit 0; done``: that loop passes
as soon as ANY file validates. ``uip maestro bpmn init`` leaves a valid
scaffold behind, so a sandbox holding a valid scaffold and an invalid real
process read as a pass (CI run 35501830119, devcon_expense_approval). Flow's
helper validates every flow under the project and fails on the first bad one;
this does the same.

Each file is parsed with ``xml.etree.ElementTree`` before the CLI sees it: the
validator tokenizes tolerantly and reports ``Valid`` on XML with an unbound
namespace prefix, so the CLI alone cannot carry a well-formedness criterion.
The skill states the same rule for its own readers (``SKILL.md`` step 4,
``references/structural-bpmn.md``).

Discovery: EVERY ``.bpmn`` under the sandbox, except scratch files
(``bpmn_check.is_scratch_bpmn``: tool caches, the brownfield pipeline's
``*.baseline/.edited/.merged/.original.bpmn``, and temp or archive dirs).
Validating those failed a correct edit on the UNEDITED ``X.baseline.bpmn`` that
``compile -o`` leaves beside the target (builder-sdk#1871). Not only project-registered files: on that same CI run the
agent's real process sat outside the initialised project while the valid
scaffold sat inside it, so a project-scoped rule still read as a pass.
``validate`` is offline, so one attempt per file is enough.

Timeouts are budgeted across the whole run, not per file. A per-file cap is
the wrong unit here precisely because the loop above exists to grade several
files: two slow files each finishing inside their own cap still overrun the
criterion, the harness SIGKILLs the shell, and its buffered stdout — the only
record of which file stalled — is discarded. ``validate_flow.py`` documents
that same failure. So :data:`DEFAULT_BUDGET_SECONDS` is an aggregate wall-clock
deadline: each file gets whatever is left of it, and an overrun is reported
from here, named, and flushed. The default is
:data:`CRITERION_TIMEOUT_SECONDS` -- the timeout every caller sets -- minus
:data:`BUDGET_HEADROOM_SECONDS` for interpreter start, discovery, and
writing the failure message. A caller on a different criterion
timeout passes ``--budget``.

Every print is flushed for the same reason: on an overrun the harness keeps
nothing this process has not already written.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared.bpmn_check import (  # noqa: E402
    context_value,
    is_scratch_bpmn,
    root_bindings,
)

CRITERION_TIMEOUT_SECONDS = 180
BUDGET_HEADROOM_SECONDS = 10
DEFAULT_BUDGET_SECONDS = CRITERION_TIMEOUT_SECONDS - BUDGET_HEADROOM_SECONDS


def _bpmn_files() -> list[Path]:
    root = Path.cwd()
    candidates = [
        p for p in root.rglob("*.bpmn") if not is_scratch_bpmn(p.relative_to(root))
    ]
    return sorted(candidates)


_ERROR_LINE = re.compile(r"^\s*-\s*\[error\]\s*\[(?P<element>[^\]]+)\]\s*(?P<code>[A-Z_]+):(?P<message>.*)$")
_ERROR_COUNT = re.compile(r"Found (\d+) error")
_GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def unbound_connection_refusal(path: Path, stdout: str, connector_key: str) -> str | None:
    """Why a failed validate is the documented unbound-connection refusal, or None.

    Opt-in (``--accept-unbound-connection <connectorKey>``) for a task whose
    tenant may hold no connection the agent can defensibly bind. The builder-SDK
    skill leaves a connector's connection binding as a placeholder rather than
    bind an unrelated one (R14 v2 query-params refused the tenant's only HTTP
    connection, another user's "Spotify", for a Google Tasks call), and
    ``validate`` then reports ``MISSING_BINDING`` (builder-sdk#1884).

    Accepted only when EVERY error is ``MISSING_BINDING`` on a node whose
    ``connectorKey`` is ``connector_key``, and each such node's connection reads
    a binding whose default is a placeholder, not a GUID. A made-up connection
    id is GUID-shaped and still fails, and so does any other error. Whether the
    agent SAID why it left the binding open is the task's own judge criterion.
    """
    try:
        payload = json.loads(stdout)
    except ValueError:
        return None
    text = str(payload.get("Instructions", "")) if isinstance(payload, dict) else ""
    errors = [m for m in map(_ERROR_LINE.match, text.splitlines()) if m]
    count = _ERROR_COUNT.search(text)
    if not errors or (count and int(count.group(1)) != len(errors)):
        return None
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    by_id = {el.attrib.get("id"): el for el in root.iter() if el.attrib.get("id")}
    bindings = root_bindings(root)
    placeholders = []
    for error in errors:
        if error["code"] != "MISSING_BINDING" or connector_key not in error["message"]:
            return None
        node = by_id.get(error["element"].strip())
        if node is None or context_value(node, "connectorKey") != connector_key:
            return None
        connection = context_value(node, "connection")
        if not connection.startswith("=bindings."):
            return None
        default = bindings.get(connection[len("=bindings."):], {}).get("default", "")
        if not default or _GUID.match(default):
            return None
        placeholders.append(f"{error['element'].strip()} -> {default!r}")
    return ", ".join(placeholders)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate every .bpmn under the sandbox."
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=DEFAULT_BUDGET_SECONDS,
        metavar="SECONDS",
        help=(
            "aggregate wall-clock budget for validating every file "
            f"(default: {DEFAULT_BUDGET_SECONDS}, sized for a "
            f"{CRITERION_TIMEOUT_SECONDS}s criterion timeout)"
        ),
    )
    parser.add_argument(
        "--accept-unbound-connection",
        metavar="CONNECTOR_KEY",
        help=(
            "accept a validate failure whose only errors are MISSING_BINDING on "
            "CONNECTOR_KEY nodes whose connection binding is still a placeholder "
            "(the documented refusal to bind an unrelated connection)"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    budget = args.budget
    deadline = time.monotonic() + budget

    files = _bpmn_files()
    if not files:
        print("FAIL: no .bpmn file found under the sandbox", file=sys.stderr, flush=True)
        return 1
    rc = 0
    accepted = 0
    for path in files:
        print(f"Validating {path}", flush=True)
        # `validate` tokenizes with a tolerant parser and reports Valid on XML
        # carrying an unbound namespace prefix (SKILL.md "Validate", and
        # references/structural-bpmn.md: "Run the well-formed-XML parse before
        # validate every time"). Without this the criterion passes malformed
        # BPMN, so do what the skill tells its own readers to do.
        try:
            ET.parse(path)
        except ET.ParseError as exc:
            print(
                f"FAIL: {path} is not well-formed XML: {exc}",
                file=sys.stderr,
                flush=True,
            )
            rc = 1
            continue
        # Whatever is left of the aggregate budget, so a fast file hands its
        # unused share to a slow one. Never below 1s: a non-positive timeout
        # would raise instead of running.
        per_file = max(1, int(deadline - time.monotonic()))
        try:
            proc = subprocess.run(
                ["uip", "maestro", "bpmn", "validate", str(path), "--output", "json"],
                capture_output=True,
                text=True,
                timeout=per_file,
            )
        except subprocess.TimeoutExpired:
            print(
                f"FAIL: validate timed out after {per_file}s on {path} "
                f"(aggregate budget {budget}s)",
                file=sys.stderr,
                flush=True,
            )
            return 1
        if proc.returncode != 0 and args.accept_unbound_connection:
            refusal = unbound_connection_refusal(
                path, proc.stdout or "", args.accept_unbound_connection
            )
            if refusal:
                print(
                    f"ACCEPTED: {path} fails validate only on unbound "
                    f"{args.accept_unbound_connection} connection placeholder(s): {refusal}",
                    flush=True,
                )
                accepted += 1
                continue
        if proc.returncode != 0:
            tail = (proc.stdout or proc.stderr or "").strip()[-1500:]
            print(
                f"FAIL: validate failed for {path}\n{tail}",
                file=sys.stderr,
                flush=True,
            )
            rc = 1
    if rc == 0:
        note = f" ({accepted} only on an unbound connection placeholder)" if accepted else ""
        print(f"OK: {len(files)} .bpmn file(s) validate{note}", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
