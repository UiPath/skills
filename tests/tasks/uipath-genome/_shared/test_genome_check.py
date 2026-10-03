"""Unit tests for genome_check.py: the skill's own worked examples pass the strict profile,
a format slip fails strict but not core, and a broken contract fails core.

Run: pytest tests/tasks/uipath-genome/_shared/ -v
"""

import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import genome_check  # noqa: E402

EXAMPLES = HERE.parents[3] / "skills" / "uipath-genome" / "assets" / "examples"
COMPONENT_EXAMPLE = EXAMPLES / "purchase-requisition-entry-genome.md"  # transactional, two units of work
PROCESS_EXAMPLE = EXAMPLES / "invoice-processing-genome.md"


def run(tmp_path, text, level="component", profile="core", extra=()):
    target = tmp_path / "sample-genome.md"
    target.write_text(text, encoding="utf-8")
    return genome_check.main([level, str(target), "--profile", profile, *extra])


def level_of(path: Path) -> str:
    return re.search(r"UIPATH-AUTOMATION-GENOME: (\w+)", path.read_text(encoding="utf-8")).group(1)


@pytest.mark.parametrize("example", sorted(EXAMPLES.glob("*-genome.md")), ids=lambda p: p.name)
def test_every_example_passes_strict(example):
    assert genome_check.main([level_of(example), str(example), "--profile", "strict"]) == 0


def test_code_token_fails_strict_only(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8").replace("## Workflow\n", "## Workflow\n\nReads `in_Folder`.\n", 1)
    assert run(tmp_path, text, profile="core") == 0
    assert run(tmp_path, text, profile="strict") == 1


def test_unmarked_question_fails_strict_only(tmp_path):
    text = re.sub(r"\((setting|constant); default:", "(default:", COMPONENT_EXAMPLE.read_text(encoding="utf-8"), count=1)
    assert run(tmp_path, text, profile="core") == 0
    assert run(tmp_path, text, profile="strict") == 1


def test_domain_outcome_row_fails_strict_only(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8").replace("| Success |", "| Approved |", 1)
    assert run(tmp_path, text, profile="core") == 0
    assert run(tmp_path, text, profile="strict") == 1


def test_missing_section_fails_core(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8").replace("## Acceptance Criteria", "## Checks", 1)
    assert run(tmp_path, text, profile="core") == 1


def test_split_options_layout_is_strict_only(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8").replace("| Unit of work | Option |", "| Item | Choice |")
    assert run(tmp_path, text, profile="core") == 0
    assert run(tmp_path, text, profile="strict") == 1


def test_external_consumer_line_replaces_split_options(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8")
    ts_start = text.index("**Split options**")
    ts_end = text.index("**Evidence:**", ts_start)
    text = text[:ts_start] + "Split options: none — the consumer is outside this genome: the posting process.\n\n" + text[ts_end:]
    assert run(tmp_path, text, profile="core") == 0


def test_process_example_core_with_skills():
    assert genome_check.main(["process", str(PROCESS_EXAMPLE), "--skills", "uipath-rpa", "uipath-agents"]) == 0


def test_glob_needs_exactly_one_match(tmp_path, monkeypatch):
    (tmp_path / "a-genome.md").write_text("x", encoding="utf-8")
    (tmp_path / "b-genome.md").write_text("x", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert genome_check.main(["component", "*-genome.md"]) == 1
    assert genome_check.main(["tokens", "*-genome.md", "--files", "2", "--expect", "x"]) == 0


def test_shape_checks_advisory_moves_flow_findings_to_strict(tmp_path):
    text = re.sub(r"units? of work", "item", COMPONENT_EXAMPLE.read_text(encoding="utf-8"), flags=re.I)
    assert run(tmp_path, text, profile="core") == 1
    assert run(tmp_path, text, profile="core", extra=["--shape-checks", "advisory"]) == 0
    assert run(tmp_path, text, profile="strict", extra=["--shape-checks", "advisory"]) == 1


def test_plain_bullet_criteria_count(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8").replace("- [ ] ", "- ")
    assert run(tmp_path, text, profile="core") == 0
    assert run(tmp_path, text, profile="strict") == 0


def test_minimums_follow_the_genome_complexity(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8")
    workflow = text[text.index("## Workflow"):text.index("## Business Rules")]
    keep = []
    for line in workflow.splitlines():
        m = re.match(r"(\d+)\. ", line)
        if m and int(m.group(1)) > 3:
            break
        keep.append(line)
    three_steps = text.replace(workflow, "\n".join(keep) + "\n\n")
    medium = re.sub(r"(## Complexity\s+)\S+", r"\1medium", three_steps)
    assert run(tmp_path, medium, profile="core") == 0     # core gates only on the floor of 3 steps
    assert run(tmp_path, medium, profile="strict") == 1   # strict wants 5 steps for a medium genome
    workflow3 = medium[medium.index("## Workflow"):medium.index("## Business Rules")]
    two_steps = medium.replace(workflow3, workflow3.split("\n3. ")[0] + "\n\n")
    assert run(tmp_path, two_steps, profile="core") == 1  # below the floor


def test_part_of_line_is_strict_only(tmp_path):
    text = PROCESS_EXAMPLE.read_text(encoding="utf-8")
    assert genome_check.main(["process", str(PROCESS_EXAMPLE), "--skills", "uipath-rpa"]) == 0
    folder = PROCESS_EXAMPLE.with_suffix("")
    copy = tmp_path / folder.name
    copy.mkdir()
    for f in folder.glob("*-genome.md"):
        (copy / f.name).write_text(re.sub(r"^> Part of:.*\n", "", f.read_text(encoding="utf-8"), flags=re.M), encoding="utf-8")
    process = tmp_path / PROCESS_EXAMPLE.name
    process.write_text(text, encoding="utf-8")
    assert genome_check.main(["process", str(process), "--skills", "uipath-rpa"]) == 0
    assert genome_check.main(["process", str(process), "--profile", "strict", "--skills", "uipath-rpa"]) == 1


def test_format_variants_pass_core_fail_strict(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8")
    text = re.sub(r"^### Flow \d+.*$", "", text, flags=re.M)               # flow without its heading
    cq_start = text.index("## Configuration Questions")
    cq_end = text.index("## Workflow")
    table = "## Configuration Questions\n\n| # | Question | Default |\n|---|---|---|\n| 1 | Which queue? | PR_Requisitions |\n\n"
    text = text[:cq_start] + table + text[cq_end:]                          # questions as a table
    assert run(tmp_path, text, profile="core", extra=["--shape", "transactional", "--unit", "requisition"]) == 0
    assert run(tmp_path, text, profile="strict") == 1


def test_operate_skill_in_build_with_is_strict_only(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8")
    row = "| Queues and assets for the run | `uipath-platform` | Tenant resources the run reads |\n"
    text = text.replace("## Platform Dependencies", row + "\n## Platform Dependencies", 1)
    assert run(tmp_path, text, profile="core") == 0
    assert run(tmp_path, text, profile="strict") == 1
