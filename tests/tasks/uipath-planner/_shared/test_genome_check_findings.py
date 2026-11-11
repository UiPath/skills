"""One test per finding check-genome.mjs reports: each breaks the worked example in one place and asserts the
message the author sees and the exit code the grader gets. The checker is Node; these tests drive it through
`node`, so the CI job needs Node >= 20 on the runner.

Run: pytest tests/tasks/uipath-planner/_shared/test_genome_check_findings.py -v
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SCRIPT = REPO / "skills" / "uipath-planner" / "scripts" / "check-genome.mjs"
FINGERPRINT = REPO / "skills" / "uipath-planner" / "scripts" / "sdd-fingerprint.mjs"


def node(*args):
    """Runs the checker; returns (exit code, stdout, stderr)."""
    done = subprocess.run(["node", str(SCRIPT), *map(str, args)], capture_output=True, text=True, encoding="utf-8", check=False)
    return done.returncode, done.stdout, done.stderr


def cli(*args):
    """Runs the checker; returns (exit code, stdout)."""
    return node(*args)[:2]


def node_call(function, *args):
    """Calls one of the checker's exported functions with JSON arguments; returns its JSON result."""
    script = (f"import * as c from {json.dumps(SCRIPT.as_uri())};"
              f"process.stdout.write(JSON.stringify(c.{function}(...{json.dumps(list(args))})));")
    done = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(done.stdout)


EXAMPLES = REPO / "tests" / "tasks" / "uipath-planner" / "_shared" / "genome-examples"  # known-good genomes, kept with the planner tests
COMPONENT = (EXAMPLES / "purchase-requisition-entry-genome.md").read_text(encoding="utf-8")
PROCESS = EXAMPLES / "invoice-processing-genome.md"
PROCESS_DIR = EXAMPLES / "invoice-processing-genome"


@pytest.fixture
def check(tmp_path):
    """check(text, ...) writes text as a genome, runs the checker, returns (exit code, stdout)."""

    def run(text, level="component", profile="core", extra=()):
        target = tmp_path / "sample-genome.md"
        target.write_text(text, encoding="utf-8")
        return cli(level, target, "--profile", profile, *extra)

    return run


@pytest.fixture
def process_tree(tmp_path):
    """A writable copy of the process example and its component genomes."""
    root = tmp_path / "tree"
    root.mkdir()
    shutil.copy(PROCESS, root / PROCESS.name)
    shutil.copytree(PROCESS_DIR, root / PROCESS_DIR.name)
    return root / PROCESS.name


@pytest.fixture
def check_process(process_tree):
    def run(extra=(), profile="core", transform=None):
        if transform:
            process_tree.write_text(transform(process_tree.read_text(encoding="utf-8")), encoding="utf-8")
        return cli("process", process_tree, "--profile", profile, *extra)

    return run


def section(text, heading, until):
    return text[text.index(heading):text.index(until)]


def split_row(text, prefix):
    return next(l for l in text.splitlines() if l.startswith(prefix))


def replace_row(text, prefix, new):
    return text.replace(split_row(text, prefix), new, 1)


# --- shared checks -------------------------------------------------------------------------------

def test_missing_preamble_comment_fails_core(check):
    text = re.sub(r"<!--.*?-->", "", COMPONENT, count=1, flags=re.S)
    rc, out = check(text)
    assert rc == 1
    assert "missing preamble comment 'UIPATH-AUTOMATION-GENOME: component'" in out


def test_preamble_not_written_exactly_fails_strict_only(check):
    text = COMPONENT.replace("UIPATH-AUTOMATION-GENOME: component", "uipath-automation-genome: component", 1)
    assert check(text)[0] == 0
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "preamble comment not written exactly" in out


def test_missing_blueprint_blockquote_fails_core(check):
    rc, out = check(COMPONENT.replace("automation blueprint", "automation spec"))
    assert rc == 1
    assert "missing blueprint blockquote" in out


def test_blueprint_blockquote_not_worded_as_the_template_fails_strict_only(check):
    text = COMPONENT.replace("This is a UiPath automation blueprint", "Here is a UiPath automation blueprint", 1)
    assert check(text)[0] == 0
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "blueprint blockquote not written as the template words it" in out


