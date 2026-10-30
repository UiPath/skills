"""Unit tests for the skill's scripts/check-genome.mjs, the checker the genome tasks grade with:
the known-good genomes kept with the tests pass the strict profile, a format slip fails strict but not core,
and a broken contract fails core. The checker is Node (users need no Python); these tests drive it
through `node`, so the CI job needs Node >= 20 on the runner.

Run: pytest tests/tasks/uipath-planner/_shared/test_genome_check.py -v
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
CHECKER = REPO / "skills" / "uipath-planner" / "scripts" / "check-genome.mjs"


def node(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["node", str(CHECKER), *args], capture_output=True, text=True, encoding="utf-8")


def node_call(function: str, *args):
    """Call one of the checker's exported functions with JSON arguments; returns its JSON result."""
    script = (f"import * as c from {json.dumps(CHECKER.as_uri())};"
              f"process.stdout.write(JSON.stringify(c.{function}(...{json.dumps(list(args))})));")
    r = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(r.stdout)


class genome_check:
    """The checker's surface as these tests use it."""

    @staticmethod
    def main(argv: list[str]) -> int:
        r = node(*argv)
        sys.stdout.write(r.stdout)
        return r.returncode

    @staticmethod
    def context(path: Path) -> dict:
        return node_call("context", str(path))

    @staticmethod
    def check_export(genomes, processes, recordsets):
        errors, notes = node_call("checkExport", [[str(p), lib] for p, lib in genomes], processes, recordsets)
        return errors, notes

    @staticmethod
    def workflow_steps(text: str) -> list[str]:
        return node_call("workflowSteps", text)

    @staticmethod
    def skills() -> dict:
        return json.loads(node("skills").stdout)


EXAMPLES = HERE / "genome-examples"  # known-good genomes, kept with the tests; the skill ships the templates only
MAPPING_GUIDE = REPO / "skills" / "uipath-planner" / "references" / "skill-mapping-guide.md"
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
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8").replace("uipath-genome-builder", "the build skills")
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


