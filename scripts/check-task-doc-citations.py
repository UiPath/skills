#!/usr/bin/env python3
"""Fail when a task YAML cites a skill reference file that does not exist.

Task prompts and grader notes under tests/tasks/<skill>/ often name the skill
doc that states the rule under test, for example "write a placeholder task per
references/placeholder-tasks.md". When that doc is renamed or retired, nothing
else re-reads the task, so the prompt keeps sending the agent to a file it
cannot open (UiPath/skills#4531: #675 renamed skeleton-tasks.md, and the v2
Flow promotion retired references/plugins/ixp/impl.md, but tasks kept citing
both).

A citation is any `<prefix>references/<path>.md` in a task YAML:

- `skills/<other>/.../references/x.md` resolves inside skills/<other>.
- Anything else resolves inside the skill the task folder is named after
  (tests/tasks/<skill>/...), with any leading folders kept, so
  `author/references/x.md` means skills/<skill>/author/references/x.md.

A citation passes when the file exists in any generation of that skill:
skills/, preview/skills/ or classic/skills/. A task folder that is not a skill
(for example tests/tasks/activation/) only has its `skills/<other>/` citations
checked.

Usage:
    python3 scripts/check-task-doc-citations.py            # scan tests/tasks
    python3 scripts/check-task-doc-citations.py --root R   # scan another repo root

Exit codes:
    0 - every citation resolves
    1 - one or more dead citations (printed with GitHub annotations)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SKILL_TREES = ("skills", "preview/skills", "classic/skills")

# `(?<![\w.-])` keeps the match from starting mid-word; the prefix is any run of
# path segments before `references/`, so `skills/x/references/...`,
# `author/references/...` and a bare `references/...` are all captured.
_CITATION_RE = re.compile(
    r"(?<![\w.-])(?P<prefix>(?:[\w.$-]+/)*)references/(?P<rest>[\w./-]+?\.md)\b"
)
_SKILLS_PREFIX_RE = re.compile(r"(?:^|/)skills/(?P<skill>uipath-[\w-]+)/(?P<sub>(?:[\w-]+/)*)$")


def skill_exists(root: Path, skill: str) -> bool:
    return any((root / tree / skill).is_dir() for tree in SKILL_TREES)


def resolve(root: Path, task_skill: str | None, prefix: str, rest: str) -> tuple[str | None, str]:
    """Return (skill, path inside the skill) for a citation, or (None, "") to skip."""
    m = _SKILLS_PREFIX_RE.search(prefix)
    if m:
        return m.group("skill"), f"{m.group('sub')}references/{rest}"
    if task_skill is None:
        return None, ""
    # Leading `../` or `$VAR/` segments carry no location inside the skill.
    sub = "".join(
        seg + "/" for seg in prefix.split("/") if seg and seg != ".." and seg != "." and not seg.startswith("$")
    )
    return task_skill, f"{sub}references/{rest}"


def exists(root: Path, skill: str, rel: str) -> bool:
    return any((root / tree / skill / rel).is_file() for tree in SKILL_TREES)


def scan(root: Path) -> list[tuple[str, int, str, str]]:
    """Return (task file, line, citation, skill) for every dead citation."""
    dead = []
    tasks_root = root / "tests" / "tasks"
    for path in sorted(tasks_root.rglob("*")):
        if path.suffix not in (".yaml", ".yml") or not path.is_file():
            continue
        folder = path.relative_to(tasks_root).parts[0]
        task_skill = folder if skill_exists(root, folder) else None
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in _CITATION_RE.finditer(line):
                skill, rel = resolve(root, task_skill, m.group("prefix"), m.group("rest"))
                if skill is None:
                    continue
                if not exists(root, skill, rel):
                    cited = m.group(0)
                    dead.append((path.relative_to(root).as_posix(), lineno, cited, skill))
    return dead


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repo root to scan (default: this repo)")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    dead = scan(root)
    if not dead:
        print("Every skill reference cited in tests/tasks resolves.")
        return 0

    for file, line, cited, skill in dead:
        print(f"::error file={file},line={line}::{cited} is not in skills/, preview/skills/ or classic/skills/{skill}")
        print(f"  {file}:{line}: {cited} (skill {skill})")
    print(
        f"\n{len(dead)} dead skill-reference citation(s). The cited doc was renamed or retired:"
        "\npoint the task at the doc that now states the rule, or name the rule instead of a file.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