BUILDER = "uipath-genome"


def test_blockquote_must_name_the_builder(check):
    text = COMPONENT.replace(f"Build it with the **{BUILDER}** skill", "Build it with the build skill", 1)
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert f"blueprint blockquote does not name {BUILDER}" in out


@pytest.mark.parametrize("legacy", ["uipath-genome-builder"])
def test_blockquote_naming_a_legacy_builder_passes(check, legacy):
    text = COMPONENT.replace(f"Build it with the **{BUILDER}** skill", f"Build it with the **{legacy}** skill", 1)
    assert text != COMPONENT
    assert check(text, profile="strict")[0] == 0


def sdd_fingerprint(sdd):
    return subprocess.run(["node", str(FINGERPRINT), str(sdd)], capture_output=True, text=True, check=True).stdout.strip()


def designed_in(text, line):
    return re.sub(r"^(> \*\*This is a UiPath automation blueprint\.\*\*.*)$", lambda m: f"{m[1]}\n\n{line}", text, count=1, flags=re.M)


def pinned(tmp_path, fingerprint=None):
    """A genome text whose Designed in: line links x-sdd.md in tmp_path, pinned to fingerprint or the SDD's own."""
    sdd = tmp_path / "x-sdd.md"
    sdd.write_text("# SDD\n\n| **Status** | agreed |\n", encoding="utf-8")
    recorded = fingerprint or sdd_fingerprint(sdd)
    return designed_in(COMPONENT, f"> Designed in: [Design](x-sdd.md) · sdd-sha256 {recorded}")


def test_designed_in_line_without_fingerprint_fails_strict_only(check, tmp_path):
    text = designed_in(COMPONENT, "> Designed in: [Design](x-sdd.md)")
    assert text != COMPONENT
    assert check(text)[0] == 0
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "Designed in: line has no sdd-sha256 fingerprint" in out
    assert check(pinned(tmp_path), profile="strict")[0] == 0


def test_designed_in_fingerprint_that_no_longer_matches_fails_strict_only(check, tmp_path):
    text = pinned(tmp_path, "a" * 64)
    assert check(text)[0] == 0
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "Designed in: sdd-sha256 does not match x-sdd.md; the SDD changed since the genome was written" in out


def test_designed_in_sdd_that_cannot_be_read_fails_strict_only(check, tmp_path):
    text = pinned(tmp_path)
    (tmp_path / "x-sdd.md").unlink()
    assert check(text)[0] == 0
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "Designed in: x-sdd.md or a child SDD it lists cannot be read" in out


def test_designed_in_root_sdd_with_an_unreadable_child_fails_strict(check, tmp_path):
    (tmp_path / "x-sdd.md").write_text("| **Project SDD role** | root |\n\n[Child](child-sdd.md)\n", encoding="utf-8")
    (tmp_path / "child-sdd.md").write_text("# Child\n", encoding="utf-8")
    text = designed_in(COMPONENT, f"> Designed in: [Design](x-sdd.md) · sdd-sha256 {sdd_fingerprint(tmp_path / 'x-sdd.md')}")
    assert check(text, profile="strict")[0] == 0
    (tmp_path / "child-sdd.md").unlink()
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "Designed in: x-sdd.md or a child SDD it lists cannot be read" in out


def test_retired_skill_name_fails_core(check):
    rc, out = check(COMPONENT + "\nOlder drafts used uipath-coded-agents.\n")
    assert rc == 1
    assert "retired skill name 'uipath-coded-agents' present" in out


def test_unknown_skill_name_in_build_with_fails_core(check):
    rc, out = check(COMPONENT.replace("`uipath-rpa`", "`uipath-bogus`", 1))
    assert rc == 1
    assert "unknown skill name 'uipath-bogus' in Build With" in out


def test_too_few_criteria_for_the_complexity_fails_strict_only(check):
    kept = [l for l in COMPONENT.splitlines() if not re.match(r"(?:[5-9]|1\d)\. Given", l)]
    text = "\n".join(kept) + "\n"
    assert check(text)[0] == 0
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "acceptance criteria: 4 found, expected >= 5 for the stated complexity" in out


