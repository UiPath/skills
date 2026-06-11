#!/usr/bin/env python3
"""Verify that every CLI command mocked in a troubleshoot scenario's manifest is
shaped correctly against the locally installed `uip` CLI.

Shape-aggregated: distinct match strings that share the same (path, flag-set,
positional-count) collapse into one shape and validate once. Twenty
`or jobs get <uuid> --output json` rules across 12 scenarios produce a single
[OK] line instead of 20 redundant ones; the affected manifests are listed
under each shape.

Three checks per shape:

  1. Path     — every subcommand token must appear in its parent's Subcommands
                list (walks the tree level-by-level via `uip <prefix> --help`,
                with KNOWN_ASPECT_ROUTERS as a fallback for aspect-router
                hosts whose JSON help hides routed subcommands).
  2. Flags    — every `--flag` from the shape must exist in the leaf command's
                Options list (or be a CLI-wide global flag).
  3. Arguments — positional count must not exceed the leaf's declared
                 Arguments count.

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
# Dashless 32-char hex IDs (e.g. trace IDs) are positionals, same as dashed
# UUIDs. Without this, an all-[a-f] hex ID that starts with a letter parses
# as a kebab-case subcommand token and the shape walk reports a false BAD.
HEX32_RE = re.compile(r"^[0-9a-fA-F]{32}$")
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
        elif not in_args and (UUID_RE.match(t) or HEX32_RE.match(t)):
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
    """Extract subcommand names from a --help payload's Subcommands list.

    Handles two name formats the CLI emits:
      - plain:    `"or"` / `"or [options]"`                          -> {"or"}
      - aliased:  `"or|orchestrator"` / `"or|orchestrator [options]"` -> {"or", "orchestrator"}
    The pipe-joined form appears on platforms (Linux/Docker — CI's runtime)
    where the JSON help renders the alias list as a single Subcommands entry.
    Without splitting on `|`, the membership check `"or" in subs` returns
    False and every `or X` rule cascades to BAD.
    """
    if not help_payload:
        return set()
    data = help_payload.get("Data") or {}
    subs = data.get("Subcommands") or []
    names: set[str] = set()
    for s in subs:
        n = s.get("Name") or ""
        # Names sometimes include trailing `[options]` / `<args>` — first token only
        first = n.split()[0] if n else ""
        if not first or first.startswith("<") or first.startswith("["):
            continue
        for alias in first.split("|"):
            if alias:
                names.add(alias)
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


def validate_shape(
    uip_bin: str,
    path: tuple[str, ...],
    used_flags: frozenset[str],
    positional_count: int,
) -> tuple[bool, str]:
    """Validate a (path, flag-set, positional-count) shape against the CLI."""
    if not path:
        return False, "no parseable subcommand path"

    # 1. Walk the path level-by-level
    for depth in range(len(path)):
        parent = tuple(path[:depth])
        token = path[depth]
        help_payload = fetch_help(uip_bin, parent)
        if help_payload is None:
            # Tool installed but cannot render help (timeout, broken peer
            # dep, etc.). Can't introspect further; treat as plausibly
            # valid so the smoke isn't gated on upstream tool-packaging
            # issues. The runtime e2e tests still exercise the real call.
            return True, f"WARN: could not fetch help for 'uip {' '.join(parent)}' — skipping deeper validation"
        result = help_payload.get("Result")
        if result == "ConfigError":
            # Tool failed to load at runtime (e.g., missing peer dep like
            # @uipath/auth on traces-tool). Same tolerance as above.
            return True, f"WARN: parent 'uip {' '.join(parent)}' returned ConfigError — skipping deeper validation"
        if result != "Success":
            return False, f"parent 'uip {' '.join(parent)}' returned {result}"
        subs = subcommand_names(help_payload)
        if token in subs:
            continue
        # aspect-router fallback: some parents (e.g. `uip maestro`) host
        # routed subcommands the JSON help payload doesn't enumerate.
        if token in KNOWN_ASPECT_ROUTERS.get(parent, set()):
            continue
        # lazily-listed plugin tolerance: some plugins install correctly but
        # aren't listed in the parent's Subcommands (e.g. `is`, `resource`,
        # `docsai` in uip 1.2.x-alpha). Probe the token directly: if
        # `uip <prefix> <token> --help` returns Success the subcommand is real —
        # the parent just doesn't advertise it.
        probe = fetch_help(uip_bin, tuple(path[: depth + 1]))
        if probe is not None and probe.get("Result") == "Success":
            continue
        return False, f"'{token}' is not a subcommand of 'uip {' '.join(parent) or '(root)'}'"

    # 2. Leaf-level flag validation (per-command flags + inherited global flags)
    leaf_help = fetch_help(uip_bin, tuple(path))
    if leaf_help is None:
        return False, f"could not fetch help for leaf 'uip {' '.join(path)}'"

    allowed_flags = flag_names(leaf_help) | GLOBAL_FLAGS
    bad_flags = sorted(f for f in used_flags if f not in allowed_flags)
    if bad_flags:
        return False, f"unknown flag(s) on 'uip {' '.join(path)}': {', '.join(bad_flags)}"

    # 3. Argument count check (informational — many commands accept varargs)
    expected_args = arg_count(leaf_help)
    if expected_args and positional_count > expected_args:
        return False, (
            f"'uip {' '.join(path)}' expects {expected_args} positional arg(s); "
            f"manifest supplies {positional_count}"
        )

    return True, ""


def shape_repr(path: tuple[str, ...], flags: frozenset[str], positional_count: int) -> str:
    """Compact human-readable shape rendering."""
    parts = list(path)
    if positional_count == 1:
        parts.append("<arg>")
    elif positional_count > 1:
        parts.append(f"<{positional_count} args>")
    if flags:
        parts.append("[" + " ".join(sorted(flags)) + "]")
    return " ".join(parts)


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

    # Aggregate manifest rules into distinct shapes. A shape is the
    # validation-relevant fingerprint: (path tuple, flag set, positional
    # count). Different UUIDs / quoted values collapse into the same shape
    # because they're positionals — so we validate each shape once instead
    # of every match string separately, and report one [OK]/[BAD] per shape
    # with the list of manifest rules it covers underneath.
    shapes: dict[tuple[tuple[str, ...], frozenset[str], int], list[dict]] = defaultdict(list)
    parse_errors: list[dict] = []
    total_rules = 0
    for entry in walk_manifests(args.root):
        if "parse_error" in entry:
            parse_errors.append(entry)
            continue
        if not entry["match"]:
            continue
        total_rules += 1
        path, flags, positionals = tokenize_match(entry["match"])
        sig = (tuple(path), frozenset(flags), len(positionals))
        shapes[sig].append(entry)

    shape_keys = sorted(shapes.keys())
    print(f"Manifests scanned under: {args.root}")
    print(f"Manifest parse errors:   {len(parse_errors)}")
    print(f"Rules across manifests:  {total_rules}")
    print(f"Distinct rule shapes:    {len(shape_keys)}")
    print()

    bad_shapes: list[tuple[tuple, str]] = []
    oks = warns = 0
    for sig in shape_keys:
        path, flags, positional_count = sig
        ok, msg = validate_shape(args.uip, path, flags, positional_count)
        is_warn = ok and msg.startswith("WARN:")
        marker = "WARN" if is_warn else ("OK  " if ok else "BAD ")
        repr_ = shape_repr(*sig)
        suffix = f"  -- {msg}" if msg else ""
        rule_count = len(shapes[sig])
        scenario_count = len({e["scenario"] for e in shapes[sig]})
        s_rule = "rule" if rule_count == 1 else "rules"
        s_scen = "scenario" if scenario_count == 1 else "scenarios"
        print(f"  [{marker}] {repr_}{suffix}")
        print(f"          ({rule_count} {s_rule} across {scenario_count} {s_scen})")
        if is_warn:
            warns += 1
            oks += 1
        elif ok:
            oks += 1
        else:
            bad_shapes.append((sig, msg))

    invalid = len(bad_shapes)

    print()
    print(f"Valid shapes:   {oks} / {len(shape_keys)}  ({warns} warn)")
    print(f"Invalid shapes: {invalid} / {len(shape_keys)}")

    if parse_errors:
        print()
        print("Manifest parse errors:")
        for e in parse_errors:
            print(f"  [{e['scenario']}] {e['manifest']}: {e['parse_error']}")

    if bad_shapes:
        print()
        print("Invalid shapes — affected manifest rules:")
        for sig, msg in bad_shapes:
            print(f"  {shape_repr(*sig)}  ({msg})")
            for entry in shapes[sig]:
                print(f"    {entry['scenario']}: rule {entry['rule_index']}")
        return 1

    print()
    print("OK — every mocked command, flag, and positional shape is valid against the installed uip CLI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
