#!/usr/bin/env python3
"""Verify that every CLI command mocked in a diagnostic scenario's manifest is
a real subcommand in the locally installed `uip` CLI.

Approach:
  1. Walk every manifest.json under tests/tasks/uipath-diagnostics/.
  2. For each rule's `match` string, parse out the leading subcommand path
     (drop flags, UUIDs, quoted args).
  3. For each unique parsed path, run `uip <path> --output json --help`. The
     command exists iff the CLI returns `Result: Success`.
  4. Report which manifest rules reference paths the CLI does not expose.

Exits 0 if every mocked command is reachable; exits 1 otherwise.

Usage:
  python verify_manifest_commands.py [--root <repo-root>] [--uip <bin>]

Determinism: output depends only on (a) the manifests on disk and (b) the set
of tools currently installed in `uip`. No LLM, no network beyond `uip` itself.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
QUOTED_RE = re.compile(r'^["\'].*["\']?$')
HELP_TIMEOUT_S = 30


def parse_command_path(match: str) -> tuple[str, ...]:
    """Extract the leading subcommand path from a manifest `match` string.

    Stops at the first flag (`-…`), UUID, quoted string, or `--help`. Returns
    an empty tuple if nothing parseable remains.
    """
    if not match:
        return ()
    path: list[str] = []
    for tok in match.split():
        if tok.startswith("-"):
            break
        if UUID_RE.match(tok):
            break
        if QUOTED_RE.match(tok):
            break
        path.append(tok)
    return tuple(path)


def walk_manifests(root: Path) -> Iterable[dict]:
    """Yield one entry per rule.match across every diagnostic manifest."""
    for manifest_path in sorted(root.glob("*/fixtures/mocks/responses/manifest.json")):
        scenario = manifest_path.parents[3].name
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            yield {"scenario": scenario, "manifest": manifest_path, "parse_error": str(exc)}
            continue
        for idx, rule in enumerate(manifest.get("rules", [])):
            match = rule.get("match", "")
            yield {
                "scenario": scenario,
                "manifest": manifest_path,
                "rule_index": idx,
                "match": match,
                "path": parse_command_path(match),
                "passthrough": bool(rule.get("passthrough")),
            }


def validate_path(uip_bin: str, path: tuple[str, ...]) -> tuple[bool, str]:
    """Run `uip <path> --output json --help`. Return (valid, message)."""
    cmd = [uip_bin, *path, "--output", "json", "--help"]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=HELP_TIMEOUT_S
        )
    except subprocess.TimeoutExpired:
        return False, f"timeout after {HELP_TIMEOUT_S}s"
    except FileNotFoundError:
        return False, f"uip binary not found at {uip_bin!r}"

    stdout = result.stdout.strip()
    if not stdout:
        return False, f"empty stdout (rc={result.returncode})"
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return False, f"non-JSON stdout (rc={result.returncode}): {stdout[:120]}"
    if data.get("Result") == "Success":
        return True, ""
    return False, data.get("Message", "unknown error")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="diagnostics task root (default: parent of _shared/scripts)",
    )
    parser.add_argument("--uip", default="uip", help="uip binary (default: uip on PATH)")
    args = parser.parse_args(argv)

    if not args.root.exists():
        print(f"error: root {args.root} does not exist", file=sys.stderr)
        return 2

    rules_by_path: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    parse_errors: list[dict] = []
    skipped: list[dict] = []

    for entry in walk_manifests(args.root):
        if "parse_error" in entry:
            parse_errors.append(entry)
            continue
        if not entry["path"]:
            skipped.append(entry)
            continue
        rules_by_path[entry["path"]].append(entry)

    paths = sorted(rules_by_path)
    print(f"Manifests scanned under: {args.root}")
    print(f"Manifest parse errors:   {len(parse_errors)}")
    print(f"Rules with no parseable command: {len(skipped)}")
    print(f"Distinct command paths to verify: {len(paths)}")
    print()

    valid: list[tuple[str, ...]] = []
    invalid: list[tuple[tuple[str, ...], str]] = []
    for path in paths:
        ok, msg = validate_path(args.uip, path)
        marker = "OK " if ok else "BAD"
        print(f"  [{marker}] uip {' '.join(path)}" + (f"  -- {msg}" if msg else ""))
        if ok:
            valid.append(path)
        else:
            invalid.append((path, msg))

    print()
    print(f"Valid:   {len(valid)} / {len(paths)}")
    print(f"Invalid: {len(invalid)} / {len(paths)}")

    if parse_errors:
        print()
        print("Manifest parse errors:")
        for e in parse_errors:
            print(f"  [{e['scenario']}] {e['manifest']}: {e['parse_error']}")

    if invalid:
        print()
        print("Invalid commands — affected manifests:")
        for path, msg in invalid:
            print(f"  uip {' '.join(path)}  ({msg})")
            for entry in rules_by_path[path]:
                print(f"    {entry['scenario']}: rule {entry['rule_index']}  {entry['match']}")
        return 1

    print()
    print("OK — every mocked command is a real subcommand in the installed uip CLI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
