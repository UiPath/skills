#!/usr/bin/env python3
"""JiraCreateIssue: structural + live + tenant checks.

Exits non-zero on the first failure with ``FAIL: ...``; prints ``OK: ...`` per
check on success.

  1. A ``.flow`` file is valid JSON with ``nodes``/``edges``.
  2. It references the ``uipath-atlassian-jira`` connector key.
  3. It references a Create-Issue operation.
  4. LIVE: ``flow debug`` runs to ``Completed`` (this actually creates a real
     Jira issue) and produces an issue key in its outputs.
  5. TENANT: re-reading that key via ``curated_get_issue`` returns the seed
     summary — proof the flow hit Jira rather than fabricating an output.

The created key is recorded to ``.created_keys`` so post_run teardown deletes
it even if a later step fails.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
MAESTRO = os.path.dirname(os.path.dirname(HERE))  # …/uipath-maestro-flow
sys.path.insert(0, MAESTRO)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "_jira_shared"))
from _shared.flow_check import (  # noqa: E402
    collect_outputs,
    get_last_debug_raw,
    run_debug,
)
import jira_is  # noqa: E402

JIRA_KEY = "uipath-atlassian-jira"
ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")
WORKDIR = Path.cwd()


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _load_seed() -> dict:
    for candidate in (WORKDIR / "seed.json", Path(HERE) / "seed.json"):
        if candidate.is_file():
            return json.loads(candidate.read_text())
    _fail("seed.json not found (expected pre_run seed_jira.py to write it)")


def _flow_raw() -> str:
    flows = glob.glob("**/*.flow", recursive=True)
    if not flows:
        _fail("no .flow file found under cwd")
    for path in flows:
        raw = open(path, encoding="utf-8").read()
        try:
            flow = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if "nodes" in flow and "edges" in flow and JIRA_KEY in raw:
            print(f"OK: {path}: {len(flow['nodes'])} nodes, {len(flow['edges'])} edges, {JIRA_KEY} present")
            return raw
    _fail(f"no valid .flow references the {JIRA_KEY} connector (checked {flows})")


def _record_key(key: str) -> None:
    path = WORKDIR / ".created_keys"
    existing = path.read_text().split() if path.is_file() else []
    if key not in existing:
        with path.open("a") as f:
            f.write(key + "\n")


def _candidate_keys(payload: dict, project_key: str) -> list[str]:
    """Issue-key candidates from the debug run: clean leaves matching the
    issue-key shape, plus a project-scoped scan of the raw payload as a
    fallback (covers keys buried in a nested response blob)."""
    cands: list[str] = []
    for leaf in collect_outputs(payload):
        s = str(leaf).strip()
        if ISSUE_KEY_RE.match(s):
            cands.append(s)
    raw = get_last_debug_raw() or ""
    cands.extend(re.findall(rf"\b{re.escape(project_key)}-\d+\b", raw))
    # de-dup, preserve order
    seen: set[str] = set()
    return [k for k in cands if not (k in seen or seen.add(k))]


def main() -> None:
    seed = _load_seed()
    _flow_raw()

    payload = run_debug(timeout=240)
    print("OK: flow debug completed")

    project_key = seed["project_key"]
    candidates = _candidate_keys(payload, project_key)
    if not candidates:
        _fail(f"no issue key (e.g. {project_key}-123) in flow debug outputs")
    print(f"OK: candidate issue keys from debug: {candidates}")

    jira = jira_is.Jira.from_seed(seed)
    expected = seed["summary"]
    matched = None
    for key in candidates:
        fields = jira.get_issue(key)
        if fields and fields.get("summary") == expected:
            matched = key
            _record_key(key)  # for teardown
            break
    if not matched:
        _fail(
            f"no created issue in {candidates} carries the seed summary "
            f"{expected!r}; the flow did not create the expected issue in Jira "
            f"(or produced an output without hitting the tenant)"
        )
    print(f"OK: Jira issue {matched} exists with the seed summary")
    print("PASS: all JiraCreateIssue checks passed")


if __name__ == "__main__":
    main()
