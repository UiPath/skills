#!/usr/bin/env python3
"""Reachability helpers for BPMN eval checks.

Counting elements proves they exist, not that they are wired to each other. A
degenerate graph — detached gateways, a dead-end branch, an unrelated cycle —
satisfies a count-based assertion while failing the mechanism the count stands
for. These helpers let a check assert the wiring instead.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"


def edges(root: ET.Element) -> list[tuple[str, str]]:
    return [
        (f.attrib.get("sourceRef", ""), f.attrib.get("targetRef", ""))
        for f in root.findall(f".//{{{BPMN_NS}}}sequenceFlow")
    ]


def reachable(
    root: ET.Element, start: str | set[str], blocked: set[str] | None = None
) -> set[str]:
    """Every node id reachable downstream of `start`, following sequence flows.

    `blocked` nodes are not traversed, which lets a check ask whether one path
    reaches a node *without* going through another — "does the confident branch
    reach the router without passing through the human review".
    """
    starts = {start} if isinstance(start, str) else set(start)
    stop = blocked or set()
    edge_list = edges(root)
    seen: set[str] = set()
    frontier = [s for s in starts if s not in stop]

    while frontier:
        node = frontier.pop()
        for source, target in edge_list:
            if source == node and target not in seen and target not in stop:
                seen.add(target)
                frontier.append(target)

    return seen


def reaches(root: ET.Element, source: str, target: str) -> bool:
    return target in reachable(root, source)


def parent_map(root: ET.Element) -> dict[ET.Element, ET.Element]:
    """ElementTree has no parent pointers; build the map once."""
    return {child: parent for parent in root.iter() for child in parent}


def ids(elements: list[ET.Element]) -> set[str]:
    return {e.attrib.get("id", "") for e in elements}


def between(root: ET.Element, source: str, target: str) -> set[str]:
    """Nodes on some path from `source` to `target`, excluding both endpoints."""
    downstream = reachable(root, source)
    if target not in downstream:
        return set()

    # A node is on a path if it is reachable from source and can still reach target.
    return {n for n in downstream if n != target and reaches(root, n, target)}
