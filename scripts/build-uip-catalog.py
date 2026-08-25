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
import time
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


def unwalkable_regression_error(new_unwalkable, prev_unwalkable, prev_verbs):
    """Return an error string if a previously-walked group is now unwalkable, else None.

    A group whose `--help` walk fails contributes ZERO children to the
    catalog while the group node itself survives, so the loss is invisible to
    verb_count_error: on 2026-07-30 a build lost the entire `rpa debug`
    subtree (16 verbs) plus `rpa analyzer-rules list` and `rpa files diff`,
    a 0.5% drop that sailed past --max-drop-frac 0.2 and produced a PR that
    would have auto-merged.

    A group is a regression when all three hold:
      1. it is unwalkable in THIS build,
      2. it was NOT unwalkable in the committed snapshot, and
      3. the committed snapshot enumerated at least one child under it.

    Condition 3 is what keeps this quiet. Leaf commands legitimately land in
    UNWALKABLE — `uip rpa pack --help` emits no `Subcommands` — and they have
    no children in the previous snapshot, so they never trip the guard. A
    group genuinely deleted from the CLI is also silent: it never enters the
    walk frontier, so collect_group is never called and it cannot appear in
    `new_unwalkable`. That leaves exactly the flaky/broken case.

    Pure function — no I/O — so it is unit-testable without the CLI.
    """
    prev_unwalkable = set(prev_unwalkable or ())
    regressed = []
    for group in sorted(set(new_unwalkable or ())):
        if group in prev_unwalkable:
            continue
        prefix = f"{group} "
        lost = sorted(v for v in (prev_verbs or ()) if v.startswith(prefix))
        if lost:
            regressed.append((group, lost))
    if not regressed:
        return None
    total = sum(len(lost) for _, lost in regressed)
    detail = "; ".join(
        f"{group!r} (-{len(lost)}: {', '.join(lost[:3])}"
        f"{', …' if len(lost) > 3 else ''})"
        for group, lost in regressed
    )
    return (
        f"{len(regressed)} group(s) walked in the committed snapshot are "
        f"unwalkable in this build, dropping {total} verb(s): {detail}"
    )


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

# How many times to attempt a group's `--help` walk before marking it
# unwalkable, and the base backoff between attempts (multiplied by the
# attempt number). A failed walk drops the group's entire subtree from the
# catalog, so a transient failure is expensive — see collect_group.
GROUP_HELP_ATTEMPTS = 3
GROUP_HELP_BACKOFF_SECONDS = 1.0


def _ci(d, key):
    """Case-insensitive dict lookup for `uip --output json` payloads.

    The CLI PascalCases every key of a `--output json` `Data` payload (cli
    PR #2266), so a tool's name arrives as `Name`, not `name`. Reading the
    documented lowercase key yields None — which made install_all_tools skip
    every tool and collapse the catalog to the 31 base verbs (#1203). Same
    break class guarded by tests/scripts/test_runtime_payload_key_casing.py.
    """
    if not isinstance(d, dict):
        return None
    for k, v in d.items():
        if isinstance(k, str) and k.lower() == key.lower():
            return v
    return None


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
    # Drop the trailing "[options]" / "<arg>" signature, then any alias suffix.
    # `uip --help --output json` bakes aliases into a subcommand's Name with a
    # pipe — orchestrator renders as "or|orchestrator" (it's the only aliased
    # tool). Keep the canonical first token ("or") so the group matches its
    # CommandPrefix and walks as `uip or …`; otherwise the whole orchestrator
    # group is dropped (#1203 follow-up). Harmless once cli #2331 emits a bare
    # Name + separate Aliases — the split is then a no-op.
    return ARG_SIG.sub("", name).strip().split("|", 1)[0].strip()


def tool_dist_tag():
    """
    Derive the npm dist-tag to install tools under from the running CLI's own
    prerelease tag, so tools always match the CLI's line:
      1.199.0-dev.7923   -> "dev"     (GitHub Packages prerelease train)
      1.198.0-preview.84 -> "preview" (npmjs prerelease train)
      1.197.1            -> None      (stable; install the plain `latest`)
    """
    version = get_cli_version()
    dash = version.find("-")
    if dash == -1:
        return None
    return version[dash + 1:].split(".")[0] or None


