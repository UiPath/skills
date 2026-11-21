#!/usr/bin/env python3
"""Maestro community node (uip extension) - adopted project check.

Verifies that the agent turned a `uip function new` project into a community
node with `uip extension submit`, filled the template it was given, and did not
add the Maestro Extensions SDK to the node.

Checks performed:

  1. The project folder holds `uipath.json`, so it is a uip function project.
  2. `package.json` is named `maestro-extensions.acme.word-count` and lists
     neither `@uipath/maestro-extensions-sdk` nor `@uipath/maestro-extensions-gates`
     in any dependency section.
  3. `maestro-extensions.json` is valid JSON with `schema` 2 and no `version`.
  4. The template carries the values the prompt asked for: license, label, a
     description, the tag, no egress, and the minimum Maestro version.
  5. No `TODO` placeholder is left anywhere in the template.

Exits 0 on PASS, `sys.exit("FAIL: ...")` on the first violation.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT = "word-count"
PACKAGE_NAME = "maestro-extensions.acme.word-count"
SDK_PACKAGES = (
    "@uipath/maestro-extensions-sdk",
    "@uipath/maestro-extensions-gates",
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

template_path = root / "maestro-extensions.json"
template = read_json(template_path)

if template.get("schema") != 2:
    sys.exit(f"FAIL: maestro-extensions.json schema is {template.get('schema')!r}, expected 2")
if "version" in template:
    sys.exit("FAIL: maestro-extensions.json has a version key, schema 2 reads the version from package.json")

if template.get("license") != "MIT":
    sys.exit(f"FAIL: license is {template.get('license')!r}, expected 'MIT'")

display = template.get("display")
if not isinstance(display, dict):
    sys.exit("FAIL: display is missing from maestro-extensions.json")
if display.get("label") != "Word Count":
    sys.exit(f"FAIL: display.label is {display.get('label')!r}, expected 'Word Count'")
if not non_empty_text(display.get("description")):
    sys.exit("FAIL: display.description is empty")

tags = template.get("tags")
if not isinstance(tags, list) or "text" not in tags:
    sys.exit(f"FAIL: tags is {tags!r}, expected a list holding 'text'")

if template.get("egress") != []:
    sys.exit(f"FAIL: egress is {template.get('egress')!r}, expected an empty list")

maestro = template.get("maestro")
if not isinstance(maestro, dict) or maestro.get("min") != "2026.10":
    sys.exit(f"FAIL: maestro.min is {maestro!r}, expected 'min': '2026.10'")

if "TODO" in template_path.read_text(encoding="utf-8"):
    sys.exit("FAIL: maestro-extensions.json still holds a TODO placeholder")

print("PASS: the project is adopted as acme.word-count with a filled schema 2 template")
