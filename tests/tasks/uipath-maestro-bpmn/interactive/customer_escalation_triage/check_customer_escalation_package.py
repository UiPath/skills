#!/usr/bin/env python3
"""Independently pack the BPMN project and inspect the produced NuGet archive."""

from __future__ import annotations

import json
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any, NoReturn


PROJECT = Path("CustomerEscalationTriage")
EXPECTED_ARCHIVE_BASENAMES = {
    "CustomerEscalationTriage.bpmn",
    "bindings_v2.json",
    "entry-points.json",
    "operate.json",
    "package-descriptor.json",
}


def fail(message: str) -> NoReturn:
    raise SystemExit(f"FAIL: {message}")


def parse_json_output(text: str) -> Any:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    for index, character in enumerate(stripped):
        if character not in "[{":
            continue
        try:
            return json.loads(stripped[index:])
        except json.JSONDecodeError:
            continue
    fail(f"pack did not return JSON: {text}")


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

        print(
            f"OK: independently packed {package.name} ({package.stat().st_size} bytes) "
            "with BPMN and package metadata content"
        )


if __name__ == "__main__":
    main()
