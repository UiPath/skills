#!/usr/bin/env python3
"""Shared helpers for uipath-maestro-bpmn brownfield-edit eval checks.

An edit task ships a pristine fixture `.bpmn` into the sandbox; the agent makes a
surgical edit and the sidecar check diffs the edited file against the pristine
original (read from the task's own `fixture/` dir via ``load_original``, which
resolves against the reference mirror rather than the agent-writable sandbox).

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

# These helpers live in `_shared/`; fixtures stay with their task. Both are
# mirrored under $REFERENCE_DIR, which is this file's parent.
FAMILY_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def load_original(task_dir: str, basename: str) -> ET.Element:
    """Parse the pristine fixture from ``<task_dir>/fixture/`` (e.g. `edit/add_node`)."""
    path = os.path.join(FAMILY_ROOT, task_dir, "fixture", basename)
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


def assert_variables_extended_only(original: ET.Element, edited: ET.Element) -> None:
    """Pristine variable declarations must round-trip untouched — attributes of
    the ``uipath:variables`` block itself included, and in their pristine
    relative order. Additions are allowed, but every added declaration needs a
    non-empty ``name`` and ``type``, and its ``elementId`` (when present) must
    reference a live BPMN element id."""
    orig = _find_first(original, "variables")
    new = _find_first(edited, "variables")
    if orig is None:
        fail("fixture bug: no uipath:variables in pristine original")
    if new is None:
        fail("uipath:variables was dropped by the edit (must be preserved)")
    if sorted(orig.attrib.items()) != sorted(new.attrib.items()):
        fail("uipath:variables attributes were modified (must round-trip untouched)")
    ids = [child.attrib.get("id", "") for child in new]
    if not all(ids) or len(ids) != len(set(ids)):
        fail("all uipath:variables declarations must have unique non-empty ids")
    edited_by_id = {child.attrib.get("id"): child for child in new}
    for child in orig:
        child_id = child.attrib.get("id")
        match = edited_by_id.get(child_id)
        if match is None:
            fail(f"pristine variable {child_id!r} was removed (must be preserved)")
        if canonical(child) != canonical(match):
            fail(f"pristine variable {child_id!r} was modified (must round-trip untouched)")
    pristine_order = [child.attrib.get("id") for child in orig]
    pristine_set = set(pristine_order)
    edited_pristine_order = [i for i in ids if i in pristine_set]
    if edited_pristine_order != pristine_order:
        fail("pristine variable declarations were reordered (must round-trip untouched)")
    # Not `all_ids`: that accepts DI shape ids, which the canvas treats as
    # orphans on import.
    live_ids = {
        el.attrib["id"]
        for el in edited.iter()
        if el.attrib.get("id") and el.tag.startswith("{" + BPMN_NS + "}")
    }
    for child in new:
        child_id = child.attrib.get("id")
        if child_id in pristine_set:
            continue
        if not child.attrib.get("name") or not child.attrib.get("type"):
            fail(f"new variable {child_id!r} needs a non-empty name and type")
        scope = child.attrib.get("elementId")
        if scope and scope not in live_ids:
            fail(f"new variable {child_id!r} has a dangling elementId {scope!r}")


def _live_bpmn_ids(root: ET.Element) -> set[str]:
    """Ids of real BPMN elements. Excludes DI shape ids, which the canvas
    treats as orphans when a variable scopes to one."""
    return {
        el.attrib["id"]
        for el in root.iter()
        if el.attrib.get("id") and el.tag.startswith("{" + BPMN_NS + "}")
    }


def _declarations_anywhere(root: ET.Element) -> dict[str, ET.Element]:
    """Every ``uipath:variables`` child in the file, keyed by id — the root
    block plus any subprocess-level block."""
    found: dict[str, ET.Element] = {}
    for block in root.iter():
        if local(block.tag) != "variables":
            continue
        for child in block:
            child_id = child.attrib.get("id", "")
            if not child_id:
                fail("a uipath:variables declaration has no id")
            if child_id in found:
                fail(f"variable id {child_id!r} is declared more than once")
            found[child_id] = child
    return found


def assert_variables_preserved_or_rescoped(original: ET.Element, edited: ET.Element) -> None:
    """Every pristine declaration must survive with its kind, ``name`` and
    ``type`` intact, anywhere in the file. Only ``elementId`` may change, and
    it must still name a live BPMN element.

    Looser than ``assert_variables_extended_only`` on purpose: an edit that
    groups nodes into a subprocess may re-scope a variable into that
    subprocess's own block, which the skill documents as importing cleanly.
    Freezing the root block would fail that correct edit."""
    pristine = _declarations_anywhere(original)
    if not pristine:
        fail("fixture bug: no uipath:variables declarations in pristine original")
    current = _declarations_anywhere(edited)
    live_ids = _live_bpmn_ids(edited)
    for child_id, child in pristine.items():
        match = current.get(child_id)
        if match is None:
            fail(f"pristine variable {child_id!r} was dropped by the edit")
        for attribute in ("name", "type"):
            if child.attrib.get(attribute) != match.attrib.get(attribute):
                fail(
                    f"pristine variable {child_id!r} changed its {attribute} "
                    f"({child.attrib.get(attribute)!r} -> {match.attrib.get(attribute)!r})"
                )
        if local(child.tag) != local(match.tag):
            fail(f"pristine variable {child_id!r} changed kind (input/output/inputOutput)")
        scope = match.attrib.get("elementId")
        if scope and scope not in live_ids:
            fail(f"variable {child_id!r} has a dangling elementId {scope!r}")


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
