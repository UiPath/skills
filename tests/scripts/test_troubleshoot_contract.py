"""
Regression tests for scripts/check-troubleshoot-tasks.py.
Each test reproduces a false negative surfaced by code review: a scenario that
violated the contract while the gate reported OK.

Run from repo root:
    pytest tests/scripts/test_troubleshoot_contract.py
"""

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "scripts" / "check-troubleshoot-tasks.py"
GENERATOR = REPO_ROOT / "tests" / "tasks" / "uipath-troubleshoot" / "_shared" / "scripts" / "generate_scenario.py"
CONTRACT = REPO_ROOT / "tests" / "contracts" / "troubleshoot-scenario-contract.yaml"
CANONICAL = (
    REPO_ROOT
    / "tests"
    / "tasks"
    / "uipath-troubleshoot"
    / "activity-packages"
    / "word-replace-text-silent-no-substitution"
    / "task.yaml"
)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load("check_troubleshoot_tasks", CHECKER)


def _run(*args):
    """Run the checker as a subprocess; returns (exit_code, stdout)."""
    proc = subprocess.run(
        [sys.executable, str(CHECKER), *[str(a) for a in args]],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=REPO_ROOT,
    )
    return proc.returncode, proc.stdout


def _scenario(tmp_path, mutate=lambda text: text):
    """A canonical scenario, optionally mutated, in its own directory."""
    directory = tmp_path / "scenario"
    directory.mkdir()
    (directory / "task.yaml").write_text(
        mutate(CANONICAL.read_text(encoding="utf-8")), encoding="utf-8"
    )
    return directory


def test_suite_and_generator_satisfy_the_contract():
    code, out = _run()
    assert code == 0, out
    # The template must be part of the scan, not silently skipped.
    assert "the generator template" in out


def test_canonical_scenario_passes(tmp_path):
    code, out = _run(_scenario(tmp_path))
    assert code == 0, out


# --- High: only the first criterion of a type was validated -----------------

SECOND_JUDGE = """
  - type: llm_judge
    description: "second judge"
    weight: 9.0
    pass_threshold: 0.99
    include_reference: false
    include_agent_output: true
    prompt: |
      whatever
"""


def test_duplicate_judge_carrying_violations_is_caught(tmp_path):
    """A second llm_judge without include_dialog is graded by the harness too."""
    directory = _scenario(tmp_path, lambda t: t.replace("simulation:", SECOND_JUDGE.lstrip("\n") + "\nsimulation:", 1))
    code, out = _run(directory)
    assert code == 1
    assert "appears 2 times" in out
    assert "include_dialog" in out


def test_duplicate_skill_triggered_with_wrong_skill_is_caught(tmp_path):
    dupe = (
        '  - type: skill_triggered\n'
        '    description: "dupe"\n'
        '    skill_name: "uipath-platform"\n'
        '    expected_skill: "uipath-platform"\n'
        '    weight: 1.0\n\n'
    )
    directory = _scenario(tmp_path, lambda t: t.replace("simulation:", dupe + "simulation:", 1))
    code, out = _run(directory)
    assert code == 1
    assert "expected_skill" in out


def test_skill_name_drift_is_caught(tmp_path):
    """The harness detects engagement of skill_name and expects it iff
    skill_name == expected_skill. Drifting skill_name alone flips the criterion
    into a negative row that passes without the troubleshoot skill running."""
    directory = _scenario(
        tmp_path,
        lambda t: t.replace('skill_name: "uipath-troubleshoot"', 'skill_name: "uipath-platform"', 1),
    )
    code, out = _run(directory)
    assert code == 1
    assert "skill_triggered.skill_name" in out


def test_non_mapping_criterion_entry_is_caught(tmp_path):
    """A scalar entry must be a violation, not silently dropped from every rule."""
    directory = _scenario(
        tmp_path, lambda t: t.replace("success_criteria:\n", "success_criteria:\n  - malformed-scalar\n", 1)
    )
    code, out = _run(directory)
    assert code == 1
    assert "not a mapping" in out


