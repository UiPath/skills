"""Permanent same-ground contract for uipath-maestro-flow eval tasks.

The temporary allowlists name pre-campaign debt. Each family batch removes its
own entries as the task contract becomes neutral; exact equality prevents stale
allowlist entries from hiding completed work.
"""

from __future__ import annotations

import re
from pathlib import Path

FLOW_TASKS = Path(__file__).resolve().parent.parent

V1_AUTHORING_ALLOWLIST = set()

SKILL_TELEMETRY_ALLOWLIST = set()

FORBIDDEN_PROMPT_ALLOWLIST = set()

# These born-neutral escalation tasks are outside the recipe-edit sweep. Their
# prompts already require the same-name solution and tell the agent to leave
# the live execution to the grader; preserving them is part of the campaign's
# explicit no-edit fence.
FORBIDDEN_PROMPT_EXCEPTIONS = {
    "e2e/escalation_jira_ticket/escalation_jira_ticket.yaml",
    "e2e/escalation_orchestrator_paths/escalation_orchestrator_paths.yaml",
    "e2e/escalation_slack_alert/escalation_slack_alert.yaml",
}

DEBUG_SOLUTION_ALLOWLIST = set()

# F1 freezes the #2557 task even though its prompt predates the exact phrase.
DEBUG_PROJECT_LAYOUT_EXCEPTIONS = {"single_node/coded_agent/coded_agent.yaml"}

UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)


def _block(text: str, key: str) -> str:
    match = re.search(rf"(?ms)^{re.escape(key)}:[^\n]*\n(.*?)(?=^[A-Za-z_][\w-]*:|\Z)", text)
    return match.group(0) if match else ""


def _criterion_blocks(text: str) -> list[tuple[str, str]]:
    section = _block(text, "success_criteria")
    return [
        (match.group(1), match.group(0))
        for match in re.finditer(
            r"(?ms)^  - type:\s*([^\s#]+).*?(?=^  - type:|^[A-Za-z_][\w-]*:|\Z)",
            section,
        )
    ]


def _prompt_text(text: str) -> str:
    return "\n".join((_block(text, "initial_prompt"), _block(text, "simulation")))


def _tagged_tasks() -> list[tuple[str, Path, str]]:
    tasks = []
    for path in sorted(FLOW_TASKS.rglob("*.yaml")):
        text = path.read_text()
        if "uipath-maestro-flow" in _block(text, "tags"):
            tasks.append((path.relative_to(FLOW_TASKS).as_posix(), path, text))
    return tasks


def _task_text(relative: str) -> str:
    return (FLOW_TASKS / relative).read_text()


def _referenced_python_files(task_path: Path, criterion: str) -> list[Path]:
    paths = []
    for token in re.findall(
        r"(?:\$TASK_DIR/|\$SKILLS_REPO_PATH/)?[A-Za-z0-9_./-]+\.py", criterion
    ):
        if token.startswith("$TASK_DIR/"):
            path = task_path.parent / token.removeprefix("$TASK_DIR/")
        elif token.startswith("$SKILLS_REPO_PATH/"):
            path = FLOW_TASKS.parents[2] / token.removeprefix("$SKILLS_REPO_PATH/")
        else:
            path = Path(token)
        if path.is_file():
            paths.append(path)
    return paths


def _is_debug_graded(task_path: Path, text: str) -> bool:
    for criterion_type, criterion in _criterion_blocks(text):
        if criterion_type == "command_not_executed":
            continue
        executable = "\n".join(
            line for line in criterion.splitlines() if not line.lstrip().startswith("#")
        )
        normalized = executable.lower().replace("\\\\", "\\")
        if "flow\\s+debug" in normalized or "flow debug" in normalized:
            return True
        if criterion_type != "run_command":
            continue
        for script in _referenced_python_files(task_path, criterion):
            source = script.read_text(errors="replace")
            if "run_debug(" in source or re.search(
                r'["\']flow["\']\s*,\s*["\']debug["\']', source
            ):
                return True
    return False


