#!/usr/bin/env python3
"""Prune redundant agent/run_limits fields from task YAMLs.

For each task under tests/tasks/, compare every field in `agent:` and
`run_limits:` against tests/experiments/default.yaml and remove any that match
the inherited default. Also hoists deprecated `agent.max_turns` / `agent.turn_timeout`
into top-level `run_limits` before pruning (see coder_eval orchestration/experiment.py:163).

Usage:
    scripts/prune-task-defaults.py              # apply in place
    scripts/prune-task-defaults.py --dry-run    # show what would change
    scripts/prune-task-defaults.py path/to/file.yaml [more.yaml ...]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML

REPO = Path(__file__).resolve().parent.parent
DEFAULTS_PATH = REPO / "tests" / "experiments" / "default.yaml"
TASKS_ROOT = REPO / "tests" / "tasks"

# Fields under `agent:` that coder_eval auto-hoists into top-level `run_limits`
# (deprecated; warns to be removed 2026-05-20).
HOISTABLE = ("max_turns", "turn_timeout", "task_timeout")


def load_yaml(path: Path):
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 10_000  # don't reflow long lines
    # Match the repo's 2-space indented list style: "  - key:" not "- key:".
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml, yaml.load(path.read_text())


def prune_block(block, defaults: dict) -> list[str]:
    """Remove keys whose value equals the default, or whose value is an empty dict/list.

    Empty `{}` / `[]` carry no config — they're no-ops the coder_eval loader treats
    the same as "key absent". Returns removed keys.
    """
    removed = []
    if block is None:
        return removed
    defaults = defaults or {}
    for key in list(block.keys()):
        val = block[key]
        if key in defaults and val == defaults[key]:
            del block[key]
            removed.append(f"{key} (matches default)")
        elif isinstance(val, (dict, list)) and len(val) == 0:
            del block[key]
            removed.append(f"{key} (empty)")
    return removed


def process(path: Path, default_agent: dict, default_rl: dict, default_sandbox: dict, dry_run: bool) -> bool:
    yaml, data = load_yaml(path)
    if not isinstance(data, dict):
        return False

    changes: list[str] = []
    agent = data.get("agent")
    run_limits = data.get("run_limits")

    # Hoist deprecated top-level {max_turns,turn_timeout,task_timeout} → run_limits.
    # These also get auto-hoisted by the coder_eval loader (with a deprecation
    # warning) — see coder_eval/src/coder_eval/models/tasks.py:484-510.
    for field in HOISTABLE:
        if field not in data:
            continue
        if run_limits is None:
            from ruamel.yaml.comments import CommentedMap

            run_limits = CommentedMap()
            data["run_limits"] = run_limits
            data.yaml_set_comment_before_after_key("run_limits", before="\n")
        if isinstance(run_limits, dict) and field in run_limits:
            if run_limits[field] == data[field]:
                del data[field]
                changes.append(f"drop top-level {field} (duplicate of run_limits.{field})")
            else:
                changes.append(
                    f"drop top-level {field}={data[field]!r} (conflicts with run_limits.{field}={run_limits[field]!r}; kept run_limits)"
                )
                del data[field]
        else:
            run_limits[field] = data.pop(field)
            changes.append(f"hoist top-level {field} → run_limits.{field}")

    # Hoist deprecated agent.{max_turns,turn_timeout,task_timeout} → run_limits.
    if isinstance(agent, dict):
        for field in HOISTABLE:
            if field not in agent:
                continue
            if run_limits is None:
                from ruamel.yaml.comments import CommentedMap

                run_limits = CommentedMap()
                data["run_limits"] = run_limits
                # Visually separate the new block from preceding content.
                data.yaml_set_comment_before_after_key("run_limits", before="\n")
            if isinstance(run_limits, dict) and field in run_limits:
                if run_limits[field] == agent[field]:
                    del agent[field]
                    changes.append(f"drop agent.{field} (duplicate of run_limits.{field})")
                else:
                    # conflict: prefer the canonical run_limits value, drop deprecated
                    changes.append(
                        f"drop agent.{field}={agent[field]!r} (conflicts with run_limits.{field}={run_limits[field]!r}; kept run_limits)"
                    )
                    del agent[field]
            else:
                run_limits[field] = agent.pop(field)
                changes.append(f"hoist agent.{field} → run_limits.{field}")

    # Prune fields that match defaults (or are empty {}/[]).
    sandbox = data.get("sandbox")
    for block_name, block, defaults in (
        ("agent", agent, default_agent),
        ("run_limits", run_limits, default_rl),
        ("sandbox", sandbox, default_sandbox),
    ):
        if isinstance(block, dict):
            for note in prune_block(block, defaults):
                changes.append(f"drop {block_name}.{note}")

    # Remove now-empty top-level blocks.
    for block_name in ("agent", "run_limits", "sandbox"):
        block = data.get(block_name)
        if isinstance(block, dict) and not block:
            del data[block_name]
            changes.append(f"drop empty {block_name}:")

    if not changes:
        return False

    rel = path.relative_to(REPO)
    print(f"{rel}")
    for c in changes:
        print(f"  - {c}")

    if not dry_run:
        import io
        import re

        buf = io.StringIO()
        yaml.dump(data, buf)
        # Collapse runs of 2+ blank lines into 1 (left behind when whole blocks
        # like `agent:` are dropped — ruamel keeps the blank lines that flanked
        # the removed key on each side).
        cleaned = re.sub(r"\n{3,}", "\n\n", buf.getvalue())
        # Ensure agent/sandbox/run_limits are preceded by a blank line. Internal
        # blank lines can disappear when ruamel attaches them to a since-deleted
        # key (e.g. when `agent.turn_timeout` was the last key before `sandbox:`).
        cleaned = re.sub(
            r"(?<=\n)(?<!\n\n)(?=(?:agent|sandbox|run_limits):)",
            "\n",
            cleaned,
        )
        path.write_text(cleaned)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", type=Path, help="Task YAMLs (default: all under tests/tasks/)")
    ap.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    args = ap.parse_args()

    _, defaults_doc = load_yaml(DEFAULTS_PATH)
    defaults_block = defaults_doc.get("defaults") or {}
    default_agent = defaults_block.get("agent") or {}
    default_rl = defaults_block.get("run_limits") or {}
    default_sandbox = defaults_block.get("sandbox") or {}

    if args.paths:
        files = [p.resolve() for p in args.paths]
    else:
        files = sorted(TASKS_ROOT.rglob("*.yaml"))

    changed = 0
    for f in files:
        if process(f, default_agent, default_rl, default_sandbox, args.dry_run):
            changed += 1

    verb = "would update" if args.dry_run else "updated"
    print(f"\n{verb} {changed} / {len(files)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
