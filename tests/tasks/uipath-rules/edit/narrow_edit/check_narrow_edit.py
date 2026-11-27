#!/usr/bin/env python3
"""Grades one narrow edit of OrderRules against the pristine fixture.

`threshold`: Express priority starts at 500, not 1000. Only the input cells of the priority
table may change, so its rows split at 500; the 1000 in the tier table stays. `remove`: the priority decision, its shape and
its entry point are gone, and nothing else changed. `rename`: the discount decision's label
reads "Loyalty discount"; its `id` and `name` stay, so readers and consumers still resolve.

Every row requires every other element unchanged, the shapes kept where they were, and every
remaining entry point kept with its uniqueId.
"""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import check_shapes_kept, decision_for_output, decisions  # noqa: E402
from rules_check import NS, check_cases, fail, find_project, load_graph, read_entry_points  # noqa: E402

PROJECT = "OrderRules"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / f"{PROJECT}Solution" / PROJECT
SHIPPING = [({"orderTotal": total}, "Express" if total >= 500 else "Normal") for total in (0, 499.99, 500, 999, 1000, 5000)]


def canon(element: ET.Element) -> tuple:
    """The element as data, so indentation and attribute order are not differences."""
    return (element.tag, sorted(element.attrib.items()), (element.text or "").strip(),
            [canon(child) for child in element])


def model_elements(root: ET.Element) -> dict[str, ET.Element]:
    """Every top-level model element by id: decisions, inputs, models, annotations, associations.

    The diagram is left out; `check_shapes_kept` grades it.
    """
    return {e.get("id"): e for e in root
            if e.get("id") and not e.tag.endswith(("}extensionElements", "}DMNDI"))}


def check_rest_unchanged(before: ET.Element, after: ET.Element, changed: set[str], removed: set[str]) -> None:
    now = model_elements(after)
    for element_id, element in model_elements(before).items():
        if element_id in removed:
            if element_id in now:
                fail(f"{element_id} is still in the rule; the request was to remove it")
        elif element_id not in now:
            fail(f"{element_id} is gone; the request did not name it")
        elif element_id not in changed and canon(now[element_id]) != canon(element):
            fail(f"{element_id} changed; the request did not name it")
    added = sorted(set(now) - set(model_elements(before)))
    if added:
        fail(f"the edit added {added}; the request asked for no new element")


def check_entry_points(project: Path, removed_path: str | None) -> None:
    before = json.loads((FIXTURE / "entry-points.json").read_text(encoding="utf-8"))["entryPoints"]
    after = {e.get("filePath"): e.get("uniqueId") for e in read_entry_points(project)}
    for entry in before:
        if entry["filePath"] == removed_path:
            if removed_path in after:
                fail(f"entry point {removed_path} survives its decision; run `uip rules refresh`")
        elif after.get(entry["filePath"]) != entry["uniqueId"]:
            fail(f"entry point {entry['filePath']} is gone or has a new uniqueId; consumers bound to it would break")


def same_except_input_cells(before: ET.Element, after: ET.Element) -> None:
    """`after` is `before` with only input cells changed: same rows, ids, outputs and annotations."""
    def blanked(decision: ET.Element) -> tuple:
        copy = ET.fromstring(ET.tostring(decision))
        for cell in copy.findall(".//dmn:rule/dmn:inputEntry/dmn:text", NS):
            cell.text = ""
        return canon(copy)
    if blanked(after) != blanked(before):
        fail("the priority decision changed beyond its threshold cells: a row, an id, an output or an annotation")


def main(mode: str) -> None:
    project = find_project(PROJECT)
    dmn_file, after = load_graph(project)
    before = ET.parse(FIXTURE / dmn_file.name).getroot()
    priority = decision_for_output(before, "shipping").get("id")
    discount = decision_for_output(before, "discountPct").get("id")

    if mode == "threshold":
        check_rest_unchanged(before, after, changed={priority}, removed=set())
        now = decision_for_output(after, "shipping")
        same_except_input_cells(decision_for_output(before, "shipping"), now)
        check_cases(now.find("dmn:decisionTable", NS), "shipping", SHIPPING)
        check_entry_points(project, None)
    elif mode == "remove":
        check_rest_unchanged(before, after, changed=set(), removed={priority})
        if any(d.get("id") == priority for d in decisions(after)):
            fail("the priority decision is still in the rule")
        check_entry_points(project, f"/{dmn_file.name}#{priority}")
    elif mode == "rename":
        check_rest_unchanged(before, after, changed={discount}, removed=set())
        now = next(d for d in decisions(after) if d.get("id") == discount)
        if now.get("label") != "Loyalty discount":
            fail(f"the discount decision's label is {now.get('label')!r}, expected 'Loyalty discount'")
        if now.get("name") != "discount":
            fail(f"the discount decision's name changed to {now.get('name')!r}; a rename keeps the name readers use")
        relabelled = ET.fromstring(ET.tostring(now))
        relabelled.set("label", "Discount")
        if canon(relabelled) != canon(model_elements(before)[discount]):
            fail("the discount decision changed beyond its label")
        check_entry_points(project, None)
    else:
        fail(f"mode must be threshold, remove or rename, got {mode!r}")
    check_shapes_kept(before, after, elements_may_go=mode == "remove")
    print(f"OK: the {mode} edit changed only what it named; shapes and entry points kept")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
