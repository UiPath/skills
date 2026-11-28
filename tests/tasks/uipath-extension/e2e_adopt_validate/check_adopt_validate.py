#!/usr/bin/env python3
"""Maestro community node (uip extension) - adopted project check.

Verifies that the agent turned a `uip function new` project into a community
node with `uip extension init`, filled the template it was given, and did not
add the Maestro Extensions SDK to the node.

Checks performed:

  1. The project folder holds `uipath.json`, so it is a uip function project.
  2. `package.json` is named `uipath-extensions.acme.word-count` and lists
     neither `@uipath/uipath-extensions-sdk` nor `@uipath/uipath-extensions-gates`
     in any dependency section.
  3. `uipath-extensions.json` is valid JSON with `schema` 2, no `version`, and
     none of the removed `egress` and `maestro` keys.
  4. The template carries the values the prompt asked for: license, label, a
     description and the tag.
  5. `display.icon` is `assets/icon.png` and that file exists in the project,
     because schema 2 requires that icon path and adopt writes a default one.
  6. No `TODO` placeholder is left anywhere in the template.
  7. The authored function does the job the prompt asked for. `uip function
     run` with `{"text": "one two"}` returns `{"words": 2}`. A second text holds
     a double space, a tab and a newline between five words and must return
     `{"words": 5}`, so a split on single spaces or on `/ +/` fails.
  8. `_setup/gh-calls.log`, written by the stand-in `gh`, holds both index reads
     `init` makes. A run whose `init` used the host `gh` leaves no such log, so
     it fails here even when every file on disk is right. The log shows that
     the stand-in answered those reads, not that `init` made them.

Exits 0 on PASS, `sys.exit("FAIL: ...")` on the first violation.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT = "word-count"
PACKAGE_NAME = "uipath-extensions.acme.word-count"
ICON_PATH = "assets/icon.png"
STAND_IN_LOG = "_setup/gh-calls.log"
INDEX_READS = (
    "OK GET repos/UiPath/uipath-extensions",
    "OK GET repos/UiPath/uipath-extensions/contents/policy/gate-library.yaml",
)
RUN_TIMEOUT_SECONDS = 90
RUN_CASES = (
    ({"text": "one two"}, 2),
    ({"text": "a b  c\td\ne"}, 5),
)
SDK_PACKAGES = (
    "@uipath/uipath-extensions-sdk",
    "@uipath/uipath-extensions-gates",
)
DEPENDENCY_SECTIONS = (
    "dependencies",
    "devDependencies",
    "peerDependencies",
    "optionalDependencies",
)


def find_project_root() -> Path:
    """Return the project folder, whether the agent stayed at the sandbox root or entered it."""
    cwd = Path(os.getcwd())
    if (cwd / "package.json").is_file():
        return cwd
    return cwd / PROJECT


def read_json(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: {path.name} is missing from {path.parent}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        sys.exit(f"FAIL: {path.name} is not valid JSON: {error}")
    if not isinstance(value, dict):
        sys.exit(f"FAIL: {path.name} is not a JSON object")
    return value


def non_empty_text(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def function_name(root: Path) -> str:
    functions = read_json(root / "uipath.json").get("functions")
    if not isinstance(functions, dict) or len(functions) != 1:
        sys.exit(f"FAIL: uipath.json functions is {functions!r}, expected exactly one function")
    return next(iter(functions))


def find_stand_in_log(root: Path) -> Path | None:
    """Return the stand-in's call log, wherever the sandbox root sits relative to the project."""
    for base in (Path(os.getcwd()), root, root.parent):
        candidate = base / STAND_IN_LOG
        if candidate.is_file():
            return candidate
    return None


def check_index_reads(root: Path) -> None:
    log = find_stand_in_log(root)
    if log is None:
        sys.exit(
            f"FAIL: {STAND_IN_LOG} does not exist, so `uip extension init` did not read the "
            "index through the stand-in gh in _setup and may have used the host login"
        )
    calls = {line.strip() for line in log.read_text(encoding="utf-8").splitlines()}
    missing = [read for read in INDEX_READS if read not in calls]
    if missing:
        sys.exit(f"FAIL: {log} lacks the index reads {missing}, so the stand-in gh did not serve `init`")


