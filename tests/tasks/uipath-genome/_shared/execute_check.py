#!/usr/bin/env python3
"""Checks for a genome execution (Execute mode) run, from the sandbox root.

Usage:
  execute_check.py build                       the one RPA project built from the genome compiles (uip rpa build)
  execute_check.py settings --expect NAME …    that project reads every named setting as an Orchestrator asset:
                                               each name appears in its workflows, code or configuration file
  execute_check.py open-items --expect TOKEN … [--sections]   a Markdown file outside every project, under any
                                               name, naming every expected token; --sections also requires
                                               the always-present section headings
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


CONTEXT_FILES = {"agents.md", "claude.md"}


def handoff_candidates(projects: list[Path]) -> tuple[list[Path], list[Path]]:
    """(outside, inside): every Markdown file outside / inside the projects, the genome and agent
    context files excluded. The file name is the agent's choice; its content identifies it."""
    outside, inside = [], []
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if not name.lower().endswith(".md") or name.lower().endswith("-genome.md") or name.lower() in CONTEXT_FILES:
                continue
            path = Path(dirpath, name).resolve()
            (inside if any(p in path.parents for p in projects) else outside).append(path)
    return outside, inside


def cmd_open_items(a: argparse.Namespace) -> int:
    """The engineer's open items: a Markdown file outside every project that names every expected
    token, whatever it is called. --sections also requires the always-present section headings."""
    projects = rpa_projects(Path("."))
    outside, inside = handoff_candidates(projects)

    def names_all(path: Path) -> bool:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return all(t in text for t in a.expect)

    found = [p for p in outside if names_all(p)]
    if not found:
        misplaced = [p for p in inside if names_all(p)]
        if misplaced:
            print(f"FAIL: open items found only inside a project, where they ship in its package: {', '.join(map(str, misplaced))}")
        else:
            print(f"FAIL: no Markdown file outside the project names {', '.join(a.expect)}")
        return 1
    if a.sections:
        missing = {str(p): [s for s in SECTIONS if not any(l.strip() == s for l in p.read_text(encoding='utf-8', errors='ignore').splitlines())] for p in found}
        if all(missing.values()):
            for p, m in missing.items():
                print(f"FAIL: {Path(p).name} lacks {', '.join(m)}")
            return 1
    print(f"OK: open items in {', '.join(p.name for p in found)}")
    return 0


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
    p.add_argument("--sections", action="store_true", help="also require the always-present section headings")
    p.set_defaults(func=cmd_open_items)
    p = sub.add_parser("genome-unchanged")
    p.add_argument("genome")
    p.add_argument("reference")
    p.set_defaults(func=cmd_genome_unchanged)
    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
