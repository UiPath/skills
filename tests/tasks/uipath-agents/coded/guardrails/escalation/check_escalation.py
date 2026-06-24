#!/usr/bin/env python3
"""Structural checks for coded guardrail HITL escalation.

The task intentionally avoids tenant connectivity, so this checks the
load-bearing local artifacts: EscalateAction usage and a well-formed app
binding for the Action Center review app.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd())

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from _shared.bindings_assertions import (  # noqa: E402
    assert_metadata_field,
    assert_value_field,
    find_resource,
    load_bindings,
)


def main() -> None:
    graph = (ROOT / "graph.py").read_text()
    required = [
        "EscalateAction",
        "Guardrail.Escalation.Action.App",
        "Shared",
        "TaskRecipient",
        "reviewer@example.com",
    ]
    for token in required:
        if token not in graph:
            sys.exit(f"FAIL: graph.py is missing {token!r}")
    print("OK: graph.py contains EscalateAction app, folder, and recipient wiring")

    doc = load_bindings(ROOT / "bindings.json")
    app = find_resource(
        doc,
        resource="app",
        key="Guardrail.Escalation.Action.App.Shared",
    )
    assert_value_field(app, field="name", expected="Guardrail.Escalation.Action.App")
    assert_value_field(app, field="folderPath", expected="Shared")
    assert_metadata_field(app, field="ActivityName", expected="create_async")
    assert_metadata_field(app, field="DisplayLabel", expected="Guardrail.Escalation.Action.App")


if __name__ == "__main__":
    main()
