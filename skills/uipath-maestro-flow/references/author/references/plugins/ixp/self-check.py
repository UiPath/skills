#!/usr/bin/env python3
"""
IxP node self-check — canonical source.

Enforces Authoring rules #1, #3, #4, #5, #6 from impl.md. Run on the
generated `.flow` file BEFORE `uip maestro flow validate`. Exits 0 when
the file is clean, 1 when any rule is violated.

DO NOT MODIFY THIS SCRIPT TO SUPPRESS A FAILURE. The rules encode
runtime invariants (Studio Web canvas destructure, `$vars` resolution,
schema drift) that `flow validate` cannot catch. A failure here means
the `.flow` file is broken — fix the flow, not the check.

The inline heredoc form embedded in impl.md ("Self-check before
`uip maestro flow validate`") is a flattened, function-free version of
the same checks. The two forms are NOT byte-equivalent — this file
wraps the logic in `check_flow()` / `main()`, the heredoc inlines it —
but they MUST stay logically equivalent: the same FORBIDDEN_INPUT_FIELDS
set, the same per-node assertions, the same rule numbers, the same exit
codes. When changing one, change the other.
"""
from __future__ import annotations

import json
import sys


FORBIDDEN_INPUT_FIELDS = {
    "digitizationMode",
    "documentTaxonomy",
    "attachmentId",
    "fileName",
    "mimeType",
}


def check_flow(path: str) -> list[str]:
    with open(path) as fh:
        flow = json.load(fh)
    errors: list[str] = []
    for node in flow.get("nodes") or []:
        if not isinstance(node, dict):
            continue
        if not str(node.get("type", "")).startswith("uipath.ixp."):
            continue
        nid = node.get("id", "?")
        inputs = node.get("inputs") or {}
        outputs = node.get("outputs") or {}
        model = inputs.get("model")
        if not isinstance(model, dict) or not model.get("modelName") or not model.get("folderKey"):
            errors.append(
                f"{nid}: rule #1 — inputs.model.{{modelName,folderKey}} must be present "
                f"(canvas crashes with 'Cannot destructure property modelName' otherwise)"
            )
        fileRef = inputs.get("fileRef", "")
        if not isinstance(fileRef, str) or not fileRef.startswith("=js:$vars."):
            errors.append(
                f"{nid}: rule #3 — inputs.fileRef must be '=js:$vars.<upstream>.output.<field>'"
            )
        for port in ("output", "error"):
            if port not in outputs:
                errors.append(
                    f"{nid}: rule #4 — outputs.{port} required (downstream $vars.{nid}.{port} won't resolve)"
                )
        legacy = sorted(FORBIDDEN_INPUT_FIELDS & set(inputs.keys()))
        if legacy:
            errors.append(
                f"{nid}: rule #6 — forbidden legacy fields in inputs: {legacy} "
                f"(removed from current schema; registry-get does NOT return these)"
            )
        if node.get("model") is not None:
            errors.append(f"{nid}: rule #5 — top-level 'model' on instance (must live in definitions[])")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: self-check.py <ProjectName>.flow", file=sys.stderr)
        return 2
    errors = check_flow(sys.argv[1])
    if errors:
        print("IxP self-check FAILED", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    print("IxP self-check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