def test_boolean_simulation_max_turns_is_caught(tmp_path):
    """bool is an int subclass: YAML `max_turns: true` must not pass as 1."""
    directory = _scenario(tmp_path, lambda t: t.replace("\n  max_turns: 6\n", "\n  max_turns: true\n", 1))
    code, out = _run(directory)
    assert code == 1
    assert "simulation.max_turns" in out


def test_unvetted_criterion_type_is_caught(tmp_path):
    extra = '  - type: run_command\n    description: "x"\n    command: "true"\n    weight: 1.0\n\n'
    directory = _scenario(tmp_path, lambda t: t.replace("success_criteria:\n", "success_criteria:\n" + extra, 1))
    code, out = _run(directory)
    assert code == 1
    assert "run_command" in out and "not allowed" in out


def test_allowed_extra_criterion_type_passes(tmp_path):
    """command_not_executed is whitelisted; the whitelist must not be a blanket ban."""
    extra = (
        '  - type: command_not_executed\n'
        '    description: "no mutation"\n'
        '    command_pattern: "uip or jobs start"\n'
        '    weight: 1.0\n\n'
    )
    directory = _scenario(tmp_path, lambda t: t.replace("success_criteria:\n", "success_criteria:\n" + extra, 1))
    code, out = _run(directory)
    assert code == 0, out


# --- High: forbidden keys were checked by truthiness ------------------------

@pytest.mark.parametrize("value", ["[]", "null", "[RESOLUTION.md]"])
def test_forbidden_judge_key_is_caught_whatever_its_value(tmp_path, value):
    directory = _scenario(
        tmp_path,
        lambda t: t.replace("    include_dialog: true", f"    include_dialog: true\n    files: {value}", 1),
    )
    code, out = _run(directory)
    assert code == 1
    assert "`llm_judge.files` is forbidden" in out


# --- High: an unreachable generator template failed open -------------------

def _fake_repo(tmp_path, generator_source):
    """A minimal repo tree the checker can scan, with its own generator copy."""
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    (root / "tests" / "contracts").mkdir(parents=True)
    generator_dir = root / "tests" / "tasks" / "uipath-troubleshoot" / "_shared" / "scripts"
    generator_dir.mkdir(parents=True)
    scenario_dir = root / "tests" / "tasks" / "uipath-troubleshoot" / "x"
    scenario_dir.mkdir(parents=True)

    shutil.copy(CHECKER, root / "scripts" / CHECKER.name)
    shutil.copy(CONTRACT, root / "tests" / "contracts" / CONTRACT.name)
    shutil.copy(CANONICAL, scenario_dir / "task.yaml")
    (generator_dir / "generate_scenario.py").write_text(generator_source, encoding="utf-8")
    return root


def _run_in(root):
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / CHECKER.name)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=root,
    )
    return proc.returncode, proc.stdout


# Each mutation also drops include_dialog, a real violation the gate must report
# even while the template itself is what broke.
GENERATOR_SOURCE = GENERATOR.read_text(encoding="utf-8")
NO_FLAG = GENERATOR_SOURCE.replace("    include_dialog: true\n", "")

TEMPLATE_MUTATIONS = {
    "f_string_prefix": NO_FLAG.replace('TASK_YAML_TEMPLATE = """', 'TASK_YAML_TEMPLATE = f"""', 1),
    "rebound_name": NO_FLAG.replace('TASK_YAML_TEMPLATE = """', '_HEAD = """', 1) + "\nTASK_YAML_TEMPLATE = _HEAD\n",
    "concatenation": NO_FLAG.replace('TASK_YAML_TEMPLATE = """', 'TASK_YAML_TEMPLATE = "" + """', 1),
    "renamed_symbol": NO_FLAG.replace("TASK_YAML_TEMPLATE =", "TASK_TEMPLATE_YAML =", 1),
    "unknown_placeholder": NO_FLAG.replace("task_id: skill-troubleshoot-{slug}", "task_id: skill-troubleshoot-{slug}-{brandnew}", 1),
}