def run_function(root: Path, name: str, payload: dict) -> dict:
    try:
        completed = subprocess.run(
            ["uip", "function", "run", "--function", name, "--input", json.dumps(payload)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        sys.exit(f"FAIL: could not run function {name!r} with {payload!r}: {error}")
    marker = "JobResult="
    line = next((row for row in completed.stdout.splitlines() if row.startswith(marker)), None)
    if line is None:
        sys.exit(
            f"FAIL: function {name!r} printed no JobResult for {payload!r}: "
            f"exit {completed.returncode}, "
            f"stdout tail {completed.stdout[-300:]!r}, "
            f"stderr tail {completed.stderr[-300:]!r}"
        )
    try:
        result = json.loads(line[len(marker):])
    except json.JSONDecodeError as error:
        sys.exit(f"FAIL: JobResult for {payload!r} is not valid JSON: {error}")
    if result.get("status") != "Successful":
        sys.exit(f"FAIL: function {name!r} with {payload!r} ended {result.get('status')!r}: {result.get('info')}")
    output = result.get("outputArguments")
    if not isinstance(output, dict):
        sys.exit(f"FAIL: function {name!r} with {payload!r} returned no outputArguments")
    return output


root = find_project_root()

if not (root / "uipath.json").is_file():
    sys.exit(f"FAIL: uipath.json is missing from {root}, so this is not a uip function project")

package = read_json(root / "package.json")
if package.get("name") != PACKAGE_NAME:
    sys.exit(f"FAIL: package.json name is {package.get('name')!r}, expected {PACKAGE_NAME!r}")

for section in DEPENDENCY_SECTIONS:
    declared = package.get(section)
    if not isinstance(declared, dict):
        continue
    for sdk in SDK_PACKAGES:
        if sdk in declared:
            sys.exit(f"FAIL: package.json {section} lists {sdk}, a node must not depend on it")

template_path = root / "uipath-extensions.json"
template = read_json(template_path)

if template.get("schema") != 2:
    sys.exit(f"FAIL: uipath-extensions.json schema is {template.get('schema')!r}, expected 2")
if "version" in template:
    sys.exit("FAIL: uipath-extensions.json has a version key, schema 2 reads the version from package.json")

if template.get("license") != "MIT":
    sys.exit(f"FAIL: license is {template.get('license')!r}, expected 'MIT'")

display = template.get("display")
if not isinstance(display, dict):
    sys.exit("FAIL: display is missing from uipath-extensions.json")
if display.get("label") != "Word Count":
    sys.exit(f"FAIL: display.label is {display.get('label')!r}, expected 'Word Count'")
if not non_empty_text(display.get("description")):
    sys.exit("FAIL: display.description is empty")

tags = template.get("tags")
if not isinstance(tags, list) or "text" not in tags:
    sys.exit(f"FAIL: tags is {tags!r}, expected a list holding 'text'")

for removed in ("egress", "maestro"):
    if removed in template:
        sys.exit(f"FAIL: uipath-extensions.json has a {removed} key, schema 2 does not define it")

icon = display.get("icon")
if icon != ICON_PATH:
    sys.exit(f"FAIL: display.icon is {icon!r}, schema 2 requires {ICON_PATH!r}")
if not (root / ICON_PATH).is_file():
    sys.exit(f"FAIL: display.icon names {ICON_PATH!r}, which is not a file in the project")

if "TODO" in template_path.read_text(encoding="utf-8"):
    sys.exit("FAIL: uipath-extensions.json still holds a TODO placeholder")

check_index_reads(root)

name = function_name(root)
for payload, expected in RUN_CASES:
    output = run_function(root, name, payload)
    if output.get("words") != expected:
        sys.exit(f"FAIL: function {name!r} with {payload!r} returned {output!r}, expected {{'words': {expected}}}")

print("PASS: the project is adopted as acme.word-count, with a filled schema 2 template and a function that counts words")
