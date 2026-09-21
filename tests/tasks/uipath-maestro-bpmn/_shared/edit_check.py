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
import re
import xml.etree.ElementTree as ET
from enum import Enum

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
    """Pristine variable declarations round-trip untouched: the first block's
    with that block's attributes and their relative order, the rest by value.
    Additions may land in the process block or a ``bpmn:subProcess`` block —
    the only two the canvas reads — and each needs a non-empty ``name`` and
    ``type``, an ``elementId`` that names a live BPMN element when present,
    and an id unique across every block."""
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
    # Additions may live in any canvas-read uipath:variables block, not just
    # the first; _declarations_anywhere enforces block ownership, whole-file
    # id uniqueness, and rejects an id-less declaration in any block.
    pristine_anywhere = _declarations_anywhere(original, Side.ORIGINAL)
    edited_anywhere = _declarations_anywhere(edited, Side.EDITED)
    live_ids = _live_bpmn_ids(edited)
    for child_id, child in edited_anywhere.items():
        if child_id in pristine_anywhere:
            continue
        _assert_addition_is_well_formed(child, child_id, live_ids)
    # Pristine declarations beyond the first block (a fixture with a
    # subprocess-owned block) round-trip too; the first block's are already
    # checked above with their block's attributes and order.
    for child_id, child in pristine_anywhere.items():
        if child_id in pristine_set:
            continue
        match = edited_anywhere.get(child_id)
        if match is None:
            fail(f"pristine variable {child_id!r} was removed (must be preserved)")
        if canonical(child) != canonical(match):
            fail(f"pristine variable {child_id!r} was modified (must round-trip untouched)")


def _live_bpmn_ids(root: ET.Element) -> set[str]:
    """Ids of real BPMN elements. Excludes DI shape ids, which the canvas
    treats as orphans when a variable scopes to one."""
    return {
        el.attrib["id"]
        for el in root.iter()
        if el.attrib.get("id") and el.tag.startswith("{" + BPMN_NS + "}")
    }


def _assert_addition_is_well_formed(
    child: ET.Element,
    child_id: str,
    live_ids: set[str],
) -> None:
    if not child.attrib.get("name") or not child.attrib.get("type"):
        fail(f"new variable {child_id!r} needs a non-empty name and type")
    scope = child.attrib.get("elementId")
    if scope and scope not in live_ids:
        fail(f"new variable {child_id!r} has a dangling elementId {scope!r}")


class Side(Enum):
    """Which file a declaration set was read from. A defect on the ORIGINAL
    side is a fixture bug, not an agent error."""

    ORIGINAL = "pristine original"
    EDITED = "edited file"


def _declarations_anywhere(root: ET.Element, side: Side) -> dict[str, ET.Element]:
    """Every ``uipath:variables`` child in the file, keyed by id.

    The canvas reads ``uipath:variables`` from exactly two owners — the
    ``bpmn:process`` root and a ``bpmn:subProcess`` (PO.Frontend
    ``bpmn-from-xml-headless.ts`` filters the element out of every other
    node's data) — so a block on any other element is dropped on import and
    fails here rather than being silently walked."""
    prefix = "fixture bug: " if side is Side.ORIGINAL else ""
    where = side.value
    parents = _parents(root)
    found: dict[str, ET.Element] = {}
    for block in root.iter():
        if local(block.tag) != "variables":
            continue
        owner = parents.get(parents.get(block))
        owner_name = local(owner.tag) if owner is not None else "?"
        if owner_name not in ("process", "subProcess"):
            owner_id = owner.attrib.get("id") if owner is not None else None
            fail(
                f"{prefix}uipath:variables block on {owner_name} {owner_id!r} in the "
                f"{where} is dropped on import — declare in the process block or a "
                "bpmn:subProcess block"
            )
        for child in block:
            child_id = child.attrib.get("id", "")
            if not child_id:
                fail(f"{prefix}a uipath:variables declaration in the {where} has no id")
            if child_id in found:
                fail(f"{prefix}variable id {child_id!r} is declared more than once in the {where}")
            found[child_id] = child
    return found


def _frozen_view(element: ET.Element):
    """Everything about a declaration except the one thing a re-scope may
    move: its ``elementId``."""
    return (
        local(element.tag),
        tuple(sorted((k, v) for k, v in element.attrib.items() if k != "elementId")),
        (element.text or "").strip(),
    )


def _parents(root: ET.Element) -> dict[ET.Element, ET.Element]:
    return {child: parent for parent in root.iter() for child in parent}


def _enclosing_subprocess_ids(
    element: ET.Element,
    parents: dict[ET.Element, ET.Element],
) -> list[str]:
    """Subprocess ids containing ``element``, innermost first."""
    ids: list[str] = []
    current = parents.get(element)
    while current is not None:
        if local(current.tag) == "subProcess" and current.attrib.get("id"):
            ids.append(current.attrib["id"])
        current = parents.get(current)
    return ids


