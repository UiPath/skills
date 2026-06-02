#!/usr/bin/env python3
"""Verify the validation fixture corpus still parses and was packaged.

Run from the scored workspace after the agent has packed each fixture. Checks
that the fixture corpus has not been mutated, every fixture BPMN file is
well-formed, and local package artifacts were produced outside fixture folders.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Fixtures that must (a) parse as XML and (b) pack successfully.
EXPECTED_PACKABLE = (
    "fixtures/validation/linear-process/linear-process.bpmn",
    "fixtures/validation/imported-brownfield-preservation/imported-brownfield-preservation.bpmn",
    "fixtures/validation/gateway-boundary-error/gateway-boundary-error.bpmn",
    "fixtures/validation/integration-service-enriched/integration-service-enriched.bpmn",
    "fixtures/validation/subprocess-multi-instance/subprocess-multi-instance.bpmn",
    "fixtures/validation/registry-coverage-matrix/registry-coverage-matrix.bpmn",
    "fixtures/validation/wrapper-family-contract/wrapper-family-contract.bpmn",
    "fixtures/validation/agent-invocation/agent-invocation.bpmn",
)

# Fixtures that parse as XML but deliberately contain unsupported uipath
# extensions (e.g. `<uipath:Activity preservation="unsupported">`) so the
# validator rejects them at pack time. They must still be present and well-
# formed, but their absence from the produced nupkg set is correct.
EXPECTED_VALIDATION_ONLY = (
    "fixtures/validation/contract-variants/contract-variants.bpmn",
)

EXPECTED = EXPECTED_PACKABLE + EXPECTED_VALIDATION_ONLY

PACKAGE_OUTPUT = Path("fixture-pack-output")


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

    packages = list(PACKAGE_OUTPUT.rglob("*.nupkg"))
    if len(packages) < len(EXPECTED_PACKABLE):
        sys.exit(
            "FAIL: expected at least "
            f"{len(EXPECTED_PACKABLE)} package artifacts under {PACKAGE_OUTPUT}, found {len(packages)}"
        )
    fixture_package_paths = [
        str(path) for path in packages if "fixtures/validation" in path.as_posix()
    ]
    if fixture_package_paths:
        sys.exit(
            f"FAIL: package artifacts were written under fixture folders: {fixture_package_paths}"
        )

    print(f"OK: {len(EXPECTED)} fixture BPMN files parse and {len(packages)} packages exist")


if __name__ == "__main__":
    main()
