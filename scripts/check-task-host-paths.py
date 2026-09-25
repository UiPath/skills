#!/usr/bin/env python3
"""Block new $TASK_DIR / $SKILLS_REPO_PATH host-path references under tests/tasks/.

#3271 migrated the task corpus off these two host-path escape hatches: sandbox
drivers (docker/tempdir) don't have a full host repo checkout, so a task that
reaches for $TASK_DIR or $SKILLS_REPO_PATH either breaks under those drivers or
silently reintroduces a host-path dependency the migration removed. Shared
fixtures/scripts a task needs belong in sandbox.template_sources (agent-visible)
or are reached via $REFERENCE_DIR (grading-only, invisible to the agent) — see
the #3271 commit message and tests/README.md.

A DOCUMENTED set of exceptions was deliberately left in place by that migration
(optional ambient skills/<name>/references/*.md strengthening checks that
degrade gracefully when the var is unset, tasks needing genuinely broader
host-repo access, and meta-tests recognizing the token as legacy text). This
script does not relitigate those — it only blocks lines a PR ADDS. Pre-existing
occurrences (including the documented exceptions) are untouched, so this is a
one-way ratchet, not a full-corpus ban.

Usage:
    python3 scripts/check-task-host-paths.py                     # diff vs merge-base with origin/main
    python3 scripts/check-task-host-paths.py --base-ref <ref>    # diff vs a specific ref
    python3 scripts/check-task-host-paths.py --full              # scan the whole tree (audit mode, always exits 1 if any hit)

Exit codes:
    0 — no new (or, in --full mode, no) occurrences found
    1 — one or more offending lines (paths printed, with GitHub annotations)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROOT = REPO_ROOT / "tests" / "tasks"

_TOKEN_RE = re.compile(r"\bTASK_DIR\b|\bSKILLS_REPO_PATH\b")

# Per-suite meta-tests that price/resolve run_command criteria off the raw YAML
# text: each one's regexes and docstrings MENTION both retired tokens (and, for
# $TASK_DIR, the still-supported literal form) by design, to keep pricing any
# task that still legitimately uses them and to document the $REFERENCE_DIR
# migration inline. This is the "meta-tests recognizing the token as legacy
# text" exception #3271 documented — not a host-path dependency to ratchet.
_EXEMPT_BASENAMES = {"test_criterion_budgets.py"}

_ADVICE = (
    "$TASK_DIR / $SKILLS_REPO_PATH are retired host-path escape hatches (#3271) —\n"
    "sandbox drivers don't have a full host repo checkout. Stage the file the task\n"
    "needs via sandbox.template_sources (agent-visible) or reach it via\n"
    "$REFERENCE_DIR (grading-only). See tests/README.md and the #3271 commit\n"
    "message for the migration pattern and its documented exceptions."
)


def _rel(path: str) -> str:
    p = Path(path)
    try:
        return str(p.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return path


def _run(args: list[str]) -> str:
    return subprocess.run(args, cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout


def _full_scan(root: Path) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.name in _EXEMPT_BASENAMES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), start=1):
            if _TOKEN_RE.search(line):
                hits.append((_rel(str(path)), n, line.strip()))
    return hits


def _diff_scan(base_ref: str, root: Path) -> list[tuple[str, int, str]]:
    rel_root = root.relative_to(REPO_ROOT).as_posix()
    try:
        merge_base = _run(["git", "merge-base", base_ref, "HEAD"]).strip()
    except subprocess.CalledProcessError as exc:
        sys.exit(f"could not resolve merge-base against {base_ref!r}: {exc.stderr}")

    diff = _run(
        ["git", "diff", "--unified=0", "--no-color", merge_base, "HEAD", "--", rel_root]
    )

    hits: list[tuple[str, int, str]] = []
    current_file = None
    new_line_no = None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[4:]
            if path == "/dev/null" or Path(path[2:]).name in _EXEMPT_BASENAMES:
                current_file = None
            else:
                current_file = path[2:]  # strip "b/"
            continue
        if line.startswith("@@ "):
            match = re.search(r"\+(\d+)", line)
            new_line_no = int(match.group(1)) if match else None
            continue
        if line.startswith("+") and not line.startswith("+++"):
            if current_file is not None and new_line_no is not None:
                content = line[1:]
                if _TOKEN_RE.search(content):
                    hits.append((current_file, new_line_no, content.strip()))
                new_line_no += 1
            continue
        if line.startswith("-") and not line.startswith("---"):
            continue
    return hits


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=str(DEFAULT_ROOT))
    parser.add_argument("--base-ref", default="origin/main", help="ref to diff against (default: origin/main)")
    parser.add_argument("--full", action="store_true", help="scan the whole tree instead of diffing")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        sys.exit(f"root not found: {root}")

    hits = _full_scan(root) if args.full else _diff_scan(args.base_ref, root)

    if not hits:
        mode = "full scan" if args.full else f"diff vs {args.base_ref}"
        print(f"OK — no $TASK_DIR/$SKILLS_REPO_PATH references ({mode}).")
        return 0

    print(f"FAIL — {len(hits)} $TASK_DIR/$SKILLS_REPO_PATH reference(s) found under {root}:\n")
    for path, line_no, content in hits:
        print(f"::error file={path},line={line_no}::retired $TASK_DIR/$SKILLS_REPO_PATH reference")
        print(f"  {path}:{line_no}  {content}")
    print()
    print(_ADVICE)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
