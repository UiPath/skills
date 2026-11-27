#!/usr/bin/env python3
"""Grades work inside the existing Logistics solution, which already holds ShippingRules.

`new`: ReturnsRules joins Logistics. The sandbox still holds exactly one `.uipx`, that
manifest lists the new project once, the project sits in the solution folder, and its
return window matches the policy. `existing`: the request names ShippingRules, which already
exists, so its files must stay as they were and Logistics must still list it once. Where else
the agent puts the new policy is its choice. Both rows require ShippingRules unchanged.
"""

from __future__ import annotations

import filecmp
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from rules_check import check_cases, fail, find_project, load_rule, table_of  # noqa: E402

PRISTINE = Path(__file__).resolve().parents[2] / "_fixtures" / "solution_with_rule" / "Logistics"
RETURNS = [({"daysSinceDelivery": days}, days <= 30) for days in (0, 29.5, 30, 30.5, 365)]


def solution() -> tuple[Path, list]:
    manifests = sorted(Path(".").rglob("*.uipx"))
    if len(manifests) != 1:
        fail(f"the sandbox holds {len(manifests)} .uipx files {[str(m) for m in manifests]}, expected only Logistics.uipx")
    if manifests[0].name != "Logistics.uipx":
        fail(f"the one .uipx is {manifests[0]}, expected Logistics.uipx")
    return manifests[0].parent, json.loads(manifests[0].read_text(encoding="utf-8")).get("Projects") or []


def listed(projects: list, name: str) -> int:
    return sum(1 for p in projects if p.get("ProjectRelativePath") == f"{name}/project.uiproj")


def check_shipping_unchanged(folder: Path, projects: list) -> None:
    if listed(projects, "ShippingRules") != 1:
        fail("Logistics.uipx no longer lists ShippingRules exactly once")
    pristine = PRISTINE / "ShippingRules"
    current = folder / "ShippingRules"
    for file in sorted(p.relative_to(pristine) for p in pristine.rglob("*") if p.is_file()):
        if not (current / file).is_file() or not filecmp.cmp(pristine / file, current / file, shallow=False):
            fail(f"ShippingRules/{file} changed or is gone; the existing project is not this request's to change")


def grade_new() -> None:
    folder, projects = solution()
    check_shipping_unchanged(folder, projects)
    if listed(projects, "ReturnsRules") != 1:
        fail("Logistics.uipx does not list ReturnsRules/project.uiproj exactly once")
    project = find_project("ReturnsRules")
    if project.resolve().parent != folder.resolve():
        fail(f"ReturnsRules is at {project}, expected directly inside {folder}")
    _, root = load_rule(project)
    check_cases(table_of(root), "returnable", RETURNS)
    print("OK: one solution, ReturnsRules registered in it, ShippingRules unchanged, and the return window matches")


def grade_existing() -> None:
    manifest = Path("Logistics") / "Logistics.uipx"
    if not manifest.is_file():
        fail("Logistics/Logistics.uipx is gone")
    projects = json.loads(manifest.read_text(encoding="utf-8")).get("Projects") or []
    check_shipping_unchanged(manifest.parent, projects)
    print("OK: the existing ShippingRules is unchanged and still in Logistics")


if __name__ == "__main__":
    modes = {"new": grade_new, "existing": grade_existing}
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in modes:
        fail(f"mode must be one of {sorted(modes)}, got {mode!r}")
    modes[mode]()