def test_too_few_criteria_fails_core(check):
    kept = [l for l in COMPONENT.splitlines() if not re.match(r"(?:[3-9]|1\d)\. Given", l)]
    rc, out = check("\n".join(kept) + "\n")
    assert rc == 1
    assert "acceptance criteria: 2 found, expected >= 3" in out


def test_generic_acceptance_criterion_fails_core(check):
    text = COMPONENT.replace("17. Given three robots", "17. The automation completes successfully.\n18. Given three robots", 1)
    rc, out = check(text)
    assert rc == 1
    assert "generic acceptance criterion: 17. The automation completes successfully." in out


# --- Transactional Shape -------------------------------------------------------------------------

def shape_of(text):
    return section(text, "## Transactional Shape", "## Acceptance Criteria")


def with_shape(text, new_shape):
    return text.replace(shape_of(text), "## Transactional Shape\n\n" + new_shape + "\n\n")


def test_verdict_in_the_shape_fails_strict_only(check):
    text = COMPONENT.replace("**Flows:**", "**Recommendation:** split it.\n\n**Flows:**", 1)
    assert check(text)[0] == 0
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "carries a verdict" in out


def test_shape_that_is_neither_stub_nor_flows_fails_core(check):
    rc, out = check(with_shape(COMPONENT, "The queue is described elsewhere."))
    assert rc == 1
    assert "Transactional Shape is neither the stub nor flows naming their unit of work" in out


def test_flows_line_is_strict_only(check):
    text = COMPONENT.replace(split_row(COMPONENT, "**Flows:**"), "", 1)
    assert check(text)[0] == 0
    rc, out = check(text, profile="strict")
    assert "Transactional Shape has no 'Flows:' line" in out


def test_template_placeholder_in_the_shape_fails_strict(check):
    text = COMPONENT.replace("**Flows:** Flow 1 — requisition row", "**Flows:** Flow 1 — {unit}", 1)
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "leaves a template placeholder unfilled: — {unit}" in out


def test_component_in_a_process_needs_role_and_pointer(check):
    text = COMPONENT.replace("# Genome: Purchase Requisition Entry", "# Genome: Purchase Requisition Entry\n\n> Part of: Procurement", 1)
    rc, out = check(text)
    assert rc == 1
    assert "a component inside a process has no 'Role:' line" in out
    rc, out = check(text, profile="strict")
    assert "does not point to the process genome's split options" in out


def test_unit_of_work_line_is_strict_only(check):
    text = COMPONENT.replace("**Unit of work:**", "Unit of work:", 1)
    assert check(text)[0] == 0
    rc, out = check(text, profile="strict")
    assert "no '**Unit of work:**' line" in out


def test_missing_split_options_fails_strict(check):
    text = re.sub(r"^\| one requisition (row|line) \|.*$", "", COMPONENT, flags=re.M)
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "no Split options table and no 'outside this genome' line" in out


def test_missing_as_is_table_fails_strict(check):
    rc, out = check(COMPONENT.replace("| Aspect | As-is |", "| Aspect | Today |", 1), profile="strict")
    assert rc == 1
    assert "no As-is table" in out


def test_outcomes_without_retry_and_stop_fail_strict(check):
    text = re.sub(r"retr\w*|consecutive", "again", COMPONENT, flags=re.I)
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "outcomes do not state the item retry and the consecutive-failure stop" in out


def test_unit_missing_an_option_fails_strict(check):
    text = re.sub(r"^\| one requisition line \| C \|.*$", "", COMPONENT, flags=re.M)
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "unit 'one requisition line' lacks option(s) ['C']" in out


def _decided(text: str, line: str) -> str:
    return re.sub(r"^(\*\*Evidence:\*\*.*)$", lambda m: m.group(1) + "\n" + line, text, count=1, flags=re.M)


def test_a_decided_split_lists_its_option_alone(check):
    text = re.sub(r"^\| one requisition line \| [AC] \|.*$", "", COMPONENT, flags=re.M)
    text = re.sub(r"^\| (?!one requisition line)[^|]+ \| [ABC] \|.*$", "", text, flags=re.M)
    text = _decided(text, "**Decided:** B, one requisition line — the SDD §10")
    rc, out = check(text, profile="strict")
    assert "lacks option(s)" not in out and "alternative units of work named" not in out, out


