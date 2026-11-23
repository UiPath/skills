#!/usr/bin/env python3
"""Grade the Integration Service draft-boundary task on its artifact, not its prose.

The draft passes when its Slack step is an unresolved Integration Service node and
nothing private was invented to make it look resolved:

- the step is EITHER an ``Intsvc.*`` ``uipath:activity`` on a ``sendTask`` /
  ``serviceTask`` (the v1 XML arm writes this, and so does the v2 SDK arm's
  ``.connector()``) whose connection reads a declared binding left unresolved, OR a
  bare ``bpmn:task`` (no Intsvc payload) whose name carries the connector key and a
  sending verb, the v2 skill's placeholder for an operation it cannot resolve;
- a notes file the agent wrote exists, in any wording;
  ``--notes-vocabulary`` checks, on its own, that the notes name the four CLI-owned
  blockers;
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

# A bare-task draft names the connector by its key, so the placeholder records which
# Integration Service connector it stands for ("Send Slack digest" alone carries no
# connector intent), plus a sending verb, so a preparation step does not stand in for
# the send. Nouns ("message") are not verbs.
CONNECTOR_KEY = "uipath-salesforce-slack"
SEND_WORD = re.compile(r"\b(send|sends|sending|post|posts|posting|notify|deliver|publish|dispatch)\b", re.IGNORECASE)
# Files an agent did not write: agent instructions an image or harness may stage.
NOT_NOTES = {"CLAUDE.md", "AGENTS.md"}
# The four CLI-owned blockers, each in any reasonable phrasing.
BLOCKERS = {
    "connection binding": re.compile(r"connection\s+binding", re.IGNORECASE),
    "dynamic schema(s)": re.compile(r"dynamic\s+(\w+\s+){0,4}schema", re.IGNORECASE),
    "bindings_v2.json": re.compile(r"bindings_v2\.json", re.IGNORECASE),
    "package metadata": re.compile(r"package\s+metadata", re.IGNORECASE),
}
GUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
BINDING_READ = re.compile(r"^=bindings\.([\w.-]+)$")


def intsvc_nodes(root: ET.Element) -> list[ET.Element]:
    wrappers = [*elements(root, "sendTask"), *elements(root, "serviceTask")]
    return [task for task in wrappers if has_uipath_extension(task, "Intsvc.")]


def bare_connector_tasks(root: ET.Element) -> list[ET.Element]:
    found = []
    for task in elements(root, "task"):
        # A bpmn:task carrying an Intsvc payload is not a bare placeholder: it is a
        # connector node on the wrong wrapper, and it would dodge the binding check.
        if has_uipath_extension(task, "Intsvc."):
            continue
        name = attr(task, "name")
        if CONNECTOR_KEY in name.lower() and SEND_WORD.search(name):
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
    folder_value = context_value(node, "folderKey")
    folder = BINDING_READ.match(folder_value)
    if folder:
        if folder.group(1) not in bindings:
            fail(f"{node_id}: folderKey reads `=bindings.{folder.group(1)}`, but the process declares no such binding (declared: {sorted(bindings)})")
        reads[folder.group(1)] = "folderKey"
    elif GUID.match(folder_value):
        fail(f"{node_id}: folderKey is a literal folder key; leave it to a binding the CLI resolves")
    for bid, role in reads.items():
        b = bindings[bid]
        for key in ("default", "resourceKey"):
            value = (b.get(key) or "").strip()
            if GUID.match(value):
                fail(f"{node_id}: {role} binding `{bid}` has a resolved id in {key} ({value}); a draft leaves the connection binding unresolved")


def notes_text() -> str:
    """Every non-empty notes file the agent left, wherever it put it.

    The prompt names no location: v1 writes it beside the .bpmn, the builder-SDK arm
    at the workspace root. Neither `uip maestro bpmn init` nor the SDK writes a .md,
    so what remains after skipping installed packages, dot-directories, skill copies
    and agent-instruction files is the agent's own.
    """
    texts = []
    for p in sorted(glob.glob("**/*.md", recursive=True)):
        path = Path(p)
        if "node_modules" in path.parts or any(part.startswith(".") for part in path.parts[:-1]):
            continue
        if path.name.startswith("SKILL") or path.name in NOT_NOTES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            texts.append(text)
    return "\n".join(texts)


def require_notes() -> None:
    if not notes_text():
        fail("no README or notes .md file: the task asks for one stating the CLI-owned blockers")


def notes_vocabulary() -> None:
    """Advisory: do the notes name the four CLI-owned blockers, in any phrasing?"""
    text = notes_text()
    missing = [name for name, pattern in BLOCKERS.items() if not pattern.search(text)]
    if missing:
        fail(f"notes do not name CLI-owned blockers: {missing}")
    print("OK: notes name connection binding, dynamic schemas, bindings_v2.json and package metadata")


def main() -> None:
    path, root = parse_bpmn("SlackDigestBoundaryBpmn")
    nodes = intsvc_nodes(root)
    bare = bare_connector_tasks(root)
    if not nodes and not bare:
        if any(has_uipath_extension(task, "Intsvc.") for task in elements(root, "task")):
            fail("the Intsvc.* activity sits on a bare bpmn:task; a connector node is a sendTask or serviceTask")
        fail(
            "missing the draft Slack step: expected an Intsvc.* uipath:activity on a "
            f"sendTask/serviceTask, or a bare bpmn:task whose name carries {CONNECTOR_KEY} and a sending verb"
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
    if sys.argv[1:] == ["--notes-vocabulary"]:
        notes_vocabulary()
    else:
        main()
