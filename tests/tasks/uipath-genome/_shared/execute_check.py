#!/usr/bin/env python3
"""Checks for a genome execution (Execute mode) run, from the sandbox root.

Usage:
  execute_check.py build                       the one RPA project built from the genome compiles (uip rpa build)
  execute_check.py settings --expect NAME …    that project reads every named setting as an Orchestrator asset:
                                               each name is an asset read's asset name, or a cell of a
                                               configuration workbook's Assets sheet
  execute_check.py open-items --expect TOKEN … [--sections]   a Markdown file outside every project, under any
                                               name, headed '# Open items' and naming every expected token;
                                               --sections also requires the always-present section headings
  execute_check.py genome-unchanged <genome> <reference>   execution left the genome byte-identical

Cross-platform on purpose: coder-eval runs run_command through cmd.exe on Windows, so criteria call this
script through `python -c` and read REFERENCE_DIR from the environment. Exit 0 on pass, 1 with a reason.
"""

import argparse
import filecmp
import html
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
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


XAML_ASSET_READ = re.compile(r"<(\w+:)?(GetRobotAsset|GetRobotCredential|GetAsset|GetCredential)\b(?:[^>]*?/>|.*?</(?:\w+:)?\2>)", re.S)
XAML_ASSET_NAME = re.compile(r'\bAssetName="([^"]*)"|\.AssetName>(.*?)</', re.S)
CODE_ASSET_READ = re.compile(r"\b(?:GetAsset|GetRobotAsset|GetCredential|GetRobotCredential)\s*\(\s*([^,)]*)")
SHEET_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def resolve_name(argument: str, text: str) -> str:
    """The asset-name argument, plus the value of the one identifier it names (a constant, a variable's default)."""
    m = re.fullmatch(r"\s*\[?\s*(\w+)\s*\]?\s*", html.unescape(argument))
    if not m:
        return argument
    ident = re.escape(m.group(1))
    bound = re.search(rf"\b{ident}\b\s*(?:As\s+String\s*)?=\s*\"([^\"]*)\"", text) \
        or re.search(rf"<Variable\b(?=[^>]*\bName=\"{ident}\")[^>]*\bDefault=\"([^\"]*)\"", text)
    return argument + " " + (bound.group(1) if bound else "")


def asset_name_arguments(path: Path) -> list[str]:
    """The asset-name argument of every asset read in one workflow or code file."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".xaml":
        found = [a or b for m in XAML_ASSET_READ.finditer(text) for a, b in XAML_ASSET_NAME.findall(m.group(0))]
    else:
        found = CODE_ASSET_READ.findall(text)
    return [resolve_name(arg, text) for arg in found]


def assets_sheet_cells(path: Path) -> list[str]:
    """Every cell value on a workbook's Assets sheet (the REFramework configuration names the assets it reads there)."""
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        book = ET.fromstring(z.read("xl/workbook.xml"))
        rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        shared = ["".join(t.text or "" for t in si.iter(f"{SHEET_NS}t"))
                  for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(f"{SHEET_NS}si")] \
            if "xl/sharedStrings.xml" in names else []
        cells = []
        for sheet in book.iter(f"{SHEET_NS}sheet"):
            if sheet.get("name", "").strip().lower() != "assets":
                continue
            target = rels.get(sheet.get(f"{REL_NS}id"), "")
            target = target.lstrip("/") if target.startswith("/") else "xl/" + target
            for c in ET.fromstring(z.read(target)).iter(f"{SHEET_NS}c"):
                v = c.find(f"{SHEET_NS}v")
                if c.get("t") == "s" and v is not None:
                    cells.append(shared[int(v.text)])
                elif c.get("t") == "inlineStr":
                    cells.append("".join(t.text or "" for t in c.iter(f"{SHEET_NS}t")))
                elif v is not None:
                    cells.append(v.text or "")
        return cells


def setting_reads(project: Path) -> tuple[list[str], list[str]]:
    """(asset-name arguments of the workflow and code files, cells of the workbooks' Assets sheets)."""
    arguments, cells = [], []
    for dirpath, dirnames, filenames in os.walk(project):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            path = Path(dirpath) / name
            suffix = path.suffix.lower()
            try:
                if suffix in {".xaml", ".cs", ".vb"}:
                    arguments += asset_name_arguments(path)
                elif suffix == ".xlsx":
                    cells += assets_sheet_cells(path)
            except (OSError, KeyError, ValueError, IndexError, zipfile.BadZipFile, ET.ParseError) as e:
                print(f"skipped {path}: {e}")
    return arguments, cells


def cmd_settings(a: argparse.Namespace) -> int:
    """Each setting is read as an Orchestrator asset: its name is the asset-name argument of an asset read in a
    workflow or code file (directly, or through the one constant or variable that argument names), or a cell of a
    configuration workbook's Assets sheet. A name anywhere else — a Settings row, a literal, an unrelated call —
    does not count."""
    project = one_project()
    arguments, cells = setting_reads(project)
    missing = [n for n in a.expect if not any(n in arg for arg in arguments) and n not in {c.strip() for c in cells}]
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


OPEN_ITEMS_HEADING = re.compile(r"^# Open items\b", re.M | re.I)


def cmd_open_items(a: argparse.Namespace) -> int:
    """The engineer's open items: a Markdown file outside every project, whatever it is called, headed
    '# Open items' as the open-items guide's template is, that names every expected token — a run brief,
    ledger or report naming the same tokens does not count. --sections also requires the always-present
    section headings."""
    projects = rpa_projects(Path("."))
    outside, inside = handoff_candidates(projects)

    def names_all(path: Path) -> bool:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return bool(OPEN_ITEMS_HEADING.search(text)) and all(t in text for t in a.expect)

    found = [p for p in outside if names_all(p)]
    if not found:
        misplaced = [p for p in inside if names_all(p)]
        if misplaced:
            print(f"FAIL: open items found only inside a project, where they ship in its package: {', '.join(map(str, misplaced))}")
        else:
            print(f"FAIL: no Markdown file outside the project is headed '# Open items' and names {', '.join(a.expect)}")
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
