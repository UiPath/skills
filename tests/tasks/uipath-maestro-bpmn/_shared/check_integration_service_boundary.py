#!/usr/bin/env python3
"""Grade the Integration Service draft-boundary task on its artifact, not its prose.

The draft passes when its Slack step is an unresolved Integration Service node and
nothing private was invented to make it look resolved:

- the step is EITHER an ``Intsvc.*`` ``uipath:activity`` on a ``sendTask`` /
  ``serviceTask`` (the v1 XML arm writes this, and so does the v2 SDK arm's
  ``.connector()``) whose connection reads a declared binding left unresolved, OR a
  bare ``bpmn:task`` named for the Slack send (the v2 skill's form for an operation
  the connector library does not carry);
- a notes file exists, in any wording: the prompt asks for one, and which words it
  uses is the agent's call (UiPath/builder-sdk#1808 — the grader used to grep four
  v1 phrases, and a correct v2 README failed on vocabulary alone);
- no tenant host, no hand-written package file, no resolved connection id, and a
  wired, laid-out sequence.
"""

import glob
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
    attr,
    context_value,
    elements,
    fail,
    has_uipath_extension,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_hand_authored_package_files,
    require_no_private_connector_values,
    require_sequence_integrity,
    root_bindings,
)

# The connector the task prompt names. A bare-task draft must name it, and name a
# send, so "Prepare Slack digest" does not stand in for the missing send step.
CONNECTOR_NAME = "slack"
SEND_WORD = re.compile(r"\b(send|post|message|notify|deliver|digest\s+to)\b", re.IGNORECASE)
GUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
BINDING_READ = re.compile(r"^=bindings\.([\w.-]+)$")


def intsvc_nodes(root: ET.Element) -> list[ET.Element]:
    wrappers = [*elements(root, "sendTask"), *elements(root, "serviceTask")]
    return [task for task in wrappers if has_uipath_extension(task, "Intsvc.")]


def bare_connector_tasks(root: ET.Element) -> list[ET.Element]:
    found = []
    for task in elements(root, "task"):
        name = attr(task, "name")
        if CONNECTOR_NAME in name.lower() and SEND_WORD.search(name):
            found.append(task)
    return found


def require_connection_unresolved(root: ET.Element, node: ET.Element) -> None:
    """The node reads its connection through a declared binding with no real id.

    Both arms declare bindings in the process's ``uipath:bindings``; an unresolved
    one carries a symbolic or placeholder default (``slack``, ``<connection-id>``) or
    none. A GUID there is a resolved connection, or an invented one: either way the
    draft crossed the CLI-owned boundary. ``bindings_v2.json`` is held to the same
    rule by ``require_no_hand_authored_package_files``.
    """
    node_id = attr(node, "id")
    bindings = root_bindings(root)
    connection = context_value(node, "connection")
    match = BINDING_READ.match(connection)
    if not match:
        if GUID.match(connection):
            fail(f"{node_id}: connection is a literal connection id ({connection}); leave it to a binding the CLI resolves")
        fail(f"{node_id}: connection must read a declared binding (`=bindings.<id>`), found {connection!r}")
    binding_id = match.group(1)
    if binding_id not in bindings:
        fail(f"{node_id}: connection reads `=bindings.{binding_id}`, but the process declares no such binding (declared: {sorted(bindings)})")
    reads = {binding_id: "connection"}
    folder = BINDING_READ.match(context_value(node, "folderKey"))
    if folder and folder.group(1) in bindings:
        reads[folder.group(1)] = "folderKey"
    elif GUID.match(context_value(node, "folderKey")):
        fail(f"{node_id}: folderKey is a literal folder key; leave it to a binding the CLI resolves")
    for bid, role in reads.items():
        b = bindings[bid]
        for key in ("default", "resourceKey"):
            value = (b.get(key) or "").strip()
            if GUID.match(value):
                fail(f"{node_id}: {role} binding `{bid}` has a resolved id in {key} ({value}); a draft leaves the connection binding unresolved")


def require_notes() -> None:
    notes = [
        p
        for p in sorted(glob.glob("**/*.md", recursive=True))
        if "node_modules" not in Path(p).parts
        and not Path(p).name.startswith("SKILL")
        and Path(p).read_text(encoding="utf-8").strip()
    ]
    if not notes:
        fail("no README or notes .md file: the task asks for one stating the CLI-owned blockers")


def main() -> None:
    path, root = parse_bpmn("SlackDigestBoundaryBpmn")
    nodes = intsvc_nodes(root)
    bare = bare_connector_tasks(root)
    if not nodes and not bare:
        fail(
            "missing the draft Slack step: expected an Intsvc.* uipath:activity on a "
            "sendTask/serviceTask, or a bare bpmn:task named for the Slack send"
        )
    for node in nodes:
        require_connection_unresolved(root, node)
    require_no_private_connector_values(root)
    # Draft boundary: connection binding + package metadata are CLI-owned. Files the
    # CLI wrote (`init` / `refresh`) are that boundary; hand-written ones, or a
    # resolved connection id, are what breach it — see require_no_hand_authored_package_files.
    require_no_hand_authored_package_files()
    require_notes()
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    form = "Intsvc node with an unresolved connection binding" if nodes else "bare task naming the connector"
    print(f"OK: {path} keeps Integration Service details in the CLI-owned boundary ({form})")


if __name__ == "__main__":
    main()
