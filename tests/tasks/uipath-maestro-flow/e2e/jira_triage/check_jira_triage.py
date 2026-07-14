#!/usr/bin/env python3
"""JiraTriage: structural + live + tenant checks for an input-driven
loop-and-switch triage flow.

The agent builds ONE flow that, per seeded issue, creates a Jira issue and then
— for the issues whose `priority` equals a value passed as a FLOW INPUT —
escalates it: transition to In Progress, assign it, and post an escalation
comment. Issues whose priority does not match the input are left untouched.

This check proves the composite, input-driven shape actually ran end to end:

  1. STRUCTURAL: a valid `.flow` references the `uipath-atlassian-jira`
     connector and contains a loop node (`core.logic.loop`) AND a branch node
     (`core.logic.switch`/`core.logic.decision`). It also declares at least one
     input variable — the escalation priority must be an input, not a constant.
  2. LIVE: `flow debug` runs to Completed with the escalation input set to
     "Medium" (supplied here, unknown to the agent).
  3. TENANT: re-reading each created issue proves the loop created ALL seeded
     issues and the branch routed ON THE INPUT — exactly the "Medium" issue is
     In Progress + assigned + carries the escalation comment, and the "High"
     and "Low" issues are untouched (still open, unassigned). A flow that
     hardcodes a priority escalates the wrong issue and fails here.

Every confirmed key is recorded to `.created_keys` as it is seen, so post_run
teardown deletes it even if a later assertion fails.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # local jira_is
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))  # …/uipath-maestro-flow (for _shared)
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_any_node_type,
    assert_flow_has_node_type,
    find_project_dir,
    get_last_debug_raw,
    read_flow_input_vars,
    run_debug,
)
import jira_is  # noqa: E402

JIRA_KEY = "uipath-atlassian-jira"
ESCALATE_VALUE = "Medium"  # supplied via --inputs; the agent never sees this


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _record_key(key: str) -> None:
    kf = Path(".created_keys")
    seen = set(kf.read_text().split()) if kf.is_file() else set()
    if key not in seen:
        with kf.open("a") as f:
            f.write(key + "\n")


def _status_name(fields: dict) -> str | None:
    s = fields.get("status")
    return s.get("name") if isinstance(s, dict) else s


def _assignee(fields: dict):
    a = fields.get("assignee")
    if not a:
        return None
    return (a.get("accountId") or a.get("displayName")) if isinstance(a, dict) else a


def main() -> None:
    seed = json.loads(Path("seed.json").read_text())
    issues = seed["issues"]
    project = seed["project_key"]
    expected_status = seed["expected_status"]
    escalated_marker = seed["escalated_comment"]
    prio_by_summary = {i["summary"]: i["priority"] for i in issues}

    # 1. STRUCTURAL ----------------------------------------------------------
    flows = glob.glob("**/*.flow", recursive=True)
    raw = next((r for p in flows for r in [open(p, encoding="utf-8").read()]
                if JIRA_KEY in r and '"nodes"' in r), None)
    if raw is None:
        _fail(f"no .flow references the {JIRA_KEY} connector (found {flows})")
    print(f"OK: flow references {JIRA_KEY}")

    assert_flow_has_node_type(["core.logic.loop"])
    assert_flow_has_any_node_type(["core.logic.switch", "core.logic.decision"])
    print("OK: flow contains a loop node and a switch/decision node")

    project_dir = find_project_dir()
    input_ids = read_flow_input_vars(project_dir)
    if not input_ids:
        _fail("flow declares no input variable — the escalation priority must be "
              "a flow input, not a hardcoded constant")
    print(f"OK: flow declares input variable(s): {input_ids}")

    # 2. LIVE — escalate the Medium issues via the flow input ---------------
    inputs = {i: ESCALATE_VALUE for i in input_ids}
    payload = run_debug(inputs=inputs, timeout=360)
    print(f"OK: flow debug completed (escalation input = {ESCALATE_VALUE!r})")

    cands = list(dict.fromkeys(re.findall(rf"\b{re.escape(project)}-\d+\b", get_last_debug_raw() or "")))
    if not cands:
        _fail(f"no issue key (e.g. {project}-123) in flow debug payload — the loop created nothing")
    print(f"OK: candidate keys from debug: {cands}")

    # 3. TENANT --------------------------------------------------------------
    conn = jira_is.connection_id()
    found: dict[str, dict] = {}  # summary -> fields, for issues that are ours
    for key in cands:
        fields = jira_is.get_issue(conn, key)
        if not fields:
            continue
        _record_key(key)  # real issue this run created — always clean it up
        summary = fields.get("summary")
        if summary in prio_by_summary:
            found[summary] = fields

    missing = [s for s in prio_by_summary if s not in found]
    if missing:
        _fail(f"the loop did not create every seeded issue — missing {missing}; "
              f"created and matched {list(found)}")

    # Exactly the issue(s) whose priority == the input must be escalated.
    for summary, fields in found.items():
        priority = prio_by_summary[summary]
        status = _status_name(fields)
        assignee = _assignee(fields)
        comment_blob = json.dumps(fields.get("comment"))
        should_escalate = priority == ESCALATE_VALUE

        if should_escalate:
            problems = []
            if status != expected_status:
                problems.append(f"status={status!r} (want {expected_status!r})")
            if not assignee:
                problems.append("assignee empty (want assigned)")
            if escalated_marker not in comment_blob:
                problems.append(f"missing comment {escalated_marker!r}")
            if problems:
                _fail(f"the {priority} issue should have been escalated but "
                      f"{'; '.join(problems)} — the flow did not act on the input-matched item")
        else:
            problems = []
            if status == expected_status:
                problems.append(f"status={status!r} (should be untouched)")
            if assignee:
                problems.append(f"assignee={assignee!r} (should be unassigned)")
            if escalated_marker in comment_blob:
                problems.append("carries the escalation comment")
            if problems:
                _fail(f"the {priority} issue was escalated but should NOT have been "
                      f"(input was {ESCALATE_VALUE!r}): {'; '.join(problems)} — the flow "
                      "escalated the wrong item (likely a hardcoded priority)")

    print(f"OK: only the {ESCALATE_VALUE} issue was escalated (In Progress + assigned + commented); "
          "High/Low untouched")
    print("PASS: all JiraTriage checks passed")


if __name__ == "__main__":
    main()
