#!/usr/bin/env python3
"""Shared XML checks for uipath-maestro-bpmn eval tasks."""

from __future__ import annotations

import glob
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from pathlib import Path
from typing import TypeVar

_PathLike = TypeVar("_PathLike", str, Path)

NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "uipath": "http://uipath.org/schema/bpmn",
}


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def _project_files(paths: Iterable[_PathLike]) -> list[_PathLike]:
    """The subset of ``paths`` that sit beside a ``project.uiproj``.

    The single definition of "this is the real project file, not a stray draft
    copy or fixture", shared by :func:`find_bpmn_file` and
    :func:`resolve_project`. Items are returned as they were passed in, so a
    caller working in ``str`` keeps its ``str``.
    """
    return [p for p in paths if (Path(p).parent / "project.uiproj").is_file()]


def find_bpmn_file(name_hint: str | None = None) -> str:
    paths = sorted(glob.glob("**/*.bpmn", recursive=True))
    if not paths:
        fail("no BPMN file found")
    if name_hint:
        matches = [p for p in paths if name_hint.lower() in os.path.basename(p).lower()]
        if matches:
            # A hint narrows to a basename, not to a project: `Foo-old.bpmn`
            # left beside `Foo.bpmn` matches too, and sorts first. Apply
            # resolve_project's rule here as well so the draft is never graded.
            hinted = _project_files(matches)
            return hinted[0] if len(hinted) == 1 else matches[0]
        fail(f"no BPMN file found with basename matching {name_hint!r}; found: {paths}")
    if len(paths) == 1:
        return paths[0]
    projects = _project_files(paths)
    if len(projects) == 1:
        return projects[0]
    fail(f"multiple BPMN files found; expected one or hint match: {paths}")


def resolve_project(bpmn_name: str) -> Path:
    """Locate the project directory containing ``bpmn_name``.

    Grades the project wherever the agent placed it (top level or nested under
    a ``<Name>Solution/`` wrapper -- ``uip maestro bpmn init`` creates the
    wrapper unless --skip-solution-registration is passed), but picks the real
    project unambiguously: exactly one ``bpmn_name`` with project.uiproj beside
    it, so a stray draft copy is never graded (``find_bpmn_file`` would
    silently return the alphabetically-first match).
    """
    candidates = _project_files(Path.cwd().rglob(bpmn_name))
    if len(candidates) != 1:
        fail(
            f"expected exactly one {bpmn_name} with project.uiproj beside it, "
            f"found {[str(p) for p in candidates]}"
        )
    return candidates[0].parent


def parse_bpmn(name_hint: str | None = None) -> tuple[str, ET.Element]:
    path = find_bpmn_file(name_hint)
    try:
        return path, ET.parse(path).getroot()
    except ET.ParseError as exc:
        fail(f"{path} is not well-formed XML: {exc}")


def elements(root: ET.Element, local_name: str) -> list[ET.Element]:
    return root.findall(f".//bpmn:{local_name}", NS)


def one_or_more(root: ET.Element, local_name: str) -> list[ET.Element]:
    found = elements(root, local_name)
    if not found:
        fail(f"missing bpmn:{local_name}")
    return found


def attr(element: ET.Element, name: str) -> str:
    return element.attrib.get(name, "")


def text_content(element: ET.Element) -> str:
    parts: list[str] = []
    if element.text:
        parts.append(element.text)
    for child in element.iter():
        if child is not element and child.text:
            parts.append(child.text)
        if child.tail:
            parts.append(child.tail)
    return "\n".join(parts)


def context_inputs(element: ET.Element) -> list[ET.Element]:
    """Every ``uipath:input`` under ``element``, at any depth.

    ``.//`` rather than a fixed path because both layouts occur in practice:
    context/body/query/path inputs as direct children of ``uipath:activity``,
    or nested inside ``uipath:context``.
    """
    return element.findall(".//uipath:input", NS)


def context_value(element: ET.Element, name: str) -> str:
    """The value of ``element``'s ``uipath:input`` named ``name``, else ``""``.

    Reads the ``value`` attribute and falls back to the element text (agents
    write either), then strips surrounding whitespace so one artifact reads the
    same way in every grader. Name matching is exact.
    """
    for inp in context_inputs(element):
        if inp.attrib.get("name") == name:
            return (inp.attrib.get("value") or inp.text or "").strip()
    return ""


def all_node_values(element: ET.Element) -> list[str]:
    """Every populated input value under ``element`` (attribute, then text)."""
    values: list[str] = []
    for inp in context_inputs(element):
        value = inp.attrib.get("value")
        if value:
            values.append(value)
        if inp.text and inp.text.strip():
            values.append(inp.text.strip())
    return values


def has_type(element: ET.Element, token: str) -> bool:
    """True when ``token`` appears anywhere in ``element``'s serialised XML."""
    return token in ET.tostring(element, encoding="unicode")


def has_uipath_extension(element: ET.Element, token: str) -> bool:
    ext = element.find("bpmn:extensionElements", NS)
    if ext is not None and token in ET.tostring(ext, encoding="unicode"):
        return True
    return any(
        token in ET.tostring(child, encoding="unicode")
        for child in element
        if child.tag.startswith(f"{{{NS['uipath']}}}")
    )


