#!/usr/bin/env python3
"""Shared helpers for uipath-maestro-bpmn brownfield-edit eval checks.

An edit task ships a pristine fixture `.bpmn` into the sandbox; the agent makes a
surgical edit and the sidecar check diffs the edited file against the pristine
original (read from the task's own `fixture/` dir via ``load_original``).

The core contract these helpers enforce: elements the agent did NOT author
(stable ids, unknown/preserve-only ``uipath:*`` payloads, ``migrationVersion``)
must round-trip structurally identical. ``canonical`` normalizes attribute order
and whitespace so legitimate reformatting is not flagged, while any real change
to a preserved subtree fails the check.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
UIPATH_NS = "http://uipath.org/schema/bpmn"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def load_original(check_file: str, basename: str) -> ET.Element:
    """Parse the pristine fixture stored next to the check script."""
    path = os.path.join(os.path.dirname(os.path.abspath(check_file)), "fixture", basename)
    if not os.path.isfile(path):
        fail(f"pristine fixture not found at {path}")
    return ET.parse(path).getroot()


def canonical(element: ET.Element):
    """A hashable, order- and whitespace-normalized view of an element subtree."""
    text = (element.text or "").strip()
    attribs = tuple(sorted(element.attrib.items()))
    children = tuple(canonical(child) for child in element)
    return (local(element.tag), attribs, text, children)


def canonical_ex(element: ET.Element, ignore: set[str] = frozenset()):
    """Like ``canonical`` but skips child elements whose local name is in ``ignore``."""
    text = (element.text or "").strip()
    attribs = tuple(sorted(element.attrib.items()))
    children = tuple(
        canonical_ex(child, ignore) for child in element if local(child.tag) not in ignore
    )
    return (local(element.tag), attribs, text, children)


def by_id(root: ET.Element, element_id: str) -> ET.Element | None:
    for el in root.iter():
        if el.attrib.get("id") == element_id:
            return el
    return None


_by_id = by_id


def all_ids(root: ET.Element) -> set[str]:
    return {el.attrib["id"] for el in root.iter() if el.attrib.get("id")}


def assert_no_orphan_di(root: ET.Element) -> None:
    """Every DI shape/edge must reference an element that still exists — catches
    leftover diagram interchange after a node/flow removal."""
    ids = all_ids(root)
    flow_ids = {fid for fid, _s, _t in flows(root)}
    for shape in (e for e in root.iter() if local(e.tag) == "BPMNShape"):
        ref = shape.attrib.get("bpmnElement")
        if ref and ref not in ids:
            fail(f"orphan BPMNShape references missing element {ref!r}")
    for edge in (e for e in root.iter() if local(e.tag) == "BPMNEdge"):
        ref = edge.attrib.get("bpmnElement")
        if ref and ref not in flow_ids and ref not in ids:
            fail(f"orphan BPMNEdge references missing flow {ref!r}")


def assert_config_preserved(original: ET.Element, edited: ET.Element, ids: list[str]) -> None:
    """Each listed node must keep its name/config/uipath payload; only its
    ``bpmn:incoming``/``bpmn:outgoing`` wiring may change (edit-adjacent nodes)."""
    ignore = {"incoming", "outgoing"}
    for element_id in ids:
        orig = _by_id(original, element_id)
        new = _by_id(edited, element_id)
        if orig is None:
            fail(f"fixture bug: id {element_id!r} not in pristine original")
        if new is None:
            fail(f"node {element_id!r} is missing after the edit")
        if canonical_ex(orig, ignore) != canonical_ex(new, ignore):
            fail(f"node {element_id!r} config/payload changed (only its wiring may change)")


def assert_ids_present(root: ET.Element, ids: list[str]) -> None:
    present = {el.attrib.get("id") for el in root.iter() if el.attrib.get("id")}
    missing = [i for i in ids if i not in present]
    if missing:
        fail(f"expected preserved ids missing after edit: {missing}")


def assert_id_absent(root: ET.Element, element_id: str) -> None:
    present = {el.attrib.get("id") for el in root.iter() if el.attrib.get("id")}
    if element_id in present:
        fail(f"element id {element_id!r} should have been removed but is still present")


def assert_preserved(original: ET.Element, edited: ET.Element, ids: list[str]) -> None:
    """Each listed element id must round-trip structurally identical."""
    for element_id in ids:
        orig = _by_id(original, element_id)
        new = _by_id(edited, element_id)
        if orig is None:
            fail(f"fixture bug: id {element_id!r} not in pristine original")
        if new is None:
            fail(f"preserved element {element_id!r} is missing after the edit")
        if canonical(orig) != canonical(new):
            fail(f"preserved element {element_id!r} was modified (must round-trip untouched)")


def _find_first(root: ET.Element, local_name: str) -> ET.Element | None:
    for el in root.iter():
        if local(el.tag) == local_name:
            return el
    return None


def assert_uipath_preserved(original: ET.Element, edited: ET.Element, local_name: str) -> None:
    """A named ``uipath:*`` payload (e.g. migrationVersion, caseManagement) must be untouched."""
    orig = _find_first(original, local_name)
    new = _find_first(edited, local_name)
    if orig is None:
        fail(f"fixture bug: no uipath:{local_name} in pristine original")
    if new is None:
        fail(f"uipath:{local_name} was dropped by the edit (must be preserved)")
    if canonical(orig) != canonical(new):
        fail(f"uipath:{local_name} payload was modified (must round-trip untouched)")


def flows(root: ET.Element) -> list[tuple[str, str, str]]:
    out = []
    for el in root.iter():
        if local(el.tag) == "sequenceFlow":
            out.append(
                (el.attrib.get("id", ""), el.attrib.get("sourceRef", ""), el.attrib.get("targetRef", ""))
            )
    return out


def has_flow(root: ET.Element, source: str, target: str) -> bool:
    return any(s == source and t == target for _id, s, t in flows(root))


def flow_node_ids(root: ET.Element) -> set[str]:
    kinds = {
        "startEvent", "endEvent", "task", "serviceTask", "sendTask", "receiveTask",
        "userTask", "businessRuleTask", "scriptTask", "callActivity", "subProcess",
        "exclusiveGateway", "parallelGateway", "inclusiveGateway", "eventBasedGateway",
    }
    return {
        el.attrib["id"]
        for el in root.iter()
        if local(el.tag) in kinds and el.attrib.get("id")
    }


def elements_local(root: ET.Element, local_name: str) -> list[ET.Element]:
    return [el for el in root.iter() if local(el.tag) == local_name]
