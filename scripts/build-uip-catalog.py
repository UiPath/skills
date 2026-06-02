#!/usr/bin/env python3
"""
Build a snapshot of every reachable `uip` CLI verb.

Walks `uip --help-all --output json` and recurses into each group (groups
emit `Subcommands` in `uip <group> --help --output json`) to enumerate every
leaf command. Writes the result to assets/uip-catalog-snapshot.json so the
CLI-verb linter can verify task YAMLs offline.

Usage:
    python3 scripts/build-uip-catalog.py [--output PATH]
"""

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "assets" / "uip-catalog-snapshot.json"

ARG_SIG = re.compile(r"\s*[<\[].*")


def verb_count_error(new_count, prev_count, min_verbs, max_drop_frac):
    """Return an error string if the new catalog looks collapsed, else None.

    Cause-agnostic backstop against a bad build (#1203: 1115 -> 31 verbs):
    - absolute floor: fewer than `min_verbs` total, and
    - relative drop: more than `max_drop_frac` smaller than the prior snapshot.
    `prev_count` is None/0 when there is no existing snapshot to compare.
    Pure function — no I/O — so it is unit-testable without the CLI.
    """
    if min_verbs and new_count < min_verbs:
        return f"only {new_count} verbs collected (< floor {min_verbs})"
    if max_drop_frac is not None and prev_count:
        floor = prev_count * (1 - max_drop_frac)
        if new_count < floor:
            return (
                f"verb count dropped {prev_count} -> {new_count}, exceeding the "
                f"{max_drop_frac:.0%} max drop (floor {floor:.0f})"
            )
    return None


_DECODER = json.JSONDecoder()

# Top-level groups whose JSON help could not be enumerated. Populated by
# collect_top_level (broken-tool detection) and collect_group (per-group
# walk errors). Read by the consumer scripts via the snapshot's
# `unwalkable_groups` field — references under these prefixes are
# classified as Uncertain rather than Stale.
UNWALKABLE = set()

# Tool prefixes that are platform-specific and may not be installable on
# the runner that builds the catalog (e.g. `rpa` requires Windows + Studio
# Helm; the nightly refresh runs on ubuntu-latest where the rpa tool can't
# install). Marked unwalkable only when the prefix is NOT exposed as a
# top-level subcommand in the current catalog build — that way a catalog
# built on Windows still resolves `uip rpa …` verbs concretely.
PLATFORM_SPECIFIC_PREFIXES = {"rpa"}


def run_uip(args):
    try:
        proc = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        sys.exit("uip CLI not found on PATH. "
                 "Install with: npm install -g @uipath/cli")
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    text = proc.stdout.lstrip()
    try:
        # Some uip subcommands print a free-form addendum (e.g. "Typical
        # workflow: ...") after the JSON document. raw_decode reads the
        # first JSON value and ignores the trailing text.
        obj, _ = _DECODER.raw_decode(text)
        return obj
    except json.JSONDecodeError:
        return None


def strip_args(name):
    return ARG_SIG.sub("", name).strip()


def install_all_tools():
    """
    Install every plugin uip knows about via `uip tools list` and `uip tools
    search`. Plugin groups (solution, maestro, tm, df, ...) only contribute
    verbs to the catalog when installed.

    The @uipath/* packages live on public npm. The internal GitHub Packages
    feed carries divergent 1.0.0-alpha.* prereleases under the same scope, so
    if npm's @uipath scope is mapped there the catalog will pick up alpha
    surface. The nightly workflow pins the scope to public npm before this
    runs (`npm config set @uipath:registry https://registry.npmjs.org/`);
    set the same locally if you hit auth errors.
    """
    listed = run_uip(["tools", "list"]) or {}
    # `uip tools list` returns short names like "solution-tool".
    # `uip tools search` returns scoped names like "@uipath/solution-tool".
    # Normalise both to the short form for comparison.
    def short(name):
        return name.rsplit("/", 1)[-1] if name else ""

    installed = {short(t.get("name", "")) for t in listed.get("Data", []) or []}

    search_results = run_uip(["tools", "search"]) or {}
    attempted = succeeded = 0
    for tool in search_results.get("Data", []) or []:
        name = tool.get("name") or ""
        if not name or short(name) in installed:
            continue
        attempted += 1
        print(f"installing missing tool {name}", file=sys.stderr)
        proc = subprocess.run(
            ["uip", "tools", "install", name, "--output", "json"],
            capture_output=True, text=True, check=False,
        )
        if proc.returncode != 0:
            # npm prints errors to stderr; stdout (JSON success channel) is
            # usually empty on failure.
            err = (proc.stderr or proc.stdout or "").strip()[:200]
            print(f"  failed: {err}", file=sys.stderr)
        else:
            succeeded += 1

    # Fail loud if we tried to install tools and every one failed. The plugins
    # contribute the bulk of the catalog; a silent all-fail collapses it to the
    # ~31 base-CLI verbs (see #1203). Usual cause: the `@uipath` npm scope is
    # mapped to GitHub Packages (CLI alpha feed) instead of public npm, where
    # the tool packages live.
    if attempted and succeeded == 0:
        sys.exit(
            f"All {attempted} tool installs failed — refusing to build a "
            "base-CLI-only catalog. Is the @uipath npm scope pointed at public "
            "npm (https://registry.npmjs.org/)?"
        )