def _owning_subprocess(
    scope: str,
    edited: ET.Element,
    parents: dict[ET.Element, ET.Element],
) -> str | None:
    """The subprocess a scope id sits in: the id itself when it names a
    subprocess, otherwise the subprocess containing the scoped element."""
    for element in edited.iter():
        if element.attrib.get("id") != scope:
            continue
        if local(element.tag) == "subProcess":
            return scope
        enclosing = _enclosing_subprocess_ids(element, parents)
        return enclosing[0] if enclosing else None
    return None


def _owning_element_id(
    element: ET.Element,
    parents: dict[ET.Element, ET.Element],
) -> str:
    """The nearest ancestor-or-self carrying an id — the flow node a mapping
    child belongs to, which is what an author needs named."""
    current: ET.Element | None = element
    while current is not None:
        if current.attrib.get("id"):
            return current.attrib["id"]
        current = parents.get(current)
    return local(element.tag)


def _referencing_elements(
    variable_id: str,
    edited: ET.Element,
) -> list[ET.Element]:
    """Elements whose own attributes or text reference ``variable_id`` —
    ``var="<id>"`` or a ``vars.<id>`` expression, including inside a CDATA
    mapping body. Declarations are not references, so ``uipath:variables``
    blocks are skipped."""
    declared: set[int] = set()
    for block in edited.iter():
        if local(block.tag) == "variables":
            for node in block.iter():
                declared.add(id(node))
            declared.add(id(block))
    # A following "." is a property read (`vars.X.field`), which IS a reference;
    # only more id characters mean a different variable.
    pattern = re.compile(r"vars\.%s(?![\w-])" % re.escape(variable_id))
    matches: list[ET.Element] = []
    for element in edited.iter():
        if id(element) in declared:
            continue
        if element.attrib.get("var") == variable_id:
            matches.append(element)
            continue
        blob = " ".join(list(element.attrib.values()) + [element.text or ""])
        if pattern.search(blob):
            matches.append(element)
    return matches


def assert_variables_preserved_or_rescoped(original: ET.Element, edited: ET.Element) -> None:
    """Every pristine declaration must survive somewhere in the file, frozen
    except for its ``elementId``. A re-scope must keep the variable reachable:
    the new scope must name a live BPMN element, and moving a variable into a
    subprocess is allowed only when nothing outside that subprocess still
    references it.

    Looser than ``assert_variables_extended_only`` on purpose: an edit that
    groups nodes into a subprocess may re-scope that subprocess's own
    variables, which structural-bpmn.md documents as importing cleanly.
    Freezing the root block would fail that correct edit."""
    pristine = _declarations_anywhere(original, Side.ORIGINAL)
    if not pristine:
        fail("fixture bug: no uipath:variables declarations in the pristine original")
    current = _declarations_anywhere(edited, Side.EDITED)
    live_ids = _live_bpmn_ids(edited)
    parents = _parents(edited)

    for child_id, child in pristine.items():
        match = current.get(child_id)
        if match is None:
            fail(f"pristine variable {child_id!r} was dropped by the edit")
        if _frozen_view(child) != _frozen_view(match):
            for attribute in ("name", "type"):
                if child.attrib.get(attribute) != match.attrib.get(attribute):
                    fail(
                        f"pristine variable {child_id!r} changed its {attribute} "
                        f"({child.attrib.get(attribute)!r} -> {match.attrib.get(attribute)!r})"
                    )
            if local(child.tag) != local(match.tag):
                fail(f"pristine variable {child_id!r} changed kind (input/output/inputOutput)")
            fail(
                f"pristine variable {child_id!r} was modified — only its "
                "elementId may change"
            )
        scope = match.attrib.get("elementId")
        if child.attrib.get("elementId") and not scope:
            fail(
                f"pristine variable {child_id!r} lost its elementId (the canvas "
                "drops the declaration and every vars reference to it)"
            )
        if scope and scope not in live_ids:
            fail(f"variable {child_id!r} has a dangling elementId {scope!r}")
        if not scope or scope == child.attrib.get("elementId"):
            continue
        subprocess_id = _owning_subprocess(scope, edited, parents)
        if subprocess_id is None:
            continue
        for element in _referencing_elements(child_id, edited):
            if subprocess_id in _enclosing_subprocess_ids(element, parents):
                continue
            fail(
                f"variable {child_id!r} was re-scoped into subprocess "
                f"{subprocess_id!r} while {_owning_element_id(element, parents)!r} "
                "outside it still references it"
            )

    for child_id, child in current.items():
        if child_id in pristine:
            continue
        _assert_addition_is_well_formed(child, child_id, live_ids)


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
