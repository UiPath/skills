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


_DECODER = json.JSONDecoder()


def run_uip(args):
    proc = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
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

    Requires GitHub Packages authentication — uip 1.1.0+ pulls tools from
    https://npm.pkg.github.com and will fail with E401 otherwise. In CI,
    set `NPM_TOKEN` (or configure `.npmrc`) before running this script.
    """
    listed = run_uip(["tools", "list"]) or {}
    # `uip tools list` returns short names like "solution-tool".
    # `uip tools search` returns scoped names like "@uipath/solution-tool".
    # Normalise both to the short form for comparison.
    def short(name):
        return name.rsplit("/", 1)[-1] if name else ""

    installed = {short(t.get("name", "")) for t in listed.get("Data", []) or []}

    search_results = run_uip(["tools", "search"]) or {}
    for tool in search_results.get("Data", []) or []:
        name = tool.get("name") or ""
        if not name or short(name) in installed:
            continue
        print(f"installing missing tool {name}", file=sys.stderr)
        proc = subprocess.run(
            ["uip", "tools", "install", name, "--output", "json"],
            capture_output=True, text=True, check=False,
        )
        if proc.returncode != 0:
            print(f"  failed: {proc.stdout[:200]}", file=sys.stderr)


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
    return verbs, groups


UNWALKABLE = set()


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
    while frontier:
        with ThreadPoolExecutor(max_workers=workers) as pool:
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
    proc = subprocess.run(
        ["uip", "--version"], capture_output=True, text=True, check=False
    )
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
    args = parser.parse_args()

    if args.install_tools:
        install_all_tools()
    verbs, groups = collect_top_level()
    verbs = expand(verbs, groups)

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