def collect_top_level():
    """
    Seed the walk from `uip --help --output json`. The top-level help lists
    every installed group (Subcommands). Each group is then walked
    recursively via collect_group.

    Also cross-references `uip tools list`: any installed tool whose
    commandPrefix is *missing* from the top-level subcommands has failed to
    load (typical cause: broken npm deps in the tool's package). Mark those
    prefixes as unwalkable so the scanner reports references under them as
    Uncertain instead of Stale.
    """
    data = run_uip(["--help"])
    if not data:
        sys.exit("uip --help returned no JSON (is uip installed?)")
    subs = data.get("Data", {}).get("Subcommands", []) or []
    verbs = set()
    groups = set()
    for sub in subs:
        name = strip_args(sub.get("Name", ""))
        if not name or name == "help":
            continue
        verbs.add(name)
        groups.add(name)

    # Only installed tools carry a reliable commandPrefix. The search result
    # lacks it and the tool-name convention (`@uipath/<x>-tool`) doesn't map
    # 1:1 to the prefix (`integrationservice-tool` → `is`, etc.) — so we
    # cannot infer prefixes for uninstalled tools without false positives.
    tools = run_uip(["tools", "list"]) or {}
    for tool in tools.get("Data", []) or []:
        prefix = tool.get("commandPrefix")
        if prefix and prefix not in groups:
            UNWALKABLE.add(prefix)
            print(f"tool {tool.get('name')!r}: installed but {prefix!r} is "
                  f"not exposed as top-level subcommand — marking unwalkable",
                  file=sys.stderr)
    # Platform-specific tools that simply aren't installed on this runner —
    # mark unwalkable so consumers fall back to Uncertain instead of Stale
    # for references like `uip rpa <verb>` on a Linux-built catalog.
    for prefix in PLATFORM_SPECIFIC_PREFIXES:
        if prefix not in groups:
            UNWALKABLE.add(prefix)
            print(f"platform-specific prefix {prefix!r} not exposed on this "
                  f"runner — marking unwalkable",
                  file=sys.stderr)
    return verbs, groups


def collect_group(group_path):
    data = run_uip([*group_path.split(), "--help"])
    if data is None or data.get("Result") == "Failure":
        # Tool errored, doesn't support `--output json`, or failed to load
        # (common for Click/Python plugins and tools with broken npm deps).
        # Mark so the scanner can downgrade findings under this prefix from
        # "stale" to "uncertain".
        UNWALKABLE.add(group_path)
        return set()
    subs = data.get("Data", {}).get("Subcommands", []) or []
    found = set()
    for sub in subs:
        name = strip_args(sub.get("Name", ""))
        if not name or name == "help":
            continue
        found.add(f"{group_path} {name}")
    return found


def expand(verbs, groups, workers=8):
    seen = set(groups)
    frontier = list(groups)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        while frontier:
            results = pool.map(collect_group, frontier)
            next_frontier = []
            for children in results:
                for child in children:
                    if child in verbs:
                        continue
                    verbs.add(child)
                    if child not in seen:
                        seen.add(child)
                        next_frontier.append(child)
            frontier = next_frontier
    return verbs


def get_cli_version():
    try:
        proc = subprocess.run(
            ["uip", "--version"], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        return "unknown"
    return proc.stdout.strip() or "unknown"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print JSON to stdout instead of writing to disk",
    )
    parser.add_argument(
        "--install-tools",
        action="store_true",
        help="Install every uip tool found via `uip tools search` before walking. "
             "Required for full coverage of plugin groups (admin, platform, ...). "
             "Slow; intended for CI.",
    )
    parser.add_argument(
        "--min-verbs",
        type=int,
        default=0,
        help="Refuse to write if fewer than N verbs were collected (absolute floor).",
    )
    parser.add_argument(
        "--max-drop-frac",
        type=float,
        default=None,
        help="Refuse to write if the verb count drops more than this fraction "
             "(0-1) vs the existing --output snapshot. E.g. 0.2 = abort on a >20%% drop.",
    )
    args = parser.parse_args()

    # Validate before any work: a fraction outside [0, 1] silently breaks the
    # relative guard (>1 yields a negative floor that never trips — a collapse
    # would slip through; <0 over-inflates it). Fail fast on misconfiguration.
    if args.max_drop_frac is not None and not 0 <= args.max_drop_frac <= 1:
        sys.exit(f"--max-drop-frac must be between 0 and 1 (inclusive), got {args.max_drop_frac}")

    if args.install_tools:
        install_all_tools()
    verbs, groups = collect_top_level()
    verbs = expand(verbs, groups)

    # Integrity guards — never overwrite a good snapshot with a collapsed one.
    prev_count = None
    if not args.stdout and args.output.exists():
        try:
            prev_count = len(json.loads(args.output.read_text()).get("verbs", []))
        except (json.JSONDecodeError, OSError):
            prev_count = None
    err = verb_count_error(len(verbs), prev_count, args.min_verbs, args.max_drop_frac)
    if err:
        sys.exit(f"Refusing to write catalog: {err}. Aborting suspected bad build.")

    snapshot = {
        "generated_at": dt.datetime.now(dt.timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "cli_version": get_cli_version(),
        "verbs": sorted(verbs),
        "unwalkable_groups": sorted(UNWALKABLE),
    }
    text = json.dumps(snapshot, indent=2) + "\n"

    if args.stdout:
        sys.stdout.write(text)
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text)
    print(
        f"Wrote {len(snapshot['verbs'])} verbs from uip {snapshot['cli_version']} "
        f"to {args.output.relative_to(REPO_ROOT)}"
    )


if __name__ == "__main__":
    main()