def test_a_decided_option_needs_its_row(check):
    text = re.sub(r"^\| one requisition line \| B \|.*$", "", COMPONENT, flags=re.M)
    text = _decided(text, "**Decided:** B, one requisition line — the request")
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "decided option B of 'one requisition line' has no Split options row" in out


def test_a_decided_line_names_its_option_first(check):
    rc, out = check(_decided(COMPONENT, "**Decided:** the SDD chose two projects"), profile="strict")
    assert rc == 1
    assert "the 'Decided:' line does not start with the option letter" in out


def _decided_b(line: str) -> str:
    """COMPONENT with the B row of 'one requisition line' alone and the given Decided: line."""
    text = re.sub(r"^\| one requisition line \| [AC] \|.*$", "", COMPONENT, flags=re.M)
    text = re.sub(r"^\| (?!one requisition line)[^|]+ \| [ABC] \|.*$", "", text, flags=re.M)
    return _decided(text, line)


def test_a_decided_b_line_with_a_project_chain_passes(check):
    rc, out = check(_decided_b("**Decided:** B, one requisition line — the SDD §10: ReqDispatcher → ReqPerformer → ReqReporter"), profile="strict")
    assert "'Decided:'" not in out, out


def test_a_decided_chain_on_option_a_fails_strict(check):
    text = re.sub(r"^\| one requisition line \| [BC] \|.*$", "", COMPONENT, flags=re.M)
    text = re.sub(r"^\| (?!one requisition line)[^|]+ \| [ABC] \|.*$", "", text, flags=re.M)
    text = _decided(text, "**Decided:** A, one requisition line — the SDD §10: ReqDispatcher → ReqPerformer")
    assert check(text)[0] == 0
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "the 'Decided:' line of option A names a project chain — only option B names its projects" in out


def test_a_decided_chain_naming_one_project_fails_strict(check):
    rc, out = check(_decided_b("**Decided:** B, one requisition line — the SDD §10: ReqDispatcher"), profile="strict")
    assert rc == 1
    assert "the 'Decided:' project chain 'ReqDispatcher' does not name two or more projects separated by ' → '" in out


def test_a_decided_source_quoting_the_request_is_no_chain(check):
    rc, out = check(_decided_b('**Decided:** B, one requisition line — the request: "retry lines individually"'), profile="strict")
    assert "project chain" not in out, out


def test_alternative_units_need_split_options_for_each(check):
    text = re.sub(r"^\| one requisition line \|.*$", "", COMPONENT, flags=re.M)
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "alternative units of work named but split options cover only one unit" in out


def test_split_columns_out_of_order_fail_strict(check):
    text = COMPONENT.replace("| Unit of work | Option | Requires | Changes against as-is |",
                             "| Unit of work | Option | Changes against as-is | Requires |", 1)
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "Split options columns are" in out


def test_split_table_without_requires_columns_fails_strict(check):
    text = COMPONENT.replace("| Unit of work | Option | Requires | Changes against as-is |",
                             "| Unit of work | Option | Notes | Effect |", 1)
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "Split options table has no Requires and Changes against as-is columns" in out


def test_empty_option_cell_fails_strict(check):
    text = replace_row(COMPONENT, "| one requisition row | B |", "| one requisition row | B |  | something |")
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "option B of 'one requisition row' has an empty Requires or Changes cell" in out


def test_ranking_the_options_fails_strict(check):
    text = replace_row(COMPONENT, "| one requisition row | B |", "| one requisition row | B | the recommended route | something |")
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "option B of 'one requisition row' ranks the options" in out


# --- --shape assertions --------------------------------------------------------------------------

def test_stub_expected_but_flows_found_fails(check):
    rc, out = check(COMPONENT, extra=["--shape", "stub"])
    assert rc == 1
    assert "expected the 'Not transactional' stub" in out


def test_flows_expected_but_stub_found_fails(check):
    rc, out = check(with_shape(COMPONENT, "Not transactional: one run, one report."), extra=["--shape", "transactional"])
    assert rc == 1
    assert "expected flow blocks, found the stub" in out