def _has_v1_authoring_grammar(criterion: str) -> bool:
    normalized = criterion.lower().replace("\\\\", "\\")
    markers = (
        "solution\\s+",
        "flow\\s+init",
        "flow\\s+node\\s+add",
        "flow\\s+node\\s+configure",
        "flow\\s+node\\s+remove",
        "flow\\s+node\\s+update",
        "flow\\s+registry",
    )
    return any(marker in normalized for marker in markers) or (
        "agent\\s+init" in normalized and "inline-in-flow" in normalized
    )


def test_every_tagged_task_has_an_explicit_task_id() -> None:
    missing = {
        relative
        for relative, _, text in _tagged_tasks()
        if not re.search(r"(?m)^task_id:\s*\S+", text)
    }
    assert missing == set()


def test_v1_only_authoring_commands_match_the_temporary_allowlist() -> None:
    offenders = set()
    for relative, _, text in _tagged_tasks():
        for criterion_type, criterion in _criterion_blocks(text):
            if criterion_type != "command_executed" or not _has_v1_authoring_grammar(
                criterion
            ):
                continue
            threshold = re.search(r"(?m)^\s+pass_threshold:\s*([0-9.]+)", criterion)
            if threshold is None or float(threshold.group(1)) > 0:
                offenders.add(relative)
    assert offenders == V1_AUTHORING_ALLOWLIST


def test_gating_skill_telemetry_matches_the_temporary_allowlist() -> None:
    offenders = set()
    for relative, _, text in _tagged_tasks():
        for criterion_type, criterion in _criterion_blocks(text):
            if criterion_type != "skill_triggered":
                continue
            threshold = re.search(r"(?m)^\s+pass_threshold:\s*([0-9.]+)", criterion)
            if threshold is None or float(threshold.group(1)) > 0:
                offenders.add(relative)
    assert offenders == SKILL_TELEMETRY_ALLOWLIST


def test_forbidden_prompt_phrases_match_the_temporary_allowlist() -> None:
    offenders = set()
    for relative, _, text in _tagged_tasks():
        prompt = " ".join(_prompt_text(text).lower().split())
        if re.search(r"do not [^.]*\bdebug\b", prompt) or UUID_PATTERN.search(prompt):
            offenders.add(relative)
    assert offenders == FORBIDDEN_PROMPT_ALLOWLIST | FORBIDDEN_PROMPT_EXCEPTIONS


def test_debug_graded_prompts_name_a_same_name_solution() -> None:
    offenders = set()
    for relative, path, text in _tagged_tasks():
        if not _is_debug_graded(path, text):
            continue
        prompt = " ".join(_prompt_text(text).lower().split())
        if not re.search(r"\b(?:in|inside) a solution of the same name\b", prompt):
            offenders.add(relative)
    assert offenders == DEBUG_SOLUTION_ALLOWLIST | DEBUG_PROJECT_LAYOUT_EXCEPTIONS


def test_external_graders_use_package_qualified_shared_imports() -> None:
    shared_modules = {
        path.stem for path in (FLOW_TASKS / "_shared").glob("*.py")
    }
    offenders = set()
    for path in FLOW_TASKS.rglob("*.py"):
        relative = path.relative_to(FLOW_TASKS)
        if relative.parts[0] == "_shared":
            continue
        for module in re.findall(
            r"(?m)^(?:from|import)\s+([A-Za-z_][A-Za-z0-9_]*)", path.read_text()
        ):
            if module in shared_modules:
                offenders.add(relative.as_posix())
    assert offenders == set()


def test_reconfigure_prompt_requires_a_tenant_wide_connection_inventory() -> None:
    prompt = _prompt_text(
        _task_text("bindings/reconfigure_different_connection.yaml")
    ).lower()

    assert "tenant-wide" in prompt
    assert "every folder" in prompt


def test_multiselect_prompt_names_slack_as_the_required_connector() -> None:
    prompt = _prompt_text(_task_text("connector_features/multiselect.yaml")).lower()

    assert "slack group direct message" in prompt
