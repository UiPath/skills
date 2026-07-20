#!/usr/bin/env python3
"""Event-trigger placeholder fallback grader (Critical Rule 8).

The sdd.md declares a case whose START is an EVENT trigger on a connector that
cannot be resolved against the registry. Per Rule 8 the skill must write a
PLACEHOLDER event trigger rather than fabricate connector IDs. This grader
asserts the placeholder shape and its sibling-file coupling:

  1. A trigger node carries `data.uipath.serviceType == "Intsvc.EventTrigger"`.
  2. It is a true placeholder — `data.uipath` carries ONLY `serviceType`
     (no `context` / `inputs` / `outputs` / `bindings` / `metadata`).
  3. No trigger edge is created (edges retired) — `schema.edges` stays `[]`.
  4. The case still starts: some stage has a `case-entered` entry condition
     (the placeholder event trigger does not itself edge into a stage).
  5. `entry-points.json` (sibling of caseplan.json) has an entry whose
     `filePath` references the event trigger node id.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.case_check import (  # noqa: E402
    find_caseplan,
    find_stages,
    find_triggers,
    read_caseplan,
)


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def main():
    caseplan_path = find_caseplan()
    plan = read_caseplan(caseplan_path)

    # 1. Placeholder event trigger present.
    event_triggers = [
        t
        for t in find_triggers(plan)
        if ((t.get("data") or {}).get("uipath") or {}).get("serviceType")
        == "Intsvc.EventTrigger"
    ]
    if not event_triggers:
        serviceTypes = [
            ((t.get("data") or {}).get("uipath") or {}).get("serviceType")
            for t in find_triggers(plan)
        ]
        _fail(
            "no trigger node with data.uipath.serviceType == 'Intsvc.EventTrigger'; "
            f"trigger serviceTypes seen: {serviceTypes}"
        )
    trig = event_triggers[0]
    trig_id = trig.get("id")

    # 2. True placeholder — only serviceType under data.uipath.
    uipath = (trig.get("data") or {}).get("uipath") or {}
    extra = [k for k in uipath if k != "serviceType"]
    if extra:
        _fail(
            f"placeholder event trigger data.uipath must carry ONLY 'serviceType'; "
            f"found extra keys {extra} (Rule 8 — no fabricated connector config)"
        )

    # 3. No trigger edge.
    edges = plan.get("edges") or []
    if edges:
        _fail(f"schema.edges must stay [] (edges retired); found {len(edges)} edge(s)")

    # 4. Case starts via a stage's case-entered entry condition.
    def _has_case_entered(stage: dict) -> bool:
        for cond in (stage.get("data") or {}).get("entryConditions") or []:
            for group in cond.get("rules") or []:
                for rule in group or []:
                    if (rule or {}).get("rule") == "case-entered":
                        return True
        return False

    if not any(_has_case_entered(s) for s in find_stages(plan, include_exception=True)):
        _fail(
            "no stage has a 'case-entered' entry condition — with a placeholder "
            "event trigger (no trigger edge), the first stage must start the case"
        )

    # 5. entry-points.json references the event trigger node.
    ep_path = os.path.join(os.path.dirname(caseplan_path), "entry-points.json")
    if not os.path.exists(ep_path):
        _fail(f"entry-points.json not found next to caseplan.json ({ep_path})")
    with open(ep_path) as f:
        ep = json.load(f)
    entries = ep.get("entryPoints") or []
    if not any(f"#{trig_id}" in (e.get("filePath") or "") for e in entries):
        filepaths = [e.get("filePath") for e in entries]
        _fail(
            f"entry-points.json has no entry referencing the event trigger "
            f"{trig_id!r}; filePaths present: {filepaths}"
        )

    print(
        f"OK: placeholder event trigger {trig_id!r} (serviceType only); "
        f"edges=[]; case-entered start present; entry-points.json entry linked"
    )


if __name__ == "__main__":
    main()
