#!/usr/bin/env python3
"""Structural check for the public-safety sanitization negative eval.

The fixture ships a valid BPMN seeded with fake-but-realistic private values
(a tenant URL, a folder key, a connection id, and person names). The agent must
scrub every seeded value to synthetic placeholders per references/public-safety.md
while keeping the file valid and structurally intact. This sidecar asserts NONE
of the seeded strings survive, reuses the shared require_no_private_connector_values
helper as a secondary tenant-host guard, and confirms the graph still parses.
"""

from __future__ import annotations

import os
import re
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from _shared.bpmn_check import (  # noqa: E402
    fail,
    find_bpmn_file,
    parse_bpmn,
    require_no_private_connector_values,
    require_sequence_integrity,
)

# The exact fake-but-realistic strings seeded into the fixture. All must be gone.
SEEDED = [
    "acme-corp.example.uipath.com",
    "folder-key-11111111-2222-3333-4444-555555555555",
    "connection-id-99999999-8888-7777-6666-000000000000",
    "Jane Doe (Contoso)",
    "John Smith (Fabrikam)",
]


def main() -> None:
    path, root = parse_bpmn("CustomerExport")

    text = open(find_bpmn_file("CustomerExport"), encoding="utf-8").read()
    leaked = [s for s in SEEDED if s in text]
    if leaked:
        fail(f"seeded private values still present after sanitization: {leaked}")

    # Reused shared guard: no real tenant/cloud host may remain.
    require_no_private_connector_values(root)
    # A sanitization pass must not break the graph.
    require_sequence_integrity(root)

    # Placeholder adoption: the three seeded resource fields must be replaced by
    # synthetic angle-bracket placeholders (e.g. <TENANT_URL>, <FOLDER_KEY>,
    # <CONNECTION_NAME>). ElementTree unescapes &lt;/&gt;, so this is robust to
    # however the agent XML-escaped the placeholders.
    placeholder = re.compile(r"<[A-Z][A-Z0-9_]*>")
    seen: set[str] = set()
    for el in root.iter():
        for value in list(el.attrib.values()) + ([el.text] if el.text else []):
            seen.update(placeholder.findall(value or ""))
    if len(seen) < 3:
        fail(
            "expected the seeded tenant URL, folder key, and connection id to be "
            f"replaced by synthetic <PLACEHOLDER> tokens; found {sorted(seen)}"
        )

    print(f"OK: {path} sanitized — no seeded private data remains and the graph is intact")


if __name__ == "__main__":
    main()