def has_typed_uipath_extension(
    element: ET.Element, extension_name: str, type_value: str
) -> bool:
    """Match both registry-supported UiPath payload type declarations."""
    payloads = list(element.findall(f"uipath:{extension_name}", NS))
    ext = element.find("bpmn:extensionElements", NS)
    if ext is not None:
        payloads.extend(ext.findall(f"uipath:{extension_name}", NS))

    for payload in payloads:
        if payload.attrib.get("type") == type_value:
            return True
        if any(
            type_elem.attrib.get("value") == type_value
            for type_elem in payload.findall("uipath:type", NS)
        ):
            return True
    return False


def require_di_for_visible_elements(root: ET.Element) -> None:
    shaped = {shape.attrib.get("bpmnElement") for shape in root.findall(".//bpmndi:BPMNShape", NS)}
    edged = {edge.attrib.get("bpmnElement") for edge in root.findall(".//bpmndi:BPMNEdge", NS)}
    nodes = [
        *elements(root, "startEvent"),
        *elements(root, "endEvent"),
        *elements(root, "task"),
        *elements(root, "serviceTask"),
        *elements(root, "sendTask"),
        *elements(root, "receiveTask"),
        *elements(root, "userTask"),
        *elements(root, "businessRuleTask"),
        *elements(root, "scriptTask"),
        *elements(root, "callActivity"),
        *elements(root, "exclusiveGateway"),
        *elements(root, "parallelGateway"),
        *elements(root, "inclusiveGateway"),
    ]
    missing_shapes = [attr(node, "id") for node in nodes if attr(node, "id") not in shaped]
    if missing_shapes:
        fail(f"visible BPMN elements missing BPMNShape: {missing_shapes}")
    missing_edges = [
        attr(flow, "id") for flow in elements(root, "sequenceFlow") if attr(flow, "id") not in edged
    ]
    if missing_edges:
        fail(f"sequence flows missing BPMNEdge: {missing_edges}")


def require_sequence_integrity(root: ET.Element) -> None:
    ids = {attr(elem, "id") for elem in root.iter() if attr(elem, "id")}
    for flow in elements(root, "sequenceFlow"):
        source = attr(flow, "sourceRef")
        target = attr(flow, "targetRef")
        if source not in ids or target not in ids:
            fail(f"sequence flow {attr(flow, 'id')} has unresolved refs {source!r}->{target!r}")


def require_no_private_connector_values(root: ET.Element) -> None:
    # A faithful, registry-driven file legitimately contains field *names* like
    # `folderId`/`connectionId` (registry context fields), the standard
    # `exporter="UiPath (https://bpmn.uipath.com)"` attribute on the root,
    # GUID-shaped values (releaseKey, entryPointId, binding ids — present in 24
    # of the known-good fixtures), and placeholder/third-party URLs that are
    # legitimate workflow data (an A2A agent URL, a connectionless HTTP endpoint,
    # an `*.example` placeholder). The real leak to police is a baked, real
    # UiPath tenant/cloud host. Inspect populated values only.
    tenant_host = re.compile(r"\b[\w-]+\.uipath\.(com|us|gov)\b", re.IGNORECASE)

    def values(element: ET.Element) -> list[str]:
        found: list[str] = []
        for el in element.iter():
            if el is root:
                continue
            v = el.attrib.get("value")
            if v:
                found.append(v)
            if el.text and el.text.strip():
                found.append(el.text.strip())
        return found

    leaked = [value[:80] for value in values(root) if tenant_host.search(value)]
    if leaked:
        fail(f"connector boundary leaked a real tenant/cloud endpoint: {leaked}")


# A sort can ride inside a CEQL-like query string ("... ORDER BY score DESC")
# rather than a flat sort input. The CLI quotes the identifier -- the artifact
# on CI run 35538478362 emits `ORDER BY 'score' ASC` -- and agents also write
# it bare, double-quoted, backticked, or bracketed. One definition, so both
# Data Fabric query graders read the same artifact the same way.
ORDER_BY_RE = re.compile(
    r"\border\s+by\s+['\"`\[]?([a-z0-9_]+)['\"`\]]?(?:\s+(asc|desc))?", re.IGNORECASE
)


def order_by(text: str) -> tuple[str, str]:
    """``(field, direction)`` from the first ORDER BY clause in ``text``.

    Both lowercased; ``("", "")`` when there is no ORDER BY, and the direction
    is ``""`` when the clause omits ASC/DESC.
    """
    match = ORDER_BY_RE.search(text or "")
    if not match:
        return "", ""
    return match.group(1).lower(), (match.group(2) or "").lower()


def declared_variable_elements(root: ET.Element) -> list[ET.Element]:
    """Every declared variable the canvas actually reads.

    ``uipath:variables`` is honoured only on ``bpmn:process`` and
    ``bpmn:subProcess``. A block hung off any other element (a ``bpmn:userTask``,
    say) is dropped at runtime, so a document-wide ``.//uipath:variables/*``
    would credit a declaration the product rejects.
    """
    scopes = elements(root, "process") + elements(root, "subProcess")
    return [
        var
        for scope in scopes
        for var in scope.findall("bpmn:extensionElements/uipath:variables/*", NS)
    ]
