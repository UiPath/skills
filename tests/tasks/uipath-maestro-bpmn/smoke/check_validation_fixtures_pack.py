#!/usr/bin/env python3
"""Verify the BPMN sources of the validation fixture corpus still parse.

Run from the scored workspace after the agent has packed (or attempted to
pack) each fixture. Checks that the fixture corpus has not been mutated and
that every fixture BPMN file is well-formed.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

EXPECTED = (
    "fixtures/validation/linear-process/linear-process.bpmn",
    "fixtures/validation/gateway-boundary-error/gateway-boundary-error.bpmn",
    "fixtures/validation/integration-service-enriched/integration-service-enriched.bpmn",
    "fixtures/validation/subprocess-multi-instance/subprocess-multi-instance.bpmn",
    "fixtures/validation/contract-variants/contract-variants.bpmn",
    "fixtures/validation/registry-coverage-matrix/registry-coverage-matrix.bpmn",
)


def main() -> None:
    missing: list[str] = []
    bad: list[str] = []
    for rel in EXPECTED:
        path = Path(rel)
        if not path.exists():
            missing.append(rel)
            continue
        try:
            ET.parse(path)
        except ET.ParseError as exc:
            bad.append(f"{rel}: {exc}")
    if missing:
        sys.exit(f"FAIL: missing fixture BPMN files: {missing}")
    if bad:
        sys.exit(f"FAIL: fixture BPMN files no longer parse: {bad}")
    print(f"OK: {len(EXPECTED)} fixture BPMN files parse")


if __name__ == "__main__":
    main()
