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

A citation passes when the file exists in a tree an eval catalog loads:
skills/ (the default package, which nightly and smoke load) or preview/skills/
(the preview catalog, which flow-v2-preview loads). classic/skills/ does not
count: it holds a retained previous generation that only a pinned flavor
(skill-flavors/<flavor>/<skill>/.canonical) composes, no experiment loads it,
and no task can declare that it targets it. So a task citing a doc that only the
classic tree still has sends the agent to a file its catalog does not ship
(#4533 review: quality_04 cited v1-only references/brownfield.md once #4529
moved v1 Case to classic/).

A `#fragment` on a citation must match a heading of the cited file, with the
same GitHub slug rules as scripts/check-skill-links.mjs (inline code and link
text kept, lowercased, every character but letters, digits, `_`, `-` and space
dropped, spaces to `-`, repeats suffixed `-1`, `-2`), or an `<a id>`/`<a name>`.

A task folder that is not a skill (for example tests/tasks/activation/) only has
its `skills/<other>/` citations checked. A `uipath-*` task folder with no skill
folder in any tree is reported as a warning: its tasks grade a skill nothing
ships, which is a skill-removal leftover for that PR to decide, not a citation.

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

# Trees an eval catalog loads. classic/skills only feeds a pinned flavor build.
SHIPPED_TREES = ("skills", "preview/skills")
ALL_TREES = SHIPPED_TREES + ("classic/skills",)

# `(?<![\w.-])` keeps the match from starting mid-word; the prefix is any run of
# path segments before `references/`, so `skills/x/references/...`,
# `author/references/...` and a bare `references/...` are all captured.
_CITATION_RE = re.compile(
    r"(?<![\w.-])(?P<prefix>(?:[\w.$-]+/)*)references/(?P<rest>[\w./-]+?\.md)\b(?:#(?P<anchor>[\w-]+))?"
)
_SKILLS_PREFIX_RE = re.compile(r"(?:^|/)skills/(?P<skill>[\w-]+)/(?P<sub>(?:[\w-]+/)*)$")


def skill_exists(root: Path, skill: str) -> bool:
    return any((root / tree / skill).is_dir() for tree in ALL_TREES)


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


def shipped_file(root: Path, skill: str, rel: str) -> Path | None:
    """The cited file in the first shipped tree that has it, else None."""
    for tree in SHIPPED_TREES:
        candidate = root / tree / skill / rel
        if candidate.is_file():
            return candidate
    return None


def classic_only(root: Path, skill: str, rel: str) -> bool:
    return (root / "classic" / "skills" / skill / rel).is_file()


_HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)(?:\s+#+)?\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_A_ID_RE = re.compile(r"""<a\s+(?:name|id)=["']([^"']+)["']""")


def slugify(heading: str) -> str:
    """GitHub heading slug, mirroring slugify() in scripts/check-skill-links.mjs."""
    text = re.sub(r"`([^`]*)`", r"\1", heading)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.strip().lower()
    text = "".join(ch for ch in text if ch.isalnum() or ch in "_- ")
    return text.replace(" ", "-")


def anchors_of(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    counts: dict[str, int] = {}
    anchors: set[str] = set()
    in_fence = False
    for line in text.splitlines():
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEADING_RE.match(line)
        if not m:
            continue
        slug = slugify(m.group(1))
        seen = counts.get(slug, 0)
        counts[slug] = seen + 1
        anchors.add(slug if seen == 0 else f"{slug}-{seen}")
    anchors.update(a.lower() for a in _A_ID_RE.findall(text))
    return anchors


def scan(root: Path) -> tuple[list[tuple[str, int, str, str]], list[str]]:
    """Return (dead citations as (task file, line, citation, reason), orphan task folders)."""
    dead = []
    orphans: set[str] = set()
    tasks_root = root / "tests" / "tasks"
    for path in sorted(tasks_root.rglob("*")):
        if path.suffix not in (".yaml", ".yml") or not path.is_file():
            continue
        folder = path.relative_to(tasks_root).parts[0]
        task_skill = folder if skill_exists(root, folder) else None
        if task_skill is None and folder.startswith("uipath-"):
            orphans.add(folder)
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in _CITATION_RE.finditer(line):
                skill, rel = resolve(root, task_skill, m.group("prefix"), m.group("rest"))
                if skill is None:
                    continue
                cited = m.group(0)
                where = path.relative_to(root).as_posix()
                target = shipped_file(root, skill, rel)
                if target is None:
                    if not skill_exists(root, skill):
                        reason = f"no skill {skill} in skills/, preview/skills/ or classic/skills/"
                    elif classic_only(root, skill, rel):
                        reason = (
                            f"only classic/skills/{skill} has it; no eval catalog loads classic/, "
                            f"so the task's skill ships no such file"
                        )
                    else:
                        reason = f"not in skills/{skill} or preview/skills/{skill}"
                    dead.append((where, lineno, cited, reason))
                    continue
                anchor = m.group("anchor")
                if anchor and anchor.lower() not in anchors_of(target):
                    rel_target = target.relative_to(root).as_posix()
                    dead.append((where, lineno, cited, f"no heading in {rel_target} has the slug #{anchor}"))
    return dead, sorted(orphans)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repo root to scan (default: this repo)")
    args = parser.parse_args(argv)
    root = args.root.resolve()

    dead, orphans = scan(root)
    for folder in orphans:
        print(
            f"::warning file=tests/tasks/{folder}::tests/tasks/{folder}/ is named after a skill that no tree ships;"
            " its bare references/ citations are not checked"
        )
    if not dead:
        print("Every skill reference cited in tests/tasks resolves.")
        return 0

    for file, line, cited, reason in dead:
        print(f"::error file={file},line={line}::{cited}: {reason}")
        print(f"  {file}:{line}: {cited} ({reason})")
    print(
        f"\n{len(dead)} dead skill-reference citation(s). The cited doc or section was renamed or retired:"
        "\npoint the task at the doc that now states the rule, or name the rule instead of a file.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
