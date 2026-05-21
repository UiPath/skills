#!/usr/bin/env python3
"""Verify the validation fixture corpus parses and selected fixtures package.

Run from the scored workspace after the agent has packed the runtime-packable
fixture subset. Checks that the fixture corpus has not been mutated, every
fixture BPMN file is well-formed, and local package artifacts were produced
outside fixture folders.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

EXPECTED_BPMN = (
    "fixtures/validation/linear-process/linear-process.bpmn",
    "fixtures/validation/imported-brownfield-preservation/imported-brownfield-preservation.bpmn",
    "fixtures/validation/gateway-boundary-error/gateway-boundary-error.bpmn",
    "fixtures/validation/integration-service-enriched/integration-service-enriched.bpmn",
    "fixtures/validation/subprocess-multi-instance/subprocess-multi-instance.bpmn",
    "fixtures/validation/contract-variants/contract-variants.bpmn",
    "fixtures/validation/registry-coverage-matrix/registry-coverage-matrix.bpmn",
    "fixtures/validation/wrapper-family-contract/wrapper-family-contract.bpmn",
)

EXPECTED_PACKAGES = (
    "integration-service-enriched",
    "registry-coverage-matrix",
    "wrapper-family-contract",
)

PACKAGE_OUTPUT = Path("fixture-pack-output")


def main() -> None:
    missing: list[str] = []
    bad: list[str] = []
    for rel in EXPECTED_BPMN:
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
    fixture_package_paths = [
        str(path) for path in packages if "fixtures/validation" in path.as_posix()
    ]
    if fixture_package_paths:
        sys.exit(
            f"FAIL: package artifacts were written under fixture folders: {fixture_package_paths}"
        )

    missing_packages = [
        name
        for name in EXPECTED_PACKAGES
        if not any(path.name.startswith(f"{name}.") for path in packages)
    ]
    if missing_packages:
        sys.exit(
            "FAIL: missing expected package artifacts under "
            f"{PACKAGE_OUTPUT}: {missing_packages}"
        )

    print(
        f"OK: {len(EXPECTED_BPMN)} fixture BPMN files parse and "
        f"{len(EXPECTED_PACKAGES)} required packages exist"
    )


if __name__ == "__main__":
    main()
