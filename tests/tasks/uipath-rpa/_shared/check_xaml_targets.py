"""Generic UiPath XAML TargetAnchorable validator.

Usage:
    python check_xaml_targets.py <Main.xaml> --rules <rules.json>

Walks a UiPath XAML, finds every `uix:TargetAnchorable` (matched by local
name so namespace shifts don't break the script), dumps them to a
short-lived temp JSON, and then enforces everything declared in the rules
file: expected target count + per-target attribute-quality rules.

The rules file is JSON with the following shape:

  {
    "target_count": <int>,
    "forbidden_patterns": [
      {"name": "<label>", "regex": "<re>", "scope": "<scope>"}
    ],
    "required_patterns": [
      {"name": "<label>", "regex": "<re>", "scope": "<scope>"}
    ]
  }

`scope` selects which selector field the regex runs against:
  - "FullSelectorArgument"  — the element selector chain
  - "ScopeSelectorArgument" — the parent window/scope selector
  - "any" (default)         — both fields, joined by newline

Exits 0 on pass, 1 on rule failure, 2 on usage / IO / parse error.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path
from xml.etree import ElementTree as ET


_TARGET_ANCHORABLE_LOCAL_NAME = "TargetAnchorable"
_VALID_SCOPES = {"FullSelectorArgument", "ScopeSelectorArgument", "any"}


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def extract_targets(xaml_path: Path) -> list[dict]:
    """Parse a XAML and return every TargetAnchorable as a plain dict."""
    tree = ET.parse(xaml_path)
    root = tree.getroot()
    targets: list[dict] = []
    for elem in root.iter():
        if _local_name(elem.tag) != _TARGET_ANCHORABLE_LOCAL_NAME:
            continue
        targets.append(
            {
                "ElementType": elem.attrib.get("ElementType", ""),
                "FullSelectorArgument": elem.attrib.get("FullSelectorArgument", ""),
                "ScopeSelectorArgument": elem.attrib.get("ScopeSelectorArgument", ""),
            }
        )
    return targets


@contextlib.contextmanager
def extract_targets_to_temp_json(xaml_path: Path) -> Iterator[tuple[list[dict], Path]]:
    """Extract TargetAnchorables and dump them to a self-cleaning temp JSON.

    Yields (targets, temp_path). The temp file is unlinked on exit, even on
    failure. Uses ``mkstemp`` (not ``NamedTemporaryFile``) so the path stays
    readable across processes on Windows during the ``yield`` window.
    """
    targets = extract_targets(xaml_path)
    fd, tmp_str = tempfile.mkstemp(prefix="xaml_targets_", suffix=".json")
    tmp_path = Path(tmp_str)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(targets, indent=2))
        yield targets, tmp_path
    finally:
        with contextlib.suppress(OSError):
            tmp_path.unlink()


def _select_text(target: dict, scope: str) -> str:
    if scope == "FullSelectorArgument":
        return target.get("FullSelectorArgument", "")
    if scope == "ScopeSelectorArgument":
        return target.get("ScopeSelectorArgument", "")
    return f"{target.get('FullSelectorArgument', '')}\n{target.get('ScopeSelectorArgument', '')}"


def _validate_rules_shape(rules: dict, rules_path: Path) -> None:
    """Best-effort schema check so misconfigured rules fail fast and clearly."""
    target_count = rules.get("target_count")
    if not isinstance(target_count, int) or target_count < 0:
        raise ValueError(
            f"{rules_path}: 'target_count' must be a non-negative integer, "
            f"got {target_count!r}"
        )
    for key in ("forbidden_patterns", "required_patterns"):
        for i, rule in enumerate(rules.get(key, [])):
            for required_field in ("name", "regex"):
                if required_field not in rule:
                    raise ValueError(
                        f"{rules_path}: {key}[{i}] missing field '{required_field}'"
                    )
            scope = rule.get("scope", "any")
            if scope not in _VALID_SCOPES:
                raise ValueError(
                    f"{rules_path}: {key}[{i}] has invalid scope {scope!r}; "
                    f"expected one of {sorted(_VALID_SCOPES)}"
                )
            try:
                re.compile(rule["regex"])
            except re.error as e:
                raise ValueError(
                    f"{rules_path}: {key}[{i}] regex {rule['regex']!r} invalid: {e}"
                ) from e


def validate_target(target: dict, idx: int, rules: dict) -> list[str]:
    """Apply forbidden + required rules to one target. Returns error strings."""
    errors: list[str] = []
    for rule in rules.get("forbidden_patterns", []):
        scope = rule.get("scope", "any")
        text = _select_text(target, scope)
        if re.search(rule["regex"], text):
            errors.append(
                f"target[{idx}]: contains forbidden pattern {rule['name']!r} in {scope}"
            )
    for rule in rules.get("required_patterns", []):
        scope = rule.get("scope", "any")
        text = _select_text(target, scope)
        if not re.search(rule["regex"], text):
            errors.append(
                f"target[{idx}]: missing required pattern {rule['name']!r} in {scope}"
            )
    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("xaml", help="Path to the XAML workflow")
    parser.add_argument(
        "--rules",
        required=True,
        help="Path to the JSON rules file (target_count + forbidden_patterns + required_patterns)",
    )
    args = parser.parse_args(argv[1:])

    xaml_path = Path(args.xaml)
    rules_path = Path(args.rules)

    if not xaml_path.is_file():
        print(f"FAIL: XAML not found: {xaml_path}", file=sys.stderr)
        return 2
    if not rules_path.is_file():
        print(f"FAIL: rules file not found: {rules_path}", file=sys.stderr)
        return 2

    try:
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
        _validate_rules_shape(rules, rules_path)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"FAIL: invalid rules file {rules_path}: {e}", file=sys.stderr)
        return 2

    expected_count = rules["target_count"]

    try:
        with extract_targets_to_temp_json(xaml_path) as (targets, tmp_path):
            if len(targets) != expected_count:
                print(
                    f"FAIL: expected {expected_count} TargetAnchorables in {xaml_path}, "
                    f"found {len(targets)} (temp dump: {tmp_path})",
                    file=sys.stderr,
                )
                return 1

            errors: list[str] = []
            for idx, target in enumerate(targets, start=1):
                errors.extend(validate_target(target, idx, rules))

            if errors:
                print(f"FAIL: attribute-quality checks failed for {xaml_path}", file=sys.stderr)
                for err in errors:
                    print(f"  - {err}", file=sys.stderr)
                print(f"(temp JSON dump: {tmp_path})", file=sys.stderr)
                return 1

            print(f"OK: {len(targets)} TargetAnchorables, all attribute-quality checks pass")
            print(f"(temp JSON dump: {tmp_path})")
            return 0
    except ET.ParseError as e:
        print(f"FAIL: XAML parse error in {xaml_path}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
