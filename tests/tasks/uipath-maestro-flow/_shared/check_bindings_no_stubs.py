#!/usr/bin/env python3
"""Check either native Flow bindings schema for empty or placeholder resources."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

EXCLUDED_PARTS = {
    ".cli-stage",
    ".git",
    ".v1stage",
    "_lib",
    "_outputs",
    "example",
    "fixtures",
    "node_modules",
    "references",
    "sdk",
    "v1stage",
}
UUID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
STUB_UUID = re.compile(r"^0{8}-0{4}-0{4}-0{4}-")


def is_real_key(value: Any) -> bool:
    rendered = str(value or "").strip()
    return bool(UUID.fullmatch(rendered)) and not STUB_UUID.match(rendered)


def load_entries(path: Path) -> tuple[list[dict[str, Any]], str]:
    document = json.loads(path.read_text())
    if isinstance(document.get("bindings"), list):
        return [
            entry
            for entry in document["bindings"]
            if str(entry.get("resource") or "").lower() == "connection"
        ], "bindings"
    if isinstance(document.get("resources"), list):
        return [
            entry
            for entry in document["resources"]
            if str(entry.get("resource") or "").lower() == "connection"
        ], "resources"
    raise AssertionError(f"{path} has neither a bindings nor resources array")


def invalid_ids(entries: list[dict[str, Any]], schema: str) -> list[str]:
    failures: list[str] = []
    for index, entry in enumerate(entries):
        identifier = str(entry.get("id") or entry.get("key") or index)
        if schema == "bindings":
            values = [entry.get("resourceKey"), entry.get("default")]
        else:
            values = []
            for binding in (entry.get("value") or {}).values():
                if isinstance(binding, dict) and "defaultValue" in binding:
                    values.append(binding.get("defaultValue"))
        if not values or any(not is_real_key(value) for value in values):
            failures.append(identifier)
    return failures


def main() -> None:
    cwd = Path.cwd()
    candidates = sorted(
        path
        for path in cwd.rglob("bindings*.json")
        if path.name in {"bindings.json", "bindings_v2.json"}
        and not EXCLUDED_PARTS.intersection(path.relative_to(cwd).parts)
    )
    assert candidates, "no generated bindings.json or bindings_v2.json found"

    checked = 0
    for path in candidates:
        entries, schema = load_entries(path)
        assert entries, f"{path} declares no bindings at all"
        failures = invalid_ids(entries, schema)
        assert not failures, f"stub or empty bindings in {path}: {failures}"
        checked += len(entries)

    print(f"{checked} bindings across {len(candidates)} file(s), all populated with non-stub values")


if __name__ == "__main__":
    main()
