#!/usr/bin/env python3
"""Verify that every CLI command mocked in a troubleshoot scenario's manifest is
shaped correctly against the locally installed `uip` CLI.

Three checks per manifest rule's `match` string:

  1. Path     — every subcommand token must appear in its parent's Subcommands
                list (walks the tree level-by-level via `uip <prefix> --help`).
  2. Flags    — every `--flag` from the match must exist in the leaf command's
                Options list.
  3. Arguments — positional tokens (UUIDs, quoted strings, plain words after
                 the path) must not exceed the leaf's declared Arguments count.

Tree-walk avoids two CLI quirks that broke a flat `--output json --help` probe:
  - Windows `.CMD` shim returns Success/Help for unknown subcommands by
    falling back to the deepest valid parent's help (false positive).
  - Deeply-nested commands (e.g. `uip maestro bpmn instance asset`) return
    help for the wrong level under `--output json` (false negative).

By walking one level at a time, each step's help is for the parent we
already know is real, so we just check the next token's membership.

Exits 0 if every check passes; exits 1 otherwise.

Determinism: depends only on (a) the manifests on disk and (b) the tools
currently installed in `uip`. No LLM, no network beyond `uip` itself.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Iterable

UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
HELP_TIMEOUT_S = 30


def tokenize_match(match: str) -> tuple[list[str], list[str], list[str]]:
    """Split a manifest `match` string into (path, flags, positionals).

    - path: leading subcommand tokens (plain identifiers before any flag /
      UUID / quoted arg).
    - flags: every `--flag` (and short `-x`) encountered, normalised by
      stripping the value if any. e.g. `--folder-key abc` and
      `--folder-key=abc` both yield `--folder-key`.
    - positionals: UUIDs and quoted strings (with quotes stripped) that
      appear after the path. These are the runtime arguments.
    """
    try:
        toks = shlex.split(match, posix=True)
    except ValueError:
        # Fall back to whitespace split for malformed strings
        toks = match.split()

    path: list[str] = []
    flags: list[str] = []
    positionals: list[str] = []
    in_args = False
    i = 0
    while i < len(toks):
        t = toks[i]
        if t.startswith("--"):
            in_args = True
            name, _, _ = t.partition("=")
            flags.append(name)
            # Consume the value if it isn't the next flag
            if "=" not in t and i + 1 < len(toks) and not toks[i + 1].startswith("-"):
                i += 1  # skip the value
        elif t.startswith("-") and len(t) > 1 and not t[1:].isdigit():
            in_args = True
            flags.append(t)
            if i + 1 < len(toks) and not toks[i + 1].startswith("-"):
                i += 1
        elif not in_args and UUID_RE.match(t):
            in_args = True
            positionals.append(t)
        elif not in_args and re.fullmatch(r"[a-z][a-z0-9-]*", t):
            # Strict kebab-case subcommand. Hyphens allowed
            # (`credential-stores`, `element-executions`, etc.); uppercase,
            # digits-leading, dots, slashes, or anything else is a value.
            path.append(t)
        elif not in_args:
            # Doesn't look like a kebab subcommand → it's the first positional
            in_args = True
            positionals.append(t)
        else:
            positionals.append(t)
        i += 1
    return path, flags, positionals


@lru_cache(maxsize=None)
def fetch_help(uip_bin: str, prefix: tuple[str, ...]) -> dict | None:
    """Fetch the parsed --help payload for `uip <prefix>`. Cached."""
    cmd = [uip_bin, *prefix, "--output", "json", "--help"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=HELP_TIMEOUT_S)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    stdout = r.stdout.strip()
    if not stdout:
        return None
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return None


# Aspect routers that JSON --help hides — the parent's JSON payload doesn't
# list these in Subcommands, yet they're real subcommands at runtime. Caught
# by the user via the maestro-stuck-rpa-job manifest which calls real
# `uip maestro bpmn instance ...` paths. Add more entries here if other tools
# exhibit the same routing quirk.
KNOWN_ASPECT_ROUTERS: dict[tuple[str, ...], set[str]] = {
    ("maestro",): {"bpmn", "case", "flow"},
}


def subcommand_names(help_payload: dict) -> set[str]:
    """Extract subcommand names from a --help payload's Subcommands list."""
    if not help_payload:
        return set()
    data = help_payload.get("Data") or {}
    subs = data.get("Subcommands") or []
    names = set()
    for s in subs:
        n = s.get("Name") or ""
        # Names sometimes include trailing `[options]` / `<args>` — first token only
        first = n.split()[0] if n else ""
        if first and not first.startswith("<") and not first.startswith("["):
            names.add(first)
    return names


def flag_names(help_payload: dict) -> set[str]:
    """Extract flag long+short names from a --help payload's Options list."""
    if not help_payload:
        return set()
    data = help_payload.get("Data") or {}
    opts = data.get("Options") or []
    names: set[str] = set()
    for o in opts:
        flags_str = o.get("Flags") or ""
        # `-t, --tenant <tenant-name>` -> ['-t', '--tenant']
        for piece in flags_str.split(","):
            piece = piece.strip().split()[0] if piece.strip() else ""
            if piece.startswith("-"):
                names.add(piece)
    return names