def test_flows_expected_but_none_found_fails(check):
    rc, out = check(with_shape(COMPONENT, "The queue is described elsewhere."), extra=["--shape", "transactional"])
    assert rc == 1
    assert "expected flows naming their unit of work, found none" in out


def test_flow_count_is_asserted(check):
    rc, out = check(COMPONENT, extra=["--shape", "transactional", "--flows", "2"])
    assert rc == 1
    assert "1 flow(s), expected 2" in out


def test_unit_token_must_appear_on_the_unit_of_work_line(check):
    rc, out = check(COMPONENT, extra=["--shape", "transactional", "--unit", "invoice"])
    assert rc == 1
    assert "no 'Unit of work' line names 'invoice'" in out


# --- Source Map step table -----------------------------------------------------------------------

STEP_ROW = "| {n} | `Step_{n}` ({pid}) | {data} | 0 | |"
HEADER = "| Step | Source objects | Data sets | Captures | Notes |\n|---|---|---|---|---|\n"


def step_count():
    return len(node_call("workflowSteps", COMPONENT))


def good_rows():
    return [STEP_ROW.format(n=k, pid=100 + k, data="none") for k in range(1, step_count() + 1)]


def extracted(rows=None, header=HEADER, with_table=True):
    rows = rows if rows is not None else good_rows()
    table = "\n\n### Steps\n\n" + header + "\n".join(rows) + "\n" if with_table else "\n"
    return COMPONENT.rstrip() + "\n\n## Source Map\n\n| Row | Source artifact | Notes |\n|---|---|---|\n| Dead code | none | |" + table


def test_source_map_without_steps_table_fails_core(check):
    rc, out = check(extracted(with_table=False))
    assert rc == 1
    assert "Source Map has no '### Steps' table" in out


def test_step_table_columns_are_strict_only(check):
    text = extracted(header="| Step | Objects | Data sets | Captures | Notes |\n|---|---|---|---|---|\n")
    assert check(text)[0] == 0
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "step table columns are" in out


def test_step_row_without_source_object_fails_strict(check):
    rows = good_rows()
    rows[0] = "| 1 |  | none | 0 | |"
    rc, out = check(extracted(rows), profile="strict")
    assert rc == 1
    assert "step table, step 1: no source object" in out


def test_step_row_with_prose_data_set_fails_strict(check):
    rows = good_rows()
    rows[0] = "| 1 | `Step_1` (101) | the order rows | 0 | |"
    rc, out = check(extracted(rows), profile="strict")
    assert rc == 1
    assert "is not a reference — move it to Notes" in out


def test_step_row_with_empty_data_sets_fails_strict(check):
    rows = good_rows()
    rows[0] = "| 1 | `Step_1` (101) |  | 0 | |"
    rc, out = check(extracted(rows), profile="strict")
    assert rc == 1
    assert "Data sets is empty — write 'none'" in out


def test_step_row_with_non_numeric_captures_fails_strict(check):
    rows = good_rows()
    rows[0] = "| 1 | `Step_1` (101) | none | several | |"
    rc, out = check(extracted(rows), profile="strict")
    assert rc == 1
    assert "Captures 'several' is not a count" in out


def test_step_row_naming_no_workflow_step_fails_core(check):
    rows = good_rows() + [STEP_ROW.format(n=99, pid=199, data="none")]
    rc, out = check(extracted(rows))
    assert rc == 1
    assert "row '99' names no Workflow step" in out


# --- component structure -------------------------------------------------------------------------

def test_build_with_after_workflow_fails_core(check):
    bw = section(COMPONENT, "## Build With", "## Platform Dependencies")
    text = COMPONENT.replace(bw, "")
    text = text.replace("## Business Rules", bw + "## Business Rules", 1)
    rc, out = check(text)
    assert rc == 1
    assert "Build With must precede Workflow" in out


def test_build_with_naming_no_skill_fails_core(check):
    bw = section(COMPONENT, "## Build With", "## Platform Dependencies")
    rc, out = check(COMPONENT.replace(bw, re.sub(r"uipath-[a-z-]+", "rpa", bw)))
    assert rc == 1
    assert "Build With names no skill" in out


