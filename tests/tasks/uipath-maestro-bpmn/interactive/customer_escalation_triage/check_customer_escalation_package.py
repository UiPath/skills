#!/usr/bin/env python3
"""Independently pack the BPMN project and inspect the produced NuGet archive."""

from __future__ import annotations

import json
import os
import re
import sys
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any, NoReturn

# Walk up to the directory that holds `_shared` so the import works regardless
# of how deep this task lives under tests/tasks/uipath-maestro-bpmn/.
_directory = os.path.dirname(os.path.abspath(__file__))
while _directory != os.path.dirname(_directory) and not os.path.isdir(
    os.path.join(_directory, "_shared")
):
    _directory = os.path.dirname(_directory)
sys.path.insert(0, _directory)

from _shared import bpmn_live  # noqa: E402



PROJECT = Path("CustomerEscalationTriageSolution") / "CustomerEscalationTriage"
EXPECTED_ARCHIVE_BASENAMES = {
    "CustomerEscalationTriage.bpmn",
    "bindings_v2.json",
    "entry-points.json",
    "operate.json",
    "package-descriptor.json",
}


UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
STUB_UUID_PATTERN = re.compile(r"^0{8}-0{4}-0{4}-0{4}-")


def is_real_connection_key(value: Any) -> bool:
    """True only for a real connection id, not an unresolved stub."""

    rendered = str(value or "").strip()
    return bool(UUID_PATTERN.fullmatch(rendered)) and not STUB_UUID_PATTERN.match(
        rendered
    )


def fail(message: str) -> NoReturn:
    raise SystemExit(f"FAIL: {message}")


def parse_json_output(text: str) -> Any:
    """Delegate to the shared parser, keeping this script's FAIL: convention.

    Was a third verbatim copy of the same banner-tolerant parse.
    """

    try:
        return bpmn_live.parse_json_output(text, "pack")
    except bpmn_live.CheckFailure as exc:
        fail(str(exc))


def main() -> None:
    if not PROJECT.is_dir():
        fail(f"missing project directory: {PROJECT}")
    with tempfile.TemporaryDirectory(prefix="bpmn-eval-pack-") as output_dir:
        result = subprocess.run(
            [
                "uip",
                "maestro",
                "bpmn",
                "pack",
                str(PROJECT),
                output_dir,
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=150,
        )
        if result.returncode != 0:
            fail(
                f"pack exited {result.returncode}\nstdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
        payload = parse_json_output(result.stdout)
        if not isinstance(payload, dict) or str(payload.get("Result", "")).casefold() != "success":
            fail(f"pack JSON did not report Success: {payload}")

        packages = list(Path(output_dir).glob("*.nupkg"))
        if len(packages) != 1:
            fail(f"expected exactly one .nupkg, found: {[path.name for path in packages]}")
        package = packages[0]
        if package.stat().st_size <= 0:
            fail(f"packed archive is empty: {package.name}")
        if not zipfile.is_zipfile(package):
            fail(f"packed file is not a valid NuGet/ZIP archive: {package.name}")

        with zipfile.ZipFile(package) as archive:
            names = set(archive.namelist())
            by_basename = {Path(name).name: name for name in names}
            missing = sorted(EXPECTED_ARCHIVE_BASENAMES - set(by_basename))
            if missing:
                fail(f"packed archive is missing expected content: {missing}")
            bpmn_payload = archive.read(by_basename["CustomerEscalationTriage.bpmn"])
            if len(bpmn_payload) < 200:
                fail("packed BPMN content is implausibly small")
            bindings = json.loads(
                archive.read(by_basename["bindings_v2.json"])
            )
            resources = bindings.get("resources")
            if (
                not isinstance(resources, list)
                or len(resources) != 3
                or any(
                    not isinstance(resource, dict)
                    or resource.get("resource") != "Connection"
                    for resource in resources
                )
            ):
                fail(
                    "packed bindings_v2.json must contain exactly three "
                    "Connection resources"
                )
            # A truthy key is not enough: an all-zero UUID is what the CLI
            # writes for an unresolved binding, so accepting any non-empty
            # string lets a stub-bound project pass a criterion that is
            # supposed to prove real wiring. Mirrors
            # uipath-maestro-flow/_shared/check_bindings_no_stubs.py.
            stubbed = [
                resource.get("key")
                for resource in resources
                if not is_real_connection_key(resource.get("key"))
            ]
            if stubbed:
                fail(
                    "packed bindings_v2.json Connection keys must be real "
                    f"connection ids, not unresolved stubs: {stubbed}"
                )

        print(
            f"OK: independently packed {package.name} ({package.stat().st_size} bytes) "
            "with BPMN, connector resources, and package metadata content"
        )


if __name__ == "__main__":
    main()