def arg_count(help_payload: dict) -> int:
    """Count declared positional arguments on the leaf command."""
    if not help_payload:
        return 0
    data = help_payload.get("Data") or {}
    return len(data.get("Arguments") or [])


GLOBAL_FLAGS = frozenset({
    # CLI-wide flags accepted by every subcommand, even when leaf help doesn't
    # relist them. Root `uip --help` doesn't include these either — they're
    # surfaced only on intermediate command-group help. Hardcoded so we don't
    # depend on a particular intermediate level being scraped.
    "--output", "--output-filter",
    "--log-level", "--log-file",
    "-h", "--help", "--help-all",
})


def validate_match(
    uip_bin: str,
    match: str,
) -> tuple[bool, str]:
    """Validate a single match string. Return (valid, message)."""
    path, used_flags, positionals = tokenize_match(match)
    if not path:
        return False, "no parseable subcommand path"

    # 1. Walk the path level-by-level
    for depth in range(len(path)):
        parent = tuple(path[:depth])
        token = path[depth]
        help_payload = fetch_help(uip_bin, parent)
        if help_payload is None:
            return False, f"could not fetch help for 'uip {' '.join(parent)}'"
        if help_payload.get("Result") != "Success":
            return False, f"parent 'uip {' '.join(parent)}' returned {help_payload.get('Result')}"
        subs = subcommand_names(help_payload)
        if token not in subs:
            return False, f"'{token}' is not a subcommand of 'uip {' '.join(parent) or '(root)'}'"

    # 2. Leaf-level flag validation (per-command flags + inherited global flags)
    leaf_help = fetch_help(uip_bin, tuple(path))
    if leaf_help is None:
        return False, f"could not fetch help for leaf 'uip {' '.join(path)}'"

    allowed_flags = flag_names(leaf_help) | GLOBAL_FLAGS
    bad_flags = [f for f in set(used_flags) if f not in allowed_flags]
    if bad_flags:
        return False, f"unknown flag(s) on 'uip {' '.join(path)}': {', '.join(sorted(bad_flags))}"

    # 3. Argument count check (informational — many commands accept varargs)
    expected_args = arg_count(leaf_help)
    if expected_args and len(positionals) > expected_args:
        return False, (
            f"'uip {' '.join(path)}' expects {expected_args} positional arg(s); "
            f"manifest supplies {len(positionals)}"
        )

    return True, ""


def walk_manifests(root: Path) -> Iterable[dict]:
    """Yield one entry per rule.match across every troubleshoot manifest."""
    for manifest_path in sorted(root.glob("*/fixtures/mocks/responses/manifest.json")):
        scenario = manifest_path.parents[3].name
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            yield {"scenario": scenario, "manifest": manifest_path, "parse_error": str(exc)}
            continue
        for idx, rule in enumerate(manifest.get("rules", [])):
            yield {
                "scenario": scenario,
                "manifest": manifest_path,
                "rule_index": idx,
                "match": rule.get("match", ""),
                "passthrough": bool(rule.get("passthrough")),
            }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="troubleshoot task root (default: parent of _shared/scripts)",
    )
    parser.add_argument("--uip", default="uip", help="uip binary (default: uip on PATH)")
    args = parser.parse_args(argv)

    if not args.root.exists():
        print(f"error: root {args.root} does not exist", file=sys.stderr)
        return 2

    rules_by_match: dict[str, list[dict]] = defaultdict(list)
    parse_errors: list[dict] = []

    for entry in walk_manifests(args.root):
        if "parse_error" in entry:
            parse_errors.append(entry)
            continue
        if not entry["match"]:
            continue
        rules_by_match[entry["match"]].append(entry)

    matches = sorted(rules_by_match)
    print(f"Manifests scanned under: {args.root}")
    print(f"Manifest parse errors:   {len(parse_errors)}")
    print(f"Distinct match strings to verify: {len(matches)}")
    print()

    valid: list[str] = []
    invalid: list[tuple[str, str]] = []
    for m in matches:
        ok, msg = validate_match(args.uip, m)
        marker = "OK " if ok else "BAD"
        suffix = f"  -- {msg}" if msg else ""
        print(f"  [{marker}] {m}{suffix}")
        (valid if ok else invalid).append((m, msg) if not ok else m)

    print()
    print(f"Valid:   {len(valid)} / {len(matches)}")
    print(f"Invalid: {len(invalid)} / {len(matches)}")

    if parse_errors:
        print()
        print("Manifest parse errors:")
        for e in parse_errors:
            print(f"  [{e['scenario']}] {e['manifest']}: {e['parse_error']}")

    if invalid:
        print()
        print("Invalid matches — affected manifests:")
        for m, msg in invalid:
            print(f"  {m}  ({msg})")
            for entry in rules_by_match[m]:
                print(f"    {entry['scenario']}: rule {entry['rule_index']}")
        return 1

    print()
    print("OK — every mocked command, flag, and positional shape is valid against the installed uip CLI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
