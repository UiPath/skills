#!/usr/bin/env python3
"""Grade the kinds a draft skeleton's boxes are labeled with.

Usage (cwd = sandbox root): check_skeleton_kinds.py <ProjectName> [--registry-json <file>]

Phase 2 labels every box ``<action> [<kind>]``, the kind taken verbatim from
the toolbox list preflight 1a reads: an extension type's ``Kind``, or its
``Label`` when it has none. This passes when every task box carries a
bracketed kind and each one is a ``Kind`` or ``Label`` of a type Studio Web's
BPMN toolbox offers. It fails on a box with no kind, on a kind that is not in
the list (an invented or paraphrased one), and on a case-management-only type
(the ones 1a's filter drops), which the BPMN toolbox does not offer.

The list comes from the installed CLI, not a copy pinned here:
``uip maestro bpmn registry list`` reads the CLI's built-in catalog, needs no
login or network, and is the same call (same binary) the agent made in 1a,
so the grade cannot drift from what the agent was shown when the CLI adds or
renames a kind. ``--registry-json`` grades against a saved list instead
(fixtures).

Standalone on purpose (stdlib only, no ``_shared`` import): the smoke tasks
stage only this directory as ``$REFERENCE_DIR``.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
ACTIVITY_TAGS = ("task", "serviceTask", "sendTask", "receiveTask", "scriptTask", "userTask",
                 "businessRuleTask", "manualTask", "callActivity")
REGISTRY_TIMEOUT_SECONDS = 30

# The types SKILL.md 1a's --output-filter drops: Studio Web generates them for
# case management, and its BPMN toolbox does not offer them.
CASE_ONLY_EXACT = {"Maestro.UpdateCaseState", "Maestro.RetrieveCaseState", "Maestro.NotificationService",
                   "Maestro.AcquireLock", "Maestro.ReleaseLock", "BPMN.Variables", "uipath:Activity"}
CASE_ONLY_PREFIX = "Maestro.Case"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def is_case_only(extension_type: str) -> bool:
    return extension_type.startswith(CASE_ONLY_PREFIX) or extension_type in CASE_ONLY_EXACT


def load_registry(saved: str | None) -> list[dict]:
    if saved:
        data = json.loads(Path(saved).read_text(encoding="utf-8"))
    else:
        uip = shutil.which("uip")
        if not uip:
            fail("uip not found on PATH; cannot read the toolbox kinds")
        try:
            res = subprocess.run([uip, "maestro", "bpmn", "registry", "list", "--limit", "-1", "--output", "json"],
                                 capture_output=True, text=True, timeout=REGISTRY_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            fail(f"`uip maestro bpmn registry list` did not answer within {REGISTRY_TIMEOUT_SECONDS}s")
        try:
            data = json.loads(res.stdout)
        except ValueError:
            fail(f"`uip maestro bpmn registry list` returned no JSON (exit {res.returncode}): {res.stdout[:300]}")
    types = ((data.get("Data") or {}).get("ExtensionTypes")) or []
    if not types:
        fail("`uip maestro bpmn registry list` returned no ExtensionTypes")
    return types


def kind_sets(types: list[dict]) -> tuple[dict[str, str], dict[str, str]]:
    """(toolbox kinds, case-only kinds), each mapping normalized text -> display text."""
    toolbox: dict[str, str] = {}
    case_only: dict[str, str] = {}
    for t in types:
        target = case_only if is_case_only(t.get("ExtensionType") or "") else toolbox
        for value in (t.get("Kind"), t.get("Label")):
            if value:
                target.setdefault(_norm(value), value)
    for key in toolbox:
        case_only.pop(key, None)
    return toolbox, case_only


def bracket_candidates(name: str) -> list[str]:
    """Every ``[...]`` suffix of a box label, longest first.

    A label may itself contain brackets (``Execute business rule [Preview]``),
    so each ``[`` that opens a suffix ending in ``]`` is a candidate. A
    trailing ``→ Variable`` note (phase 2 rule: name what the box assigns) is
    dropped first.
    """
    label = re.sub(r"\s*(→|->)\s*[^\[\]]*$", "", name.strip())
    if not label.endswith("]"):
        return []
    return [label[i + 1:-1] for i, ch in enumerate(label) if ch == "["]


def find_bpmn(name: str) -> str:
    paths = [p for p in sorted(glob.glob("**/*.bpmn", recursive=True)) if "node_modules" not in p]
    hinted = [p for p in paths if os.path.basename(p).lower() == f"{name.lower()}.bpmn"]
    in_project = [p for p in hinted if (Path(p).parent / "project.uiproj").is_file()]
    chosen = in_project or hinted
    if not chosen:
        fail(f"no {name}.bpmn found; found {paths}")
    return chosen[0]


def check(boxes: list[str], toolbox: dict[str, str], case_only: dict[str, str]) -> list[str]:
    errors = []
    for box in boxes:
        candidates = bracket_candidates(box)
        if not candidates:
            errors.append(f"box {box!r} carries no `[kind]` label")
            continue
        if any(_norm(c) in toolbox for c in candidates):
            continue
        shown = candidates[-1]
        hit = next((case_only[_norm(c)] for c in candidates if _norm(c) in case_only), None)
        if hit:
            errors.append(f"box {box!r} uses {hit!r}, a case-management type the BPMN toolbox does not offer")
        else:
            errors.append(f"box {box!r}: {shown!r} is not a Kind or Label in `registry list`")
    return errors


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--registry-json")
    args = ap.parse_args(argv)

    path = find_bpmn(args.name)
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        fail(f"{path} is not well-formed XML: {exc}")
    boxes = []
    for tag in ACTIVITY_TAGS:
        boxes += [el.get("name") or "" for el in root.iter(f"{{{BPMN_NS}}}{tag}")]
    if not boxes:
        fail(f"{path} has no task boxes")

    toolbox, case_only = kind_sets(load_registry(args.registry_json))
    errors = check(boxes, toolbox, case_only)
    if errors:
        print("FAIL:\n" + "\n".join(f"  - {e}" for e in errors))
        print("toolbox kinds: " + ", ".join(sorted(toolbox.values())))
        return 1
    print(f"OK: {len(boxes)} box(es) in {path} carry toolbox kinds: {boxes}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