def test_steps_without_bold_names_fail_strict_only(check):
    wf = section(COMPONENT, "## Workflow", "## Business Rules")
    text = COMPONENT.replace(wf, re.sub(r"^(\d+\. )\*\*([^*]*)\*\*", r"\1\2", wf, flags=re.M))
    assert check(text)[0] == 0
    rc, out = check(text, profile="strict")
    assert rc == 1
    assert "steps not all in the '1. **Step name**' form" in out


def test_empty_configuration_questions_fail_core(check):
    cq = section(COMPONENT, "## Configuration Questions", "## Workflow")
    rc, out = check(COMPONENT.replace(cq, "## Configuration Questions\n\n"))
    assert rc == 1
    assert "Configuration Questions section is empty" in out


def test_configuration_questions_without_list_or_stub_fail_strict_only(check):
    cq = section(COMPONENT, "## Configuration Questions", "## Workflow")
    text = COMPONENT.replace(cq, "## Configuration Questions\n\nAsk the owner.\n\n")
    assert check(text)[0] == 0
    rc, out = check(text, profile="strict")
    assert "neither a numbered list of questions nor the stub line" in out


def test_source_map_expectations_need_a_source_map(check):
    rc, out = check(COMPONENT, extra=["--source-map", "Dead"])
    assert rc == 1
    assert "missing or empty '## Source Map' section" in out


def test_source_map_token_must_be_mentioned(check):
    rc, out = check(extracted(), extra=["--source-map", "Dead", "Missing token"])
    assert rc == 1
    assert "Source Map does not mention 'Missing token'" in out
    assert "does not mention 'Dead'" not in out


def test_expected_token_missing_fails_core(check):
    rc, out = check(COMPONENT, extra=["--expect", "Coupa", "SAP S/4HANA"])
    assert rc == 1
    assert "expected token 'SAP S/4HANA' not found" in out
    assert "expected token 'Coupa' not found" not in out


# --- process level -------------------------------------------------------------------------------

def test_process_example_passes_core(check_process):
    rc, out = check_process()
    assert rc == 0
    assert out.startswith("OK (core)")


def test_components_after_process_map_fail_core(check_process):
    def swap(text):
        comp = section(text, "## Components", "## Process Map")
        return text.replace(comp, "").replace("## Handoffs", comp + "## Handoffs", 1)

    rc, out = check_process(transform=swap)
    assert rc == 1
    assert "Components must precede Process Map" in out


def test_components_table_needs_two_skill_rows(check_process):
    def one_row(text):
        return "\n".join(l for l in text.splitlines() if not re.match(r"\| [23] \|", l)) + "\n"

    rc, out = check_process(transform=one_row)
    assert rc == 1
    assert "Components table: fewer than 2 rows naming a skill" in out


def test_component_skill_expectation_fails_core(check_process):
    rc, out = check_process(extra=["--skills", "uipath-diagnostics"])
    assert rc == 1
    assert "Components table lacks skill 'uipath-diagnostics'" in out


def test_role_word_in_type_cell_fails_strict(check_process):
    rc, out = check_process(profile="strict", transform=lambda t: t.replace("| RPA process |", "| RPA performer |", 1))
    assert rc == 1
    assert "role word in the Type cell of 'Invoice Extraction and Matching'" in out


def test_components_table_with_no_links_fails_core(check_process):
    rc, out = check_process(transform=lambda t: re.sub(r"\[[^\]]*\]\([^)]*-genome\.md\)", "n/a", t))
    assert rc == 1
    assert "Components table links no component genome" in out


def test_linked_component_missing_on_disk_fails_core(process_tree, check_process):
    (process_tree.parent / PROCESS_DIR.name / "invoice-extraction-genome.md").unlink()
    rc, out = check_process()
    assert rc == 1
    assert "linked component genome missing on disk: invoice-processing-genome/invoice-extraction-genome.md" in out


def test_component_without_part_of_line_fails_strict_only(process_tree, check_process):
    target = process_tree.parent / PROCESS_DIR.name / "invoice-extraction-genome.md"
    target.write_text(re.sub(r"^> Part of:.*\n", "", target.read_text(encoding="utf-8"), flags=re.M), encoding="utf-8")
    assert check_process()[0] == 0
    rc, out = check_process(profile="strict")
    assert rc == 1
    assert "invoice-extraction-genome.md: component inside a process genome lacks the 'Part of:' line" in out


