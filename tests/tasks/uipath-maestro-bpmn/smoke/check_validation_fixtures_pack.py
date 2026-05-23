#!/usr/bin/env python3
"""Verify the validation fixture corpus still parses and was pack-attempted.

Run from the scored workspace after the agent has packed each fixture. Checks
that the fixture corpus has not been mutated, every fixture BPMN file is
well-formed, and runtime-packable fixtures produced local package artifacts
outside fixture folders.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

EXPECTED = (
    "fixtures/validation/linear-process/linear-process.bpmn",
    "fixtures/validation/imported-brownfield-preservation/imported-brownfield-preservation.bpmn",
    "fixtures/validation/gateway-boundary-error/gateway-boundary-error.bpmn",
    "fixtures/validation/integration-service-enriched/integration-service-enriched.bpmn",
    "fixtures/validation/subprocess-multi-instance/subprocess-multi-instance.bpmn",
    "fixtures/validation/contract-variants/contract-variants.bpmn",
    "fixtures/validation/registry-coverage-matrix/registry-coverage-matrix.bpmn",
    "fixtures/validation/wrapper-family-contract/wrapper-family-contract.bpmn",
    "fixtures/validation/agent-invocation/agent-invocation.bpmn",
)

PACKABLE_FIXTURES = {
    "agent-invocation",
    "imported-brownfield-preservation",
    "integration-service-enriched",
    "registry-coverage-matrix",
    "subprocess-multi-instance",
    "wrapper-family-contract",
}

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

    packages = sorted(PACKAGE_OUTPUT.rglob("*.nupkg"))
    package_names = {path.name.split(".processOrchestration.", 1)[0] for path in packages}
    missing_packages = sorted(PACKABLE_FIXTURES - package_names)
    if missing_packages:
        sys.exit(
            "FAIL: expected package artifacts for runtime-packable fixtures, "
            f"missing: {missing_packages}"
        )
    fixture_package_paths = [
        str(path) for path in packages if "fixtures/validation" in path.as_posix()
    ]
    if fixture_package_paths:
        sys.exit(
            f"FAIL: package artifacts were written under fixture folders: {fixture_package_paths}"
        )

    print(
        f"OK: {len(EXPECTED)} fixture BPMN files parse and "
        f"{len(packages)} runtime-packable fixture packages exist"
    )


if __name__ == "__main__":
    main()
