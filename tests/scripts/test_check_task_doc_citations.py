"""
Behaviour tests for scripts/check-task-doc-citations.py, the gate that fails
when a task YAML under tests/tasks/ cites a skill reference file (or a section of
one) that no eval catalog ships (UiPath/skills#4531, #4533 review).

Each test builds a throwaway repo layout in tmp_path and runs the script on it.
The last test runs it on this repo, so the corpus itself stays clean.

Run from repo root:
    pytest tests/scripts/test_check_task_doc_citations.py
"""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check-task-doc-citations.py"

_spec = importlib.util.spec_from_file_location("check_task_doc_citations", SCRIPT)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


def put(root: Path, rel: str, text: str = "x\n") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def task(root: Path, rel: str, body: str) -> None:
    put(root, f"tests/tasks/{rel}", f"task_id: t\ndescription: >\n  {body}\n")


def dead(root: Path) -> list[str]:
    return [f"{f}:{line}:{cited}" for f, line, cited, _ in gate.scan(root)[0]]


def test_resolving_citation_passes(tmp_path, capsys):
    put(tmp_path, "skills/uipath-x/references/placeholder-tasks.md")
    task(tmp_path, "uipath-x/a.yaml", "write a placeholder per references/placeholder-tasks.md.")
    assert gate.main(["--root", str(tmp_path)]) == 0
    assert "resolves" in capsys.readouterr().out


def test_renamed_reference_fails(tmp_path, capsys):
    # The #4531 shape: the doc was renamed, the prompt kept the old name.
    put(tmp_path, "skills/uipath-x/references/placeholder-tasks.md")
    task(tmp_path, "uipath-x/hitl/q.yaml", "write a skeleton task per references/skeleton-tasks.md:")
    assert gate.main(["--root", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "::error file=tests/tasks/uipath-x/hitl/q.yaml,line=3::references/skeleton-tasks.md" in out


def test_skills_and_preview_count(tmp_path):
    put(tmp_path, "skills/uipath-x/references/s.md")
    put(tmp_path, "preview/skills/uipath-x/references/p.md")
    task(tmp_path, "uipath-x/a.yaml", "see references/s.md and references/p.md")
    assert dead(tmp_path) == []


def test_classic_only_doc_fails(tmp_path, capsys):
    # The #4533 review shape: v1 moved to classic/, the default package (v2)
    # has no such file, and no eval catalog loads classic/.
    put(tmp_path, "skills/uipath-x/SKILL.md")
    put(tmp_path, "classic/skills/uipath-x/references/brownfield.md")
    task(tmp_path, "uipath-x/hitl/q.yaml", "edit it per references/brownfield.md")
    assert gate.main(["--root", str(tmp_path)]) == 1
    assert "only classic/skills/uipath-x has it" in capsys.readouterr().out


def test_anchor_must_match_a_heading(tmp_path):
    put(
        tmp_path,
        "skills/uipath-x/references/q.md",
        "# Query\n\n## Filter body\n\n```md\n## Not a heading\n```\n\n### `default` encoding \u2014 EVERY type\n"
        '\n<a id="Legacy-Anchor"></a>\n',
    )
    task(
        tmp_path,
        "uipath-x/a.yaml",
        "see references/q.md#filter-body, references/q.md#default-encoding--every-type,"
        " references/q.md#legacy-anchor, references/q.md#not-a-heading and references/q.md#filter-bodies",
    )
    assert dead(tmp_path) == [
        "tests/tasks/uipath-x/a.yaml:3:references/q.md#not-a-heading",
        "tests/tasks/uipath-x/a.yaml:3:references/q.md#filter-bodies",
    ]


def test_orphan_uipath_task_folder_warns(tmp_path, capsys):
    task(tmp_path, "uipath-gone/a.yaml", "see references/x.md")
    assert gate.main(["--root", str(tmp_path)]) == 0
    assert "::warning file=tests/tasks/uipath-gone::" in capsys.readouterr().out


def test_leading_folders_stay_inside_the_skill(tmp_path):
    put(tmp_path, "skills/uipath-x/references/evaluate.md")
    task(tmp_path, "uipath-x/a.yaml", "rule in `evaluate/references/upload-safety.md` and references/evaluate.md")
    assert dead(tmp_path) == ["tests/tasks/uipath-x/a.yaml:3:evaluate/references/upload-safety.md"]


def test_cross_skill_citation_resolves_in_the_named_skill(tmp_path):
    put(tmp_path, "skills/uipath-x/SKILL.md")
    put(tmp_path, "skills/uipath-y/references/orchestrator/run-jobs.md")
    task(
        tmp_path,
        "uipath-x/a.yaml",
        "see skills/uipath-y/references/orchestrator/run-jobs.md and skills/uipath-y/references/gone.md",
    )
    assert dead(tmp_path) == ["tests/tasks/uipath-x/a.yaml:3:skills/uipath-y/references/gone.md"]


def test_cross_skill_citation_to_a_non_uipath_name(tmp_path):
    # Any skill folder name resolves as a skill, not as a path inside the task's skill.
    put(tmp_path, "skills/uipath-x/SKILL.md")
    put(tmp_path, "skills/helper/references/h.md")
    task(tmp_path, "uipath-x/a.yaml", "see skills/helper/references/h.md and skills/nope/references/n.md")
    assert dead(tmp_path) == ["tests/tasks/uipath-x/a.yaml:3:skills/nope/references/n.md"]


def test_non_skill_folder_checks_only_named_skills(tmp_path):
    put(tmp_path, "skills/uipath-y/references/real.md")
    task(
        tmp_path,
        "activation/a.yaml",
        "references/anything.md, skills/uipath-y/references/real.md, skills/uipath-y/references/gone.md",
    )
    assert dead(tmp_path) == ["tests/tasks/activation/a.yaml:3:skills/uipath-y/references/gone.md"]


def test_placeholders_and_globs_are_not_citations(tmp_path):
    put(tmp_path, "skills/uipath-x/SKILL.md")
    task(tmp_path, "uipath-x/a.yaml", "references/plugins/<name>/impl.md or references/*.md")
    assert dead(tmp_path) == []


def test_this_repo_is_clean():
    assert dead(REPO_ROOT) == []