def test_handoffs_table_needs_two_rows(check_process):
    def one_row(text):
        return re.sub(r"(## Handoffs\n)(.*?)(?=^## )", r"\1\n| From | To |\n|---|---|\n| a | b |\n\n", text, flags=re.S | re.M)

    rc, out = check_process(transform=one_row)
    assert rc == 1
    assert "Handoffs table: 1 rows, expected >= 2" in out


def test_process_shape_and_tokens_are_asserted(check_process):
    rc, out = check_process(extra=["--shape", "transactional", "--expect", "Zebra"])
    assert rc == 1
    assert "expected flow blocks, found the stub" in out
    assert "expected token 'Zebra' not found" in out


# --- export cross-check --------------------------------------------------------------------------

def procs_for_rows():
    return [{"id": 100 + k, "name": f"Step_{k}", "calls": []} for k in range(1, step_count() + 1)]


def export_run(tmp_path, rows, procs, rsets):
    (tmp_path / "p.json").write_text(json.dumps(procs), encoding="utf-8")
    (tmp_path / "r.json").write_text(json.dumps(rsets), encoding="utf-8")
    target = tmp_path / "sample-genome.md"
    target.write_text(extracted(rows), encoding="utf-8")
    return cli("component", target, "--processes", tmp_path / "p.json", "--recordsets", tmp_path / "r.json")


def test_export_step_without_a_source_object_fails(tmp_path):
    rows = good_rows()
    rows[0] = "| 1 |  | none | 0 | |"
    rc, out = export_run(tmp_path, rows, procs_for_rows(), [])
    assert rc == 1
    assert "sample-genome.md step 1: no source object" in out


def test_export_data_set_problems_are_each_reported(tmp_path):
    rsets = [{"id": 1, "name": "Order_Rows"}, {"id": 2, "name": "Totals", "drives": False}, {"id": 3, "name": "Sheet::Lines"}]
    cases = {
        "`Order_Rows`": "data set `Order_Rows` has no id",
        "`Ghost` (77)": "data set `Ghost` (77) is no data set of the export",
        "`Step_2` (102)": "is no data set of the export — it is a process: move it to Source objects",
        "`Totals` (2)": "drives nothing",
        "`Other` (1)": "data set id 1 is `Order_Rows`, the row says `Other`",
    }
    for cell, expected in cases.items():
        rows = good_rows()
        rows[0] = f"| 1 | `Step_1` (101) | {cell} | 0 | |"
        rc, out = export_run(tmp_path, rows, procs_for_rows(), rsets)
        assert rc == 1, cell
        assert expected in out, cell
    rows = good_rows()
    rows[0] = "| 1 | `Step_1` (101) | `Lines` (3) | 0 | |"
    assert export_run(tmp_path, rows, procs_for_rows(), rsets)[0] == 0   # a sheet-qualified name matches its tail


def test_export_notes_a_library_workflow_nothing_calls(tmp_path):
    procs = procs_for_rows() + [{"id": 500, "name": "Shared_Util", "calls": []}]
    lib = tmp_path / "lib-genome.md"
    lib.write_text(extracted([f"| {k} | `Shared_Util` (500) | none | 0 | |" for k in range(1, step_count() + 1)]), encoding="utf-8")
    root = tmp_path / "root-genome.md"
    root.write_text(extracted(), encoding="utf-8")
    errors, notes = node_call("checkExport", [[str(root), False], [str(lib), True]], procs, [])
    assert errors == []
    assert any("`Shared_Util` (500) is a library workflow no built component calls" in n for n in notes)