def install_all_tools():
    """
    Install every plugin uip knows about (discovered via `uip tools search`)
    with npm, at the dist-tag matching the running CLI (see tool_dist_tag).
    Plugin groups (solution, maestro, tm, df, ...) only contribute verbs to the
    catalog when installed.

    Install with npm directly — NOT `uip tools install`. cli PR #2650 made `dev`
    a publish dist-tag but NOT a release channel (channels are just
    {stable, preview}), so on a `-dev` CLI `uip tools install` resolves to the
    `stable` channel and can't find a matching `-dev` tool ("No compatible
    version"). npm resolves `@dev`/`@preview` straight to the latest prerelease;
    the CLI then discovers the plugin on disk under `$(npm root -g)/@uipath/*`.

    Tools must come from the SAME feed as the CLI. The nightly tracks cli/main
    and installs both from GitHub Packages under `@dev` (the workflow sets
    `@uipath:registry=https://npm.pkg.github.com/` + auth). Locally, install the
    CLI and tools from whichever feed you intend the catalog to reflect — keep
    both on the same one.
    """
    tag = tool_dist_tag()
    listed = run_uip(["tools", "list"]) or {}
    # `uip tools list` returns short names like "solution-tool".
    # `uip tools search` returns scoped names like "@uipath/solution-tool".
    # Normalise both to the short form for comparison.
    def short(name):
        return name.rsplit("/", 1)[-1] if name else ""

    # Read tool names case-insensitively — the CLI returns `Name`, not `name`
    # (see _ci). A raw `.get("name")` silently skips every tool (#1203).
    installed = {short(_ci(t, "name") or "") for t in (_ci(listed, "data") or [])}

    search_results = run_uip(["tools", "search"]) or {}
    attempted = succeeded = 0
    for tool in (_ci(search_results, "data") or []):
        name = _ci(tool, "name") or ""
        if not name or short(name) in installed:
            continue
        spec = f"{name}@{tag}" if tag else name
        attempted += 1
        print(f"installing missing tool {spec}", file=sys.stderr)
        proc = subprocess.run(
            ["npm", "install", "-g", spec],
            capture_output=True, text=True, check=False,
        )
        if proc.returncode != 0:
            # npm prints errors to stderr; stdout is usually empty on failure.
            err = (proc.stderr or proc.stdout or "").strip()[:200]
            print(f"  failed: {err}", file=sys.stderr)
        else:
            succeeded += 1

    # Fail loud if we tried to install tools and every one failed. The plugins
    # contribute the bulk of the catalog; a silent all-fail collapses it to the
    # ~31 base-CLI verbs (see #1203). Usual cause: the `@uipath` npm scope isn't
    # pointed at the feed that carries the CLI's line (GitHub Packages for
    # -dev/-alpha, npmjs for stable).
    if attempted and succeeded == 0:
        sys.exit(
            f"All {attempted} tool installs failed — refusing to build a "
            "base-CLI-only catalog. Is the @uipath npm scope pointed at the "
            "feed for this CLI line (GitHub Packages for -dev, npmjs for stable)?"
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
    for tool in (_ci(tools, "data") or []):
        # Case-insensitive: the CLI returns `CommandPrefix`/`Name`, not the
        # lowercase forms (see _ci). A raw lowercase read yields None and
        # silently disables broken-tool detection.
        prefix = _ci(tool, "commandPrefix")
        if prefix and prefix not in groups:
            UNWALKABLE.add(prefix)
            print(f"tool {_ci(tool, 'name')!r}: installed but {prefix!r} is "
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
    # Retry before giving up: a single failed `--help` silently deletes the
    # group's whole subtree from the catalog, and the failures are not always
    # deterministic (the unwalkable set churns between builds minutes apart —
    # `rpa debug` walked at 05:35 UTC on 2026-07-30 and did not at 21:39).
    # Cost is bounded: only failing groups retry, and a healthy build has few.
    data = None
    for attempt in range(1, GROUP_HELP_ATTEMPTS + 1):
        data = run_uip([*group_path.split(), "--help"])
        if data is not None and data.get("Result") != "Failure":
            break
        if attempt < GROUP_HELP_ATTEMPTS:
            print(f"group {group_path!r}: help walk failed "
                  f"(attempt {attempt}/{GROUP_HELP_ATTEMPTS}) — retrying",
                  file=sys.stderr)
            time.sleep(GROUP_HELP_BACKOFF_SECONDS * attempt)
    if data is None or data.get("Result") == "Failure":
        # Tool errored, doesn't support `--output json`, or failed to load
        # (common for Click/Python plugins and tools with broken npm deps).
        # Also the normal outcome for a leaf command, which emits no
        # Subcommands. Mark so the scanner can downgrade findings under this
        # prefix from "stale" to "uncertain".
        UNWALKABLE.add(group_path)
        print(f"group {group_path!r}: unwalkable after "
              f"{GROUP_HELP_ATTEMPTS} attempt(s)", file=sys.stderr)
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
    parser.add_argument(
        "--allow-unwalkable-regression",
        action="store_true",
        help="Write the catalog even if a group that was walked in the existing "
             "--output snapshot is unwalkable in this build. Escape hatch for a "
             "genuine, permanent loss of JSON help; without it such a build is "
             "refused because the cause is usually transient.",
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
    prev = None
    if not args.stdout and args.output.exists():
        try:
            prev = json.loads(args.output.read_text())
        except (json.JSONDecodeError, OSError):
            prev = None
    prev_verbs = (prev or {}).get("verbs") or []
    prev_unwalkable = (prev or {}).get("unwalkable_groups") or []
    prev_count = len(prev_verbs) if prev else None

    err = verb_count_error(len(verbs), prev_count, args.min_verbs, args.max_drop_frac)
    if err:
        sys.exit(f"Refusing to write catalog: {err}. Aborting suspected bad build.")

    # Subtree-loss guard. verb_count_error cannot see this: losing a whole
    # command group is a small fraction of a ~1380-verb catalog.
    regression = unwalkable_regression_error(UNWALKABLE, prev_unwalkable, prev_verbs)
    if regression and not args.allow_unwalkable_regression:
        sys.exit(
            f"Refusing to write catalog: {regression}. Re-run the build first — "
            "these walks are often transient. Use --allow-unwalkable-regression "
            "only if the loss is real: either the CLI genuinely stopped exposing "
            "JSON help for these groups, or the committed snapshot is itself a "
            "flaky build whose extra groups this good build cannot match."
        )
    if regression:
        print(f"warning: accepting unwalkable regression ({regression})",
              file=sys.stderr)

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
