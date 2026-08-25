#!/usr/bin/env python3
"""Shared XML checks for uipath-maestro-bpmn eval tasks."""

from __future__ import annotations

import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "uipath": "http://uipath.org/schema/bpmn",
}


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def find_bpmn_file(name_hint: str | None = None) -> str:
    paths = sorted(glob.glob("**/*.bpmn", recursive=True))
    if not paths:
        fail("no BPMN file found")
    if name_hint:
        matches = [p for p in paths if name_hint.lower() in os.path.basename(p).lower()]
        if matches:
            return matches[0]
        fail(f"no BPMN file found with basename matching {name_hint!r}; found: {paths}")
    if len(paths) == 1:
        return paths[0]
    fail(f"multiple BPMN files found; expected one or hint match: {paths}")


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


def has_uipath_extension(element: ET.Element, token: str) -> bool:
    ext = element.find("bpmn:extensionElements", NS)
    return ext is not None and token in ET.tostring(ext, encoding="unicode")


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
