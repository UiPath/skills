#!/usr/bin/env python3
"""Checks for a genome execution (Execute mode) run, from the sandbox root.

Usage:
  execute_check.py build                       the one RPA project built from the genome compiles (uip rpa build)
  execute_check.py settings --expect NAME …    that project reads every named setting as an Orchestrator asset:
                                               each name appears in its workflows, code or configuration file
  execute_check.py open-items --expect TOKEN … one top-level *-open-items.md, outside every project, with the
                                               always-present sections and every expected token
  execute_check.py genome-unchanged <genome> <reference>   execution left the genome byte-identical

Cross-platform on purpose: coder-eval runs run_command through cmd.exe on Windows, so criteria call this
script through `python -c` and read REFERENCE_DIR from the environment. Exit 0 on pass, 1 with a reason.
"""

import argparse
import filecmp
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

SKIP_DIRS = {".local", ".git", "node_modules", ".venv", ".upgrade", "fixtures"}
SECTIONS = ["## Access", "## Package and deployment", "## Assets", "## Others", "## Triggers"]


def rpa_projects(root: Path) -> list[Path]:
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if "project.json" in filenames:
            try:
                manifest = json.loads((Path(dirpath) / "project.json").read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                continue
            if "main" in manifest or "entryPoints" in manifest:
                found.append(Path(dirpath).resolve())
    return found


def one_project() -> Path:
    projects = rpa_projects(Path("."))
    if len(projects) != 1:
        sys.exit(f"FAIL: expected exactly one RPA project, found {len(projects)}: {', '.join(map(str, projects)) or 'none'}")
    return projects[0]


def cmd_build(_: argparse.Namespace) -> int:
    project = one_project()
    uip = shutil.which("uip") or "uip"
    code = subprocess.call([uip, "rpa", "build", str(project), "--output", "json"])
    print(("OK" if code == 0 else "FAIL") + f": uip rpa build {project} exited {code}")
    return 0 if code == 0 else 1


ASSET_READ = re.compile(r"AssetName|GetAsset|GetRobotAsset|GetCredential", re.I)


def setting_reads(project: Path) -> tuple[str, str]:
    """(code, workbooks): the text of every workflow and code file, and of every configuration workbook."""
    code, books = [], []
    for dirpath, dirnames, filenames in os.walk(project):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            path = Path(dirpath) / name
            suffix = path.suffix.lower()
            try:
                if suffix in {".xaml", ".cs", ".vb"}:
                    code.append(path.read_text(encoding="utf-8", errors="ignore"))
                elif suffix == ".xlsx":
                    with zipfile.ZipFile(path) as z:
                        books += [z.read(n).decode("utf-8", "ignore") for n in z.namelist() if n.endswith(".xml")]
            except (OSError, zipfile.BadZipFile):
                continue
    return "\n".join(code), "\n".join(books)


def cmd_settings(a: argparse.Namespace) -> int:
    """Each setting is read as an Orchestrator asset: its name sits within an asset read in a workflow or
    code file, or in a configuration workbook (the REFramework's Assets sheet names the assets it reads).
    A name read some other way — an environment variable, a literal default — does not count."""
    project = one_project()
    code, books = setting_reads(project)
    missing = []
    for n in a.expect:
        near_asset_read = any(abs(m.start() - h.start()) <= 300 for h in re.finditer(re.escape(n), code)
                              for m in ASSET_READ.finditer(code))
        if not near_asset_read and n not in books:
            missing.append(n)
    if missing:
        print(f"FAIL: {project.name} does not read these settings as Orchestrator assets: {', '.join(missing)}")
        return 1
    print(f"OK: {project.name} reads {', '.join(a.expect)} as Orchestrator assets")
    return 0


def cmd_open_items(a: argparse.Namespace) -> int:
    files = sorted(Path(".").glob("*-open-items.md"))
    if len(files) != 1:
        print(f"FAIL: expected exactly one top-level *-open-items.md, found {len(files)}")
        return 1
    projects = rpa_projects(Path("."))
    errors = [f"{files[0]} sits inside project {p}" for p in projects if p in files[0].resolve().parents]
    text = files[0].read_text(encoding="utf-8")
    errors += [f"missing section '{s}'" for s in SECTIONS if not any(l.strip() == s for l in text.splitlines())]
    errors += [f"missing '{t}'" for t in a.expect if t not in text]
    if "- [ ]" not in text:
        errors.append("no checklist item")
    for e in errors:
        print(f"FAIL: {files[0].name}: {e}")
    if not errors:
        print(f"OK: {files[0]}")
    return 1 if errors else 0


def cmd_genome_unchanged(a: argparse.Namespace) -> int:
    same = Path(a.genome).is_file() and filecmp.cmp(a.genome, a.reference, shallow=False)
    print(("OK" if same else "FAIL") + f": {a.genome} {'matches' if same else 'differs from'} the reference")
    return 0 if same else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build").set_defaults(func=cmd_build)
    p = sub.add_parser("settings")
    p.add_argument("--expect", nargs="*", default=[])
    p.set_defaults(func=cmd_settings)
    p = sub.add_parser("open-items")
    p.add_argument("--expect", nargs="*", default=[])
    p.set_defaults(func=cmd_open_items)
    p = sub.add_parser("genome-unchanged")
    p.add_argument("genome")
    p.add_argument("reference")
    p.set_defaults(func=cmd_genome_unchanged)
    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