def test_run_prints_the_export_notes(tmp_path, process_tree):
    # check-genome.py's test replaced check_export in-process; the Node checker runs as a command, so the note
    # comes from a real export: a component the Components table marks as a library, whose workflow no built
    # component calls.
    components = process_tree.parent / PROCESS_DIR.name
    root = components / "invoice-extraction-genome.md"
    lib = components / "exception-triage-agent-genome.md"
    procs = [{"id": 500, "name": "Shared_Util", "calls": []}]
    for genome in (root, lib):
        text = genome.read_text(encoding="utf-8")
        count = len(node_call("workflowSteps", text))
        if genome == root:
            procs += [{"id": 100 + k, "name": f"Step_{k}", "calls": []} for k in range(1, count + 1)]
            rows = [STEP_ROW.format(n=k, pid=100 + k, data="none") for k in range(1, count + 1)]
        else:
            rows = [f"| {k} | `Shared_Util` (500) | none | 0 | |" for k in range(1, count + 1)]
        genome.write_text(text.rstrip() + "\n\n## Source Map\n\n### Steps\n\n" + HEADER + "\n".join(rows) + "\n", encoding="utf-8")
    process_tree.write_text(process_tree.read_text(encoding="utf-8").replace("| Agent |", "| Agent library |", 1), encoding="utf-8")
    (tmp_path / "p.json").write_text(json.dumps(procs), encoding="utf-8")
    (tmp_path / "r.json").write_text("[]", encoding="utf-8")
    rc, out = cli("process", process_tree, "--processes", tmp_path / "p.json", "--recordsets", tmp_path / "r.json")
    assert rc == 0, out
    assert "NOTE: " in out
    assert "`Shared_Util` (500) is a library workflow no built component calls" in out


def test_export_over_a_process_genome_passes_when_no_component_has_a_step_table(tmp_path, process_tree):
    (tmp_path / "p.json").write_text("[]", encoding="utf-8")
    (tmp_path / "r.json").write_text("[]", encoding="utf-8")
    rc, out = cli("process", process_tree, "--processes", tmp_path / "p.json", "--recordsets", tmp_path / "r.json")
    assert rc == 0
    assert out.startswith("OK (core)")


# --- inventory files and arguments ---------------------------------------------------------------

def test_inventory_that_is_not_a_list_of_objects_fails_with_a_message(tmp_path):
    # check-genome.py exited through sys.exit(message), printing the FAIL line on stderr. The Node checker reports
    # every unreadable input as a FAIL line on stdout; the message and the exit code are unchanged.
    target = tmp_path / "sample-genome.md"
    target.write_text(COMPONENT, encoding="utf-8")
    (tmp_path / "p.json").write_text(json.dumps({"id": 1}), encoding="utf-8")
    (tmp_path / "r.json").write_text("[]", encoding="utf-8")
    rc, out = cli("component", target, "--processes", tmp_path / "p.json", "--recordsets", tmp_path / "r.json")
    assert rc == 1
    assert "FAIL: " in out
    assert "the process inventory is a list of objects with 'id' and 'name'" in out


def test_processes_and_recordsets_must_be_given_together(tmp_path):
    target = tmp_path / "sample-genome.md"
    target.write_text(COMPONENT, encoding="utf-8")
    (tmp_path / "p.json").write_text("[]", encoding="utf-8")
    rc, _, err = node("component", target, "--processes", tmp_path / "p.json")
    assert rc == 2
    assert "--processes and --recordsets go together" in err


def test_tokens_level_reports_file_count_and_missing_tokens(tmp_path):
    a = tmp_path / "a.md"
    a.write_text("alpha beta", encoding="utf-8")
    rc, out = cli("tokens", a, "--expect", "alpha", "beta")
    assert rc == 0
    assert "OK (tokens)" in out
    rc, out = cli("tokens", a, "--expect", "alpha", "gamma", "--files", "2")
    assert rc == 1
    assert "1 file(s) match, expected 2" in out
    assert "1/2 tokens found, expected >= 100%; missing: gamma" in out
    assert cli("tokens", a, "--expect", "alpha", "gamma", "--min", "0.5")[0] == 0
    rc, out = cli("tokens", tmp_path / "none.md", "--expect", "alpha")
    assert rc == 1
    assert "no file matches" in out


def test_script_runs_as_a_command(tmp_path):
    genome = tmp_path / "sample-genome.md"
    genome.write_text(COMPONENT, encoding="utf-8")
    rc, out = cli("component", genome, "--profile", "strict")
    assert rc == 0
    assert out.startswith("OK (strict)")