def test_a_value_pattern_is_no_template_placeholder(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8")
    at = text.index("**Unit of work:**")
    pattern = text[:at] + "Items are tagged `{kind};{region}` and {region}/{unit}, referenced `{item}_{date}` and INV-{n}.\n\n" + text[at:]
    assert run(tmp_path, pattern, profile="strict") == 0
    for leftover in ("Items are tagged {status, tags, fields, output}.", "Each item is recorded as done with {result}."):
        assert run(tmp_path, text[:at] + leftover + "\n\n" + text[at:], profile="strict") == 1


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
    names = genome_check.skills()
    listed = set(names["build"]) | set(names["operate"]) | {"uipath-genome-builder"}
    assert shipped - listed == set(), "add each new skill to VALID_SKILLS or OPERATE_SKILLS"
    assert listed - shipped == set(), "a listed skill no longer ships"


def test_mapping_guide_names_every_build_skill():
    guide = MAPPING_GUIDE.read_text(encoding="utf-8")
    assert {s for s in genome_check.skills()["build"] if f"`{s}`" not in guide} == set()


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


def extracted(steps: int, rows: list[str] | None = None, framework: str | None = "UiPath — Studio 26.0") -> str:
    """The component example as an extracted genome: its Source Map with a step table of one row per step."""
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8")
    rows = rows if rows is not None else [STEP_ROW.format(n=n, pid=100 + n, data="none") for n in range(1, steps + 1)]
    table = "| Step | Source objects | Data sets | Captures | Notes |\n|---|---|---|---|---|\n" + "\n".join(rows)
    framework_row = f"| Source framework | {framework} | |\n" if framework else ""
    return (text.rstrip() + "\n\n## Source Map\n\n| Row | Source artifact | Notes |\n|---|---|---|\n" + framework_row
            + "| Dead code | none | |\n\n### Steps\n\n" + table + "\n")


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


def test_preamble_of_a_genome_written_before_the_split_still_passes(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8").replace("uipath-genome-builder", "uipath-genome")
    assert run(tmp_path, text, profile="strict") == 0


# context: the facts the read plans branch on, read once from the file

SALESFORCE_EXAMPLE = EXAMPLES / "salesforce-accounts-and-contacts-genome.md"


@pytest.mark.parametrize("path, level, mode, transactional", [
    (PROCESS_EXAMPLE, "process", "build", False),
    (COMPONENT_EXAMPLE, "component", "build", True),
    (SALESFORCE_EXAMPLE, "component", "refactor", False),
])
def test_context_reads_level_mode_and_shape_from_the_file(path, level, mode, transactional):
    ctx = genome_check.context(path)
    assert (ctx["level"], ctx["build_mode"], ctx["transactional"]) == (level, mode, transactional)
    assert ctx["check"]["ok"], ctx["check"]["errors"]


def test_context_lists_a_process_genomes_components():
    assert len(genome_check.context(PROCESS_EXAMPLE)["components"]) == 3


def test_context_fingerprint_changes_with_any_byte(tmp_path):
    genome = tmp_path / "x-genome.md"
    genome.write_text(COMPONENT_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    before = genome_check.context(genome)["sha256"]
    genome.write_text(genome.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert genome_check.context(genome)["sha256"] != before


def test_context_without_marker_fails_the_check(tmp_path):
    genome = tmp_path / "x-genome.md"
    genome.write_text("# not a genome\n", encoding="utf-8")
    ctx = genome_check.context(genome)
    assert ctx["level"] is None and not ctx["check"]["ok"]


def test_context_cli_prints_json(capsys):
    assert genome_check.main(["context", str(COMPONENT_EXAMPLE)]) == 0
    assert json.loads(capsys.readouterr().out)["level"] == "component"


# context: extracted, framework and shape facts

def test_context_extracted_needs_a_source_map_table(tmp_path):
    genome = tmp_path / "x-genome.md"
    genome.write_text(COMPONENT_EXAMPLE.read_text(encoding="utf-8").rstrip() + "\n\n## Source Map\n\n*Extraction only.*\n", encoding="utf-8")
    assert genome_check.context(genome)["extracted"] is False
    genome.write_text(extracted(example_steps(), framework=None), encoding="utf-8")
    ctx = genome_check.context(genome)
    assert ctx["extracted"] is True and ctx["source_framework"] is None and ctx["build_mode"] == "build"


def test_context_reads_the_framework_row_of_a_process_source_map(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8").rstrip()
    genome = tmp_path / "x-genome.md"
    genome.write_text(text + "\n\n## Source Map\n\n| Component | Source artifact | Notes |\n|---|---|---|\n| Source framework | Blue Prism — 7.1 | |\n", encoding="utf-8")
    assert (genome_check.context(genome)["source_framework"], genome_check.context(genome)["build_mode"]) == ("Blue Prism", "migration")


def test_context_build_mode_is_refactor_when_the_framework_names_uipath(tmp_path):
    text = SALESFORCE_EXAMPLE.read_text(encoding="utf-8").replace("| Source framework | UiPath —", "| Source framework | Studio (UiPath) —", 1)
    genome = tmp_path / "x-genome.md"
    genome.write_text(text, encoding="utf-8")
    assert genome_check.context(genome)["build_mode"] == "refactor"


def test_context_transactional_is_null_without_level_or_section(tmp_path):
    genome = tmp_path / "x-genome.md"
    genome.write_text("# not a genome\n", encoding="utf-8")
    assert genome_check.context(genome)["transactional"] is None
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8")
    start, end = text.index("## Transactional Shape"), text.index("## Acceptance Criteria")
    genome.write_text(text[:start] + text[end:], encoding="utf-8")
    assert genome_check.context(genome)["transactional"] is None


def test_source_map_without_framework_row_fails_strict_only(tmp_path):
    n = example_steps()
    assert run(tmp_path, extracted(n, framework=None), profile="core") == 0
    assert run(tmp_path, extracted(n, framework=None), profile="strict") == 1
    assert run(tmp_path, extracted(n), profile="strict") == 0


# command line

def test_flag_equals_value_is_accepted(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8")
    assert run(tmp_path, text, extra=["--shape=transactional", "--unit=requisition", "--flows=1"]) == 0
    target = tmp_path / "sample-genome.md"
    assert genome_check.main(["component", str(target), "--profile=strict"]) == 0


def test_help_prints_usage_and_exits_zero():
    for flag in ("-h", "--help"):
        r = node(flag)
        assert r.returncode == 0 and "usage:" in r.stdout


@pytest.mark.parametrize("bad", [["--flows", "1.5"], ["--flows=x"], ["--min-steps", "3x"], ["--min", "abc"], ["--files", ""]])
def test_numbers_are_validated_strictly(bad):
    assert node("component", str(COMPONENT_EXAMPLE), *bad).returncode == 2


def test_missing_inventory_is_a_fail_line(tmp_path):
    r = node("component", str(COMPONENT_EXAMPLE), "--processes", str(tmp_path / "no.json"), "--recordsets", str(tmp_path / "no2.json"))
    assert r.returncode == 1 and r.stdout.startswith("FAIL:") and "Error" not in r.stderr


def test_invalid_utf8_is_a_fail_line(tmp_path):
    genome = tmp_path / "x-genome.md"
    genome.write_bytes(COMPONENT_EXAMPLE.read_bytes() + b"\n\xff\xfe broken\n")
    for argv in (["component", str(genome)], ["context", str(genome)]):
        r = node(*argv)
        assert r.returncode == 1 and "FAIL:" in r.stdout and "not valid UTF-8" in r.stdout and "Error" not in r.stderr


def test_legacy_builder_name_is_a_known_skill(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8").replace("## Platform Dependencies", "Built through `uipath-genome`.\n\n## Platform Dependencies", 1)
    target = tmp_path / "sample-genome.md"
    target.write_text(text, encoding="utf-8")
    assert "unknown skill name 'uipath-genome'" not in node("component", str(target)).stdout
    assert run(tmp_path, text, profile="core") == 0


def test_duplicate_heading_fails_strict_only(tmp_path):
    text = COMPONENT_EXAMPLE.read_text(encoding="utf-8").rstrip() + "\n\n## Tags\n\nagain\n"
    assert run(tmp_path, text, profile="core") == 0
    assert run(tmp_path, text, profile="strict") == 1


def test_duplicate_component_link_fails_strict_only(tmp_path):
    folder = PROCESS_EXAMPLE.with_suffix("")
    copy = tmp_path / folder.name
    copy.mkdir()
    for f in folder.glob("*-genome.md"):
        (copy / f.name).write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    text = PROCESS_EXAMPLE.read_text(encoding="utf-8")
    rows = [l for l in text.splitlines() if l.startswith("| 1 ") and "-genome.md)" in l]
    assert rows, "the process example's first component row"
    process = tmp_path / PROCESS_EXAMPLE.name
    process.write_text(text.replace(rows[0], rows[0] + "\n" + rows[0].replace("| 1 ", "| 9 ", 1), 1), encoding="utf-8")
    assert genome_check.main(["process", str(process), "--skills", "uipath-rpa"]) == 0
    assert genome_check.main(["process", str(process), "--profile", "strict"]) == 1