@pytest.mark.parametrize("name", sorted(TEMPLATE_MUTATIONS))
def test_unusable_generator_template_fails_loudly(tmp_path, name):
    """Silently skipping the template would disable half the gate."""
    code, out = _run_in(_fake_repo(tmp_path, TEMPLATE_MUTATIONS[name]))
    assert code == 1, out
    assert "the generator template" not in out.splitlines()[0]


def test_missing_generator_file_fails_loudly(tmp_path):
    root = _fake_repo(tmp_path, GENERATOR_SOURCE)
    (root / "tests" / "tasks" / "uipath-troubleshoot" / "_shared" / "scripts" / "generate_scenario.py").unlink()
    code, out = _run_in(root)
    assert code == 1
    assert "generator template file not found" in out


def test_intact_fake_repo_passes(tmp_path):
    """Guards the mutations above: the unmutated copy must pass."""
    code, out = _run_in(_fake_repo(tmp_path, GENERATOR_SOURCE))
    assert code == 0, out


# --- Medium: an empty scan reported OK ------------------------------------

def test_empty_scan_fails(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    code, out = _run(empty)
    assert code == 1
    assert "scanning nothing" in out


def test_nonexistent_path_fails(tmp_path):
    code, out = _run(tmp_path / "does-not-exist")
    assert code == 1
    assert "scanning nothing" in out


# --- Medium: violations were annotated on unrelated (sometimes valid) lines -

def _annotated_lines(out):
    """{message: line_number} for every GitHub annotation in `out`."""
    found = {}
    for line in out.splitlines():
        if not line.startswith("::error"):
            continue
        head, _, message = line.partition("::")[2].partition("::")
        number = 0
        if ",line=" in head:
            number = int(head.split(",line=")[1])
        found[message] = number
    return found


def test_simulation_max_turns_is_not_blamed_on_run_limits(tmp_path):
    """The hint says `max_turns: 6`; pointing it at run_limits would break the
    task's turn budget if an author followed the annotation."""
    directory = _scenario(tmp_path, lambda t: t.replace("\n  max_turns: 6\n", "\n", 1))
    code, out = _run(directory)
    assert code == 1
    lines = (directory / "task.yaml").read_text(encoding="utf-8").splitlines()
    for message, number in _annotated_lines(out).items():
        if "simulation.max_turns" in message:
            assert number == 0 or "run_limits" not in lines[number - 1]
            assert number == 0 or "max_turns: 60" not in lines[number - 1]


def test_judge_weight_is_annotated_on_the_judge_weight_line(tmp_path):
    directory = _scenario(tmp_path, lambda t: t.replace("    weight: 3.0", "    weight: 5.0", 1))
    code, out = _run(directory)
    assert code == 1
    lines = (directory / "task.yaml").read_text(encoding="utf-8").splitlines()
    for message, number in _annotated_lines(out).items():
        if "llm_judge.weight" in message:
            assert number > 0
            assert lines[number - 1].strip() == "weight: 5.0"


# --- Low: a scalar tags value satisfied the membership test by substring ----

def test_scalar_tags_is_caught(tmp_path):
    directory = _scenario(
        tmp_path,
        lambda t: t.replace(
            "tags: [uipath-troubleshoot, rpa, e2e, mode:diagnose]",
            'tags: "uipath-troubleshoot-not-a-list"',
            1,
        ),
    )
    code, out = _run(directory)
    assert code == 1
    assert "`tags` must be a list" in out


# --- pre_run: the mock-store seal must be present and must abort on failure -

def _drop_pre_run(text):
    """Remove the whole pre_run block (header through the next blank line)."""
    lines = text.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.startswith("pre_run:"))
    end = start + 1
    while end < len(lines) and lines[end].strip():
        end += 1
    return "".join(lines[:start] + lines[end:])


def test_missing_pre_run_is_caught(tmp_path):
    """An unsealed scenario leaks the recorded uip outputs to the agent."""
    directory = _scenario(tmp_path, _drop_pre_run)
    code, out = _run(directory)
    assert code == 1
    assert "seal-mock-store" in out


