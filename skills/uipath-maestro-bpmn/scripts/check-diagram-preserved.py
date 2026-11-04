#!/usr/bin/env python3
"""Check that an edit kept the user's BPMN diagram.

Usage:
    python3 check-diagram-preserved.py <before.bpmn> <after.bpmn> [--removed ID,ID,...]

Compares the diagram (bpmndi) of the file before and after an edit and reports
anything of the user's that was lost or re-laid out:

- the plane re-targeted (e.g. from the collaboration to the process)
- a pool or lane shape missing, a lane deleted, or a node dropped from its lane
- a text annotation or group deleted, or its shape missing
- a surviving shape or edge whose colors changed
- a surviving node shape whose size changed, or that lost its bounds; pools,
  lanes and expanded subprocesses may grow to fit an insertion
- surviving node shapes moved by different offsets (a re-layout); moving all of
  them by one common offset to make room for an insertion is allowed
- a surviving flow or association that lost its edge

`--removed` names element ids the edit was asked to delete. An id named there
that is still in the edited model is reported, so it cannot hide a loss.

Not checked: edge waypoints (a re-targeted flow is re-routed) and labels.

tests/tasks/uipath-maestro-bpmn/_shared/edit_check.py `assert_diagram_preserved`
holds the same rules for the evals; keep the two in step.

Prints a JSON object. Exit 0 when nothing was lost, 1 when something was,
2 on bad input. Standard library only.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET

CONTAINERS = {"participant", "lane"}
ARTIFACTS = {"textAnnotation", "group"}


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def load(path: str) -> ET.Element:
    try:
        return ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        print(json.dumps({"Result": "Failure", "Message": f"cannot read {path}: {exc}"}))
        sys.exit(2)


def kinds(root: ET.Element) -> dict[str, str]:
    return {e.get("id"): local(e.tag) for e in root.iter() if e.get("id")}


def shapes(root: ET.Element) -> dict[str, ET.Element]:
    return {s.get("bpmnElement"): s for s in root.iter() if local(s.tag) == "BPMNShape"}


def edges(root: ET.Element) -> dict[str, ET.Element]:
    return {e.get("bpmnElement"): e for e in root.iter() if local(e.tag) == "BPMNEdge"}


def bounds(shape: ET.Element) -> tuple[int, int, int, int] | None:
    b = next((c for c in shape if local(c.tag) == "Bounds"), None)
    if b is None:
        return None
    try:
        return tuple(round(float(b.get(k))) for k in ("x", "y", "width", "height"))
    except (TypeError, ValueError):
        return None


def resizable(kind: str | None, shape: ET.Element) -> bool:
    return kind in CONTAINERS or shape.get("isExpanded") == "true"


def colors(shape: ET.Element) -> tuple:
    return tuple(sorted((k, v) for k, v in shape.attrib.items() if "color" in k))


def plane_target(root: ET.Element) -> str | None:
    plane = next((e for e in root.iter() if local(e.tag) == "BPMNPlane"), None)
    return None if plane is None else plane.get("bpmnElement")


def lanes(root: ET.Element) -> dict[str, set[str]]:
    return {
        lane.get("id"): {(r.text or "").strip() for r in lane if local(r.tag) == "flowNodeRef"}
        for lane in root.iter()
        if local(lane.tag) == "lane"
    }


def main() -> None:
    args = sys.argv[1:]
    removed: set[str] = set()
    if "--removed" in args:
        i = args.index("--removed")
        removed = {x for x in args[i + 1].split(",") if x} if i + 1 < len(args) else set()
        args = args[:i] + args[i + 2:]
    if len(args) != 2:
        print(__doc__)
        sys.exit(2)
    before, after = load(args[0]), load(args[1])
    losses: list[str] = []

    if plane_target(before) != plane_target(after):
        losses.append(f"diagram plane re-targeted from {plane_target(before)!r} to {plane_target(after)!r}")

    kind, s0, s1 = kinds(before), shapes(before), shapes(after)
    after_ids = set(kinds(after))
    for el_id in sorted(removed & after_ids):
        losses.append(f"{el_id!r} is named in --removed but is still in the model")
    removed -= after_ids
    for el_id, k in kind.items():
        if el_id in removed:
            continue
        if k in CONTAINERS and el_id in s0 and el_id not in s1:
            losses.append(f"{k} {el_id!r} lost its diagram shape")
        if k in ARTIFACTS:
            if el_id not in after_ids:
                losses.append(f"{k} {el_id!r} deleted from the model")
            elif el_id in s0 and el_id not in s1:
                losses.append(f"{k} {el_id!r} lost its diagram shape")

    l0, l1 = lanes(before), lanes(after)
    for lane_id, nodes in l0.items():
        if lane_id in removed:
            continue
        if lane_id not in l1:
            losses.append(f"lane {lane_id!r} deleted from the model")
            continue
        for node in sorted(nodes - removed - l1[lane_id]):
            if node in after_ids:
                losses.append(f"{node!r} dropped from lane {lane_id!r}")

    offsets: set[tuple[int, int]] = set()
    for el_id, shape in s0.items():
        if el_id in removed or el_id not in s1:
            continue
        if colors(shape) != colors(s1[el_id]):
            losses.append(f"{el_id!r} lost or changed its colors")
        b0, b1 = bounds(shape), bounds(s1[el_id])
        if b0 is None:
            continue
        if b1 is None:
            losses.append(f"{el_id!r} lost its bounds")
            continue
        if kind.get(el_id) in CONTAINERS:
            continue
        x0, y0, w0, h0 = b0
        x1, y1, w1, h1 = b1
        if (w0, h0) != (w1, h1) and not resizable(kind.get(el_id), shape):
            losses.append(f"{el_id!r} resized from {w0}x{h0} to {w1}x{h1}")
        if (x0, y0) != (x1, y1):
            offsets.add((x1 - x0, y1 - y0))
    if len(offsets) > 1:
        losses.append(f"existing shapes were re-laid out ({len(offsets)} different moves)")

    e0, e1 = edges(before), edges(after)
    for el_id, edge in e0.items():
        if el_id in removed or el_id not in after_ids:
            continue
        if el_id not in e1:
            losses.append(f"{kind.get(el_id, 'flow')} {el_id!r} lost its diagram edge")
        elif colors(edge) != colors(e1[el_id]):
            losses.append(f"{el_id!r} lost or changed its edge colors")

    print(json.dumps({"Result": "Failure" if losses else "Success", "Losses": losses}, indent=2))
    sys.exit(1 if losses else 0)


if __name__ == "__main__":
    main()
