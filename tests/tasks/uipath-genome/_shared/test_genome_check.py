"""Unit tests for the skill's scripts/check-genome.py, the checker the genome tasks grade with:
the skill's own worked examples pass the strict profile, a format slip fails strict but not core,
and a broken contract fails core.

Run: pytest tests/tasks/uipath-genome/_shared/ -v
"""

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
_spec = importlib.util.spec_from_file_location("genome_check", REPO / "skills" / "uipath-genome" / "scripts" / "check-genome.py")
genome_check = importlib.util.module_from_spec(_spec)
sys.modules["genome_check"] = genome_check
_bytecode, sys.dont_write_bytecode = sys.dont_write_bytecode, True  # no __pycache__ inside the shipped skill
_spec.loader.exec_module(genome_check)
sys.dont_write_bytecode = _bytecode

EXAMPLES = REPO / "skills" / "uipath-genome" / "assets" / "examples"
MAPPING_GUIDE = REPO / "skills" / "uipath-genome" / "references" / "skill-mapping-guide.md"
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


def test_preamble_without_uipath_genome_fails_strict_only(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8").replace("uipath-genome", "the build skills")
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


def test_bullet_criteria_count_but_fail_strict(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8")
    start, end = text.index("## Acceptance Criteria"), text.index("## Complexity")
    bullets = re.sub(r"^\d+\. ", "- [ ] ", text[start:end], flags=re.M)
    assert run(tmp_path, text[:start] + bullets + text[end:], profile="core") == 0
    assert run(tmp_path, text[:start] + bullets + text[end:], profile="strict") == 1


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


def test_numbered_criteria_count(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8")
    start, end = text.index("## Acceptance Criteria"), text.index("## Complexity")
    numbered = "## Acceptance Criteria\n\n" + "".join(f"{i}. Given input {i}, the automation records outcome {i}.\n" for i in range(1, 6)) + "\n"
    assert run(tmp_path, text[:start] + numbered + text[end:], profile="core") == 0


def test_unit_is_read_from_the_unit_of_work_line_only(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8")
    unit = re.search(r"^\*\*Unit of work:\*\*.*$", text, re.M).group(0)
    shape = ["--shape", "transactional", "--unit"]
    assert run(tmp_path, text, profile="core", extra=[*shape, "requisition"]) == 0
    whole_workbook = text.replace(unit, "**Unit of work:** the whole workbook, worked in one throw.", 1)
    whole_workbook = whole_workbook.replace("**Alternative units of work:**", "**Alternative units of work:** a sheet row;", 1)
    assert run(tmp_path, whole_workbook, profile="core", extra=[*shape, "row"]) == 1


def test_skill_lists_cover_the_shipped_skills():
    shipped = {p.name for root in (REPO / "skills", REPO / "preview" / "skills") if root.is_dir()
               for p in root.iterdir() if (p / "SKILL.md").is_file()}
    listed = genome_check.VALID_SKILLS | genome_check.OPERATE_SKILLS | {"uipath-genome"}
    assert shipped - listed == set(), "add each new skill to VALID_SKILLS or OPERATE_SKILLS"
    assert listed - shipped == set(), "a listed skill no longer ships"


def test_mapping_guide_names_every_build_skill():
    guide = MAPPING_GUIDE.read_text(encoding="utf-8")
    assert {s for s in genome_check.VALID_SKILLS if f"`{s}`" not in guide} == set()


def test_checker_reads_rules_not_lookalikes(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8")
    cq = text.index("## Configuration Questions")
    pointer = text[:cq] + text[cq:].replace("\n1. ", "\n1. The shared mailbox: process Configuration Question 2.\n2. ", 1)
    assert run(tmp_path, pointer, profile="strict") == 0                    # a pointer to the process genome's question
    login = text.replace("## Workflow\n", "## Workflow\n\nSigns in on the login_page form.\n", 1)
    assert run(tmp_path, login, profile="strict") == 0                      # 'in_' counts only at a word start


def test_test_cases_are_the_depth_of_a_test_component(tmp_path, capsys):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8")
    workflow = text[text.index("## Workflow"):text.index("## Business Rules")]
    cases = "## Workflow\n\n1. **Test case: Key one requisition**\n   a. Key it.\n2. **Test case: Reject a closed cost centre**\n   a. Reject it.\n\n"
    run(tmp_path, text.replace(workflow, cases), profile="strict")
    assert "numbered steps" not in capsys.readouterr().out                  # the step minimums do not apply to test cases
    ts = text[text.index("## Transactional Shape"):text.index("## Acceptance Criteria")]
    two = "## Workflow\n\n1. **Sign in**\n   a. Sign in.\n2. **Sign out**\n   a. Sign out.\n\n"
    library = text.replace(workflow, two).replace(ts, "## Transactional Shape\n\nNot transactional: a library.\n\n")
    run(tmp_path, library, profile="strict")
    assert "numbered steps" not in capsys.readouterr().out                  # nor to a library's public workflows


def test_split_option_cell_holds_its_letter_only(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8").replace("| one requisition row | A |", "| one requisition row | A — one process, both roles |", 1)
    assert run(tmp_path, text, profile="core") == 0
    assert run(tmp_path, text, profile="strict") == 1


STEP_ROW = "| {n} | `Step_{n}` ({pid}, lines 1–9) | {data} | 0 | |"


def extracted(steps: int, rows: list[str] | None = None) -> str:
    """The component example as an extracted genome: its Source Map with a step table of one row per step."""
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8")
    rows = rows if rows is not None else [STEP_ROW.format(n=n, pid=100 + n, data="none") for n in range(1, steps + 1)]
    table = "| Step | Source objects | Data sets | Captures | Notes |\n|---|---|---|---|---|\n" + "\n".join(rows)
    return text.rstrip() + "\n\n## Source Map\n\n| Row | Source artifact | Notes |\n|---|---|---|\n| Dead code | none | |\n\n### Steps\n\n" + table + "\n"


def example_steps() -> int:
    return len(genome_check.workflow_steps(COMPONENT_EXAMPLE.read_text(encoding="utf-8")))


def test_extracted_genome_needs_one_step_row_per_step(tmp_path):
    n = example_steps()
    assert run(tmp_path, extracted(n), profile="strict") == 0
    no_table = extracted(n).split("### Steps")[0]
    assert run(tmp_path, no_table, profile="core") == 1
    rows = [STEP_ROW.format(n=k, pid=100 + k, data="none") for k in range(1, n)]  # last step missing
    assert run(tmp_path, extracted(n, rows), profile="core") == 1
    rows = [STEP_ROW.format(n=k, pid=100 + k, data="none").replace(f"| {k} |", f"| Step {k} |", 1) for k in range(1, n + 1)]
    assert run(tmp_path, extracted(n, rows), profile="core") == 1


def test_step_table_cells_hold_references_only(tmp_path):
    n = example_steps()
    rows = [STEP_ROW.format(n=k, pid=100 + k, data="none") for k in range(1, n + 1)]
    rows[0] = "| 1 | `Step_1` (101); called by `Main` (100) at line 4 | none | 0 | |"
    assert run(tmp_path, extracted(n, rows), profile="core") == 0
    assert run(tmp_path, extracted(n, rows), profile="strict") == 1
    rows[0] = STEP_ROW.format(n=1, pid=101, data="")
    assert run(tmp_path, extracted(n, rows), profile="strict") == 1


def test_export_check_resolves_every_reference(tmp_path):
    n = example_steps()
    procs = [{"id": 100 + k, "name": f"Step_{k}", "calls": []} for k in range(1, n + 1)]
    rsets = [{"id": 1207, "name": "Order_Rows"}, {"id": 1208, "name": "report.csv", "drives": False}]
    (tmp_path / "p.json").write_text(json.dumps(procs), encoding="utf-8")
    (tmp_path / "r.json").write_text(json.dumps(rsets), encoding="utf-8")
    inventory = ["--processes", str(tmp_path / "p.json"), "--recordsets", str(tmp_path / "r.json")]
    rows = [STEP_ROW.format(n=k, pid=100 + k, data="`Order_Rows` (1207)" if k == 1 else "none") for k in range(1, n + 1)]
    assert run(tmp_path, extracted(n, rows), extra=inventory) == 0
    for bad in ("`Order_Rows` (1207)",            # a data set cited as a source object
                "`Step_2` (101)",                 # id 101 is Step_1
                "`Step_1`"):                      # no id
        broken = [rows[0].replace("`Step_1` (101, lines 1–9)", bad)] + rows[1:]
        assert run(tmp_path, extracted(n, broken), extra=inventory) == 1, bad
    provenance = [rows[0].replace("`Order_Rows` (1207)", "`report.csv` (1208)")] + rows[1:]
    assert run(tmp_path, extracted(n, provenance), extra=inventory) == 1


def test_export_check_finds_the_wrong_copy(tmp_path):
    procs = [{"id": 1, "name": "Root", "calls": [{"calleeId": 2}]}, {"id": 2, "name": "Sign_in"}, {"id": 3, "name": "Sign_in"}]
    table = "### Steps\n\n| Step | Source objects | Data sets | Captures | Notes |\n|---|---|---|---|---|\n"
    root, lib = tmp_path / "root-genome.md", tmp_path / "lib-genome.md"
    root.write_text("## Source Map\n\n" + table + "| 1 | `Root` (1) | none | 0 | |\n", encoding="utf-8")
    lib.write_text("## Source Map\n\n" + table + "| 1 | `Sign_in` (3) | none | 0 | |\n", encoding="utf-8")
    errors, notes = genome_check.check_export([(root, False), (lib, True)], procs, [])
    assert len(errors) == 1 and "copy they run is 2" in errors[0]
    lib.write_text("## Source Map\n\n" + table + "| 1 | `Sign_in` (2) | none | 0 | |\n", encoding="utf-8")
    assert genome_check.check_export([(root, False), (lib, True)], procs, []) == ([], [])


def test_heading_case_and_wording_variants_pass_core(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8")
    text = text.replace("## Target Applications", "## Target Applications and Systems", 1)
    text = text.replace("## Error Handling", "## error handling", 1)
    text = text.replace("This is a UiPath automation blueprint", "this is a UiPath Automation Blueprint", 1)
    text = re.sub(r"`(uipath-rpa)`", r"\1", text)
    assert run(tmp_path, text, profile="core") == 0
    assert run(tmp_path, text, profile="strict") == 1