def test_pre_run_without_the_seal_command_is_caught(tmp_path):
    directory = _scenario(
        tmp_path, lambda t: t.replace('- command: "python m/seal"', '- command: "echo noop"', 1)
    )
    code, out = _run(directory)
    assert code == 1
    assert "seal-mock-store" in out


@pytest.mark.parametrize("mutation", [
    lambda t: t.replace("\n    fail_on_error: true", "", 1),
    lambda t: t.replace("    fail_on_error: true", "    fail_on_error: false", 1),
    # A YAML string, not a bool: the harness's truthiness for it is
    # unspecified, so the checker's `is not True` must reject it.
    lambda t: t.replace("    fail_on_error: true", '    fail_on_error: "true"', 1),
])
def test_seal_not_aborting_on_failure_is_caught(tmp_path, mutation):
    """fail_on_error false, missing, or string-typed lets a failed seal restore
    the leak silently."""
    directory = _scenario(tmp_path, mutation)
    code, out = _run(directory)
    assert code == 1
    assert "fail_on_error" in out


SEAL_ITEM = '  - command: "python m/seal"\n    timeout: 60\n    fail_on_error: true'


@pytest.mark.parametrize("replacement", [
    # pre_run as a mapping instead of a list of steps.
    '  command: "python m/seal"\n  timeout: 60\n  fail_on_error: true',
    # The step as a plain string entry instead of a mapping.
    '  - "python m/seal"',
])
def test_malformed_pre_run_shape_is_caught(tmp_path, replacement):
    """A shape the harness would not run as the seal step must read as missing."""
    directory = _scenario(tmp_path, lambda t: t.replace(SEAL_ITEM, replacement, 1))
    code, out = _run(directory)
    assert code == 1
    assert "seal-mock-store" in out


def test_duplicate_seal_step_carrying_violations_is_caught(tmp_path):
    """Every copy of the seal step is validated, not just the first."""
    dupe = '  - command: "python m/seal"\n    timeout: 60\n    fail_on_error: false\n'
    directory = _scenario(tmp_path, lambda t: t.replace("\nreference:", "\n" + dupe + "\nreference:", 1))
    code, out = _run(directory)
    assert code == 1
    assert "fail_on_error" in out


def test_extra_pre_run_step_passes(tmp_path):
    """The contract requires the seal; it does not ban other staging steps."""
    extra = '  - command: "echo warmup"\n    timeout: 10\n'
    directory = _scenario(tmp_path, lambda t: t.replace("\nreference:", "\n" + extra + "\nreference:", 1))
    code, out = _run(directory)
    assert code == 0, out


def test_generator_template_without_the_seal_is_caught(tmp_path):
    """The template half of the gate: a generator that stops emitting the seal
    step must fail, annotated on the generator file. The TEMPLATE_MUTATIONS
    above only exercise render-machinery failures; this one renders fine and
    violates the contract."""
    source = GENERATOR_SOURCE.replace('- command: "python m/seal"', '- command: "echo noop"', 1)
    code, out = _run_in(_fake_repo(tmp_path, source))
    assert code == 1
    assert "seal-mock-store" in out
    assert "generate_scenario.py" in out


# --- Unit-level: pattern ordering in the annotation locator -----------------

def test_line_of_prefers_the_first_pattern_that_matches():
    text = "task_id: x\nreference:\n  file: RESOLUTION.md\n"
    assert checker._line_of(text, [r"^reference:", r"^task_id:"]) == 2
    assert checker._line_of(text, [r"^nothing-here:", r"^task_id:"]) == 1
    assert checker._line_of(text, r"^absent:") == 0


def test_line_of_section_restricts_the_search():
    text = "run_limits:\n  max_turns: 60\nsimulation:\n  max_turns: 6\n"
    assert checker._line_of(text, r"max_turns:") == 2
    assert checker._line_of(text, r"max_turns:", section=r"^simulation:") == 4
