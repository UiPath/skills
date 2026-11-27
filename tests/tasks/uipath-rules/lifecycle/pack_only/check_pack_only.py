#!/usr/bin/env python3
"""Grades the pack-only task from the artifacts on disk.

Passes when the sandbox holds a solution package (the zip `uip solution pack`
writes: packageInfo.json plus files/<projectId>/<name>.uirule) whose ShippingRules
.uirule carries the project's `.dmn` and `entry-points.json` byte for byte, and the
project itself is unchanged from the fixture: packing must not edit the rule.
"""

from __future__ import annotations

import filecmp
import io
import json
import os
import sys
import zipfile
from pathlib import Path

PROJECT = Path("Logistics") / "ShippingRules"
FIXTURE = Path(__file__).resolve().parents[2] / "_fixtures" / "solution_with_rule" / PROJECT
SKIP_DIRS = {"node_modules", ".venv", ".git", "_setup"}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def solution_zips() -> list[Path]:
    found = []
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if not name.endswith(".zip"):
                continue
            path = Path(dirpath) / name
            try:
                with zipfile.ZipFile(path) as z:
                    names = z.namelist()
            except zipfile.BadZipFile:
                continue
            if "packageInfo.json" in names and any(n.startswith("files/") and n.endswith(".uirule") for n in names):
                found.append(path)
    return found


def project_id() -> str:
    projects = json.loads((Path("Logistics") / "Logistics.uipx").read_text(encoding="utf-8")).get("Projects") or []
    ids = [p.get("Id") for p in projects if p.get("ProjectRelativePath") == "ShippingRules/project.uiproj"]
    if len(ids) != 1:
        fail("Logistics.uipx no longer lists ShippingRules exactly once")
    return ids[0]


def packed_rule(zip_path: Path, rule_id: str) -> dict[str, bytes] | None:
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if name.startswith(f"files/{rule_id}/") and name.endswith(".uirule"):
                with zipfile.ZipFile(io.BytesIO(z.read(name))) as rule:
                    return {inner: rule.read(inner) for inner in rule.namelist()}
    return None


def main() -> None:
    for file in sorted(p.relative_to(FIXTURE) for p in FIXTURE.rglob("*") if p.is_file()):
        if not (PROJECT / file).is_file() or not filecmp.cmp(FIXTURE / file, PROJECT / file, shallow=False):
            fail(f"{PROJECT / file} changed or is gone; packing must not edit the rule")
    zips = solution_zips()
    if not zips:
        fail("no solution package (a zip with packageInfo.json and files/*/*.uirule) in the sandbox")
    rule_id = project_id()
    for zip_path in zips:
        packed = packed_rule(zip_path, rule_id)
        if packed is None:
            continue
        for name in ("Business rule.dmn", "entry-points.json"):
            if packed.get(name) != (PROJECT / name).read_bytes():
                fail(f"{zip_path} packs a {name} that is not the project's")
        print(f"OK: {zip_path} carries ShippingRules with its .dmn and contract; the project is unchanged")
        return
    fail(f"solution package(s) {[str(z) for z in zips]} hold no .uirule for ShippingRules ({rule_id})")


if __name__ == "__main__":
    main()
