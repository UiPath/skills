"""Lightweight XAML assertions for DataService smoke tests.

Designed to grow into the full 71-scenario library; current scope covers smoke
tier only (activity presence + TypeArguments + no-stray-activity guard).
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET

UDA_NS = "clr-namespace:UiPath.DataService.Activities;assembly=UiPath.DataService.Activities.Core"
X_NS = "http://schemas.microsoft.com/winfx/2006/xaml"


def _load(xaml_path: str) -> ET.Element:
    try:
        return ET.parse(xaml_path).getroot()
    except FileNotFoundError:
        print(f"FAIL: {xaml_path} does not exist", file=sys.stderr)
        sys.exit(1)
    except ET.ParseError as exc:
        print(f"FAIL: {xaml_path} is not well-formed XML: {exc}", file=sys.stderr)
        sys.exit(1)


def _uda_activities(root: ET.Element) -> list[ET.Element]:
    return [el for el in root.iter() if el.tag.startswith(f"{{{UDA_NS}}}")]


def _local_name(element: ET.Element) -> str:
    return element.tag.split("}", 1)[1] if "}" in element.tag else element.tag


def assert_activities_present(
    xaml_path: str, expected: list[str], entity_type: str
) -> None:
    """Each `expected` activity must appear at least once with x:TypeArguments=local:<entity_type>."""
    root = _load(xaml_path)
    found = _uda_activities(root)
    type_args_attr = f"{{{X_NS}}}TypeArguments"
    expected_type = f"local:{entity_type}"

    missing: list[str] = []
    wrong_type: list[tuple[str, str]] = []

    for name in expected:
        matches = [el for el in found if _local_name(el) == name]
        if not matches:
            missing.append(name)
            continue
        type_args = [el.get(type_args_attr) for el in matches]
        if not any(t == expected_type for t in type_args):
            wrong_type.append((name, ", ".join(filter(None, type_args)) or "<none>"))

    if missing:
        print(f"FAIL: missing uda activities: {', '.join(missing)}", file=sys.stderr)
    if wrong_type:
        for name, observed in wrong_type:
            print(
                f"FAIL: {name} expected x:TypeArguments={expected_type!r}, got {observed!r}",
                file=sys.stderr,
            )
    if missing or wrong_type:
        sys.exit(1)


def assert_no_unexpected_uda(xaml_path: str, allowed: list[str]) -> None:
    """No uda:* activity outside the `allowed` set is present."""
    root = _load(xaml_path)
    allowed_set = set(allowed)
    stray = sorted(
        {_local_name(el) for el in _uda_activities(root)} - allowed_set
    )
    if stray:
        print(
            f"FAIL: unexpected uda activities in XAML: {', '.join(stray)}",
            file=sys.stderr,
        )
        sys.exit(1)
