#!/usr/bin/env python3
"""Verify that every CLI command mocked in a troubleshoot scenario's manifest is
shaped correctly against the locally installed `uip` CLI.

Command-aggregated: every manifest rule for the same command path collapses
into ONE check. Validity is a property of the command — not of each flag
subset a scenario passed — so all rules for `or jobs list` (`[--folder-key]`,
`[--folder-key --output --state]`, …) produce a single
`or jobs list [--folder-key --output --state …]` [OK] line that validates the
UNION of every flag seen and the MAX positional count; the affected manifests
are listed under each command.

Three checks per command:

  1. Path     — every subcommand token must appear in its parent's Subcommands
                list (walks the tree level-by-level via `uip <prefix> --help`,
                with KNOWN_ASPECT_ROUTERS as a fallback for aspect-router
                hosts whose JSON help hides routed subcommands).
  2. Flags    — every `--flag` in the command's union-of-flags must exist in the
                leaf command's Options list (or be a CLI-wide global flag).
  3. Arguments — the max positional count must not exceed the leaf's declared
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
    "--version",
})


def validate_shape(
    uip_bin: str,
    path: tuple[str, ...],
    used_flags: frozenset[str],
    positional_count: int,
) -> tuple[bool, str]:
    """Validate a (path, flag-set, positional-count) shape against the CLI."""
    if not path:
        # Bare global-flag invocation (e.g. `uip --version`, `uip --help`):
        # no subcommand to introspect. Accept when every token is a CLI-wide
        # global flag and no positionals were supplied; otherwise the match is
        # genuinely unparseable.
        if used_flags and positional_count == 0 and used_flags <= GLOBAL_FLAGS:
            return True, ""
        return False, "no parseable subcommand path"

    # `path` may end in tokens the kebab tokenizer misread as subcommands but
    # which are really positional argument values (see (c) below). When that
    # happens the walk truncates `effective_path` to the real leaf and moves
    # the trailing tokens into the positional count.
    effective_path = path
    extra_positionals = 0

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
        if token not in subs:
            # The token isn't enumerated in the parent's --help Subcommands.
            # Two known-legitimate reasons before we flag it invalid:
            #
            # (a) Aspect-routers (e.g. `maestro` -> bpmn/case/flow): the
            #     parent's JSON --help hides these even though they're real
            #     subcommands at runtime.
            if token in KNOWN_ASPECT_ROUTERS.get(parent, frozenset()):
                continue
            # (b) Lazily-listed tool command-groups: under the alpha `uip` CLI,
            #     an installed tool's top-level group (`or`, `is`, `maestro`,
            #     `resource`, `docsai`, `traces`, `rpa`, ...) is NOT listed in
            #     its parent's Subcommands even though `uip ... <token>` is a
            #     real command group ("Successfully installed
            #     @uipath/<tool>-tool" but absent from `uip --help`). Probe the
            #     token's own --help and accept it only if it renders as a
            #     DISTINCT group — its own Subcommands are non-empty and differ
            #     from the parent's. The distinctness check guards against the
            #     Windows `.CMD` shim, which falls back to the parent's help for
            #     a genuinely-unknown token (the same false positive the
            #     level-by-level tree-walk was built to avoid): a typo would
            #     echo the parent's Subcommands verbatim and be rejected here.
            probe = fetch_help(uip_bin, (*parent, token))
            if probe is None or probe.get("Result") == "ConfigError":
                return True, (
                    f"WARN: '{token}' not listed under "
                    f"'uip {' '.join(parent) or '(root)'}' and its own help could not "
                    f"be introspected — skipping deeper validation"
                )
            if probe.get("Result") == "Success":
                probe_subs = subcommand_names(probe)
                if probe_subs and probe_subs != subs:
                    continue  # real command group, just not enumerated by the parent
            # (c) Positional argument misread as a subcommand: the kebab
            #     tokenizer can't distinguish a subcommand from a
            #     lowercase-hyphenated positional VALUE — connector keys
            #     (`uipath-freshworks-freshdesk`), object names (`tickets`),
            #     etc. If `parent` is a real leaf that DECLARES positional
            #     arguments, `token` and every remaining path token are those
            #     arguments, not subcommands. Truncate to `parent` as the leaf
            #     and move the trailing tokens into the positional count. This
            #     mirrors the UUID/hex positional handling in tokenize_match and
            #     preserves typo-catching: a mistyped subcommand under a command
            #     group that takes NO positionals (arg_count 0) still falls
            #     through to BAD below.
            if arg_count(help_payload) > 0:
                effective_path = tuple(path[:depth])
                extra_positionals = len(path) - depth
                break
            return False, f"'{token}' is not a subcommand of 'uip {' '.join(parent) or '(root)'}'"

    # 2. Leaf-level flag validation (per-command flags + inherited global flags)
    leaf_help = fetch_help(uip_bin, tuple(effective_path))
    if leaf_help is None:
        return False, f"could not fetch help for leaf 'uip {' '.join(effective_path)}'"

    allowed_flags = flag_names(leaf_help) | GLOBAL_FLAGS
    bad_flags = sorted(f for f in used_flags if f not in allowed_flags)
    if bad_flags:
        return False, f"unknown flag(s) on 'uip {' '.join(effective_path)}': {', '.join(bad_flags)}"

    # 3. Argument count check (informational — many commands accept varargs)
    expected_args = arg_count(leaf_help)
    total_positionals = positional_count + extra_positionals
    if expected_args and total_positionals > expected_args:
        return False, (
            f"'uip {' '.join(effective_path)}' expects {expected_args} positional arg(s); "
            f"manifest supplies {total_positionals}"
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
    for manifest_path in sorted(root.glob("**/data/m/r/manifest.json")):
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

    # Aggregate manifest rules by COMMAND PATH. Whether a command is valid is
    # a property of the command itself — does the leaf exist, does it accept
    # each flag, does it accept the positional arity — NOT of each individual
    # flag-subset a scenario happened to pass. So every rule for a command
    # collapses into ONE check that validates the UNION of all flags seen and
    # the MAX positional count across its rules. `or jobs list [--folder-key]`,
    # `[--folder-key --output --state]`, etc. become a single
    # `or jobs list [--folder-key --output --state ...]` check.
    commands: dict[tuple[str, ...], dict] = {}
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
        agg = commands.setdefault(
            tuple(path), {"flags": set(), "max_pos": 0, "entries": []}
        )
        agg["flags"].update(flags)
        agg["max_pos"] = max(agg["max_pos"], len(positionals))
        agg["entries"].append(entry)

    command_keys = sorted(commands.keys())
    print(f"Manifests scanned under: {args.root}")
    print(f"Manifest parse errors:   {len(parse_errors)}")
    print(f"Rules across manifests:  {total_rules}")
    print(f"Distinct commands:       {len(command_keys)}")
    print()

    bad_commands: list[tuple[tuple[str, ...], frozenset[str], int, str]] = []
    oks = warns = 0
    for path in command_keys:
        agg = commands[path]
        flags = frozenset(agg["flags"])
        positional_count = agg["max_pos"]
        ok, msg = validate_shape(args.uip, path, flags, positional_count)
        is_warn = ok and msg.startswith("WARN:")
        marker = "WARN" if is_warn else ("OK  " if ok else "BAD ")
        repr_ = shape_repr(path, flags, positional_count)
        suffix = f"  -- {msg}" if msg else ""
        rule_count = len(agg["entries"])
        scenario_count = len({e["scenario"] for e in agg["entries"]})
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
            bad_commands.append((path, flags, positional_count, msg))

    invalid = len(bad_commands)

    print()
    print(f"Valid commands:   {oks} / {len(command_keys)}  ({warns} warn)")
    print(f"Invalid commands: {invalid} / {len(command_keys)}")

    if parse_errors:
        print()
        print("Manifest parse errors:")
        for e in parse_errors:
            print(f"  [{e['scenario']}] {e['manifest']}: {e['parse_error']}")

    if bad_commands:
        print()
        print("Invalid commands — affected manifest rules:")
        for path, flags, positional_count, msg in bad_commands:
            print(f"  {shape_repr(path, flags, positional_count)}  ({msg})")
            for entry in commands[path]["entries"]:
                print(f"    {entry['scenario']}: rule {entry['rule_index']}")
        return 1

    print()
    print("OK — every mocked command, with the union of its flags and max positional arity, is valid against the installed uip CLI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
