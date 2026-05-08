#!/usr/bin/env python3
"""Shared XML checks for uipath-maestro-bpmn eval tasks."""

from __future__ import annotations

import glob
import os
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
        *elements(root, "scriptTask"),
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
    private_tokens = [
        "connectionId",
        "connectionKey",
        "tenant",
        "folderKey",
        "folderId",
        "https://",
    ]
    xml = ET.tostring(root, encoding="unicode")
    present = [token for token in private_tokens if token in xml]
    if present:
        fail(f"connector boundary leaked private or CLI-owned fields: {present}")
