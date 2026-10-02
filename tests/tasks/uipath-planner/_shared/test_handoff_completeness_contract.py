"""Contract guard for the two Planner Handoff rows a host reads to decide what an SDD is.

`Status` answers "may tasks be derived?" and `Template validation` answers "is the file complete?".
They used to change in the same write, so a complete SDD held at `Status: draft` by a blocking
review item looked exactly like an interrupted run, and a host that refused unfinished drafts
refused both. These tests pin the split for the generic lane and the templates it emits.

The case lane is deliberately out of scope: it has no blocking-item state, so its ready flip and
its `passed` stay one write, and `uipath-maestro-case` reads `Template validation: passed` as its
build receipt. One test pins that too, so a later edit cannot loosen the case receipt by accident.
"""

import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")
PLANNER = os.path.join(ROOT, "skills", "uipath-planner")
GUIDE = os.path.join(PLANNER, "references", "sdd-generation-guide.md")
CASE_LANE = os.path.join(PLANNER, "references", "case", "case-design-lane-guide.md")
GENERIC_TEMPLATES = ["agent", "api-workflow", "bpmn", "coded-app", "flow", "rpa"]


def read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def validation_row(text: str) -> str:
    rows = [line for line in text.splitlines() if re.match(r"\s*\|\s*\*\*Template validation\*\*\s*\|", line)]
    assert len(rows) == 1, f"expected exactly one Template validation row, found {len(rows)}"
    return rows[0]


def test_generic_templates_do_not_tie_completeness_to_the_ready_flip() -> None:
    for name in GENERIC_TEMPLATES:
        row = validation_row(read(os.path.join(PLANNER, "assets", "templates", f"{name}-sdd-template.md")))
        assert "ready flip" not in row, f"{name}: Template validation must not wait for the ready flip"
        assert "superset check" in row, f"{name}: Template validation must name the completeness check"


def test_guide_sets_passed_on_the_completeness_check_whatever_status_reads() -> None:
    row = validation_row(read(GUIDE))
    assert "whatever `Status` reads" in row
    assert "`Status: draft` + `Template validation: passed`" in row


def test_blocking_item_keeps_draft_but_not_pending() -> None:
    guide = read(GUIDE)
    assert "Any `blocking` item keeps `Status: draft` with `Template validation: passed`" in guide


def test_known_access_method_makes_contract_details_default_carried() -> None:
    guide = read(GUIDE)
    closed_list = re.search(r"Blocking is a closed list:(.*?)Record the class", guide, re.S)
    assert closed_list, "the closed blocking list moved; update this guard"
    item_b = closed_list.group(1)
    for term in ("endpoints", "authentication", "schemas", "`default-carried`", "never `blocking`"):
        assert term in item_b, f"closed-list item (b) must name {term}"


def test_accepting_a_placeholder_resolves_the_item() -> None:
    guide = read(GUIDE)
    assert re.search(r"accepts a default, a placeholder, a TBD, or a HOLD.*?`default-carried`", guide, re.S)


def test_case_lane_keeps_passed_and_ready_in_one_write() -> None:
    lane = read(CASE_LANE)
    assert "**Ready flip is the LAST Edit:** `Status: ready`, `Template validation: passed`." in lane
