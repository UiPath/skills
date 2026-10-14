"""Permanent same-ground contract for uipath-maestro-flow eval tasks.

The temporary allowlists name pre-campaign debt plus tasks that landed on
`main` after the alignment sweep and have not been aligned yet. Each family
batch removes its own entries as the task contract becomes neutral; exact
equality prevents stale allowlist entries from hiding completed work.
"""

from __future__ import annotations

import re
from pathlib import Path

FLOW_TASKS = Path(__file__).resolve().parent.parent

# Post-sweep upstream arrivals, carried as-is until their own alignment pass:
# - evaluate/child_simulation (#2965, 2026-09-02) gates on `uip solution init`
#   and `uip maestro flow init` telemetry.
# - ixp/e2e_03_project_creation_handoff (#2809, 2026-09-02) gates on two
#   skill_triggered criteria and tells the agent not to run `flow debug`.
V1_AUTHORING_ALLOWLIST = {
    "evaluate/child_simulation/child_simulation_crud.yaml",
}

SKILL_TELEMETRY_ALLOWLIST = {
    "ixp/e2e_03_project_creation_handoff/e2e_03_project_creation_handoff.yaml",
}

FORBIDDEN_PROMPT_ALLOWLIST = {
    "ixp/e2e_03_project_creation_handoff/e2e_03_project_creation_handoff.yaml",
}

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

# Commands whose JOB the other route does differently or internally, so a
# `command_executed` on one of them measures which route ran rather than what
# the run produced. See `test_route_specific_command_telemetry_is_weightless`
# for the evidence behind each family, and for what is deliberately NOT here.
ROUTE_SPECIFIC_COMMANDS = (
    # v1 mutates the graph a node at a time; the SDK loop writes `.flow.ts`.
    r"flow node \(?(add|configure|remove|update)|flow edge ",
    # v1 scaffolds the inline agent's sidecar with the CLI; the SDK's
    # `conversationalAgent()` / `agent()` emit `agent.json` themselves.
    r"agent (init|refresh) (?=.*(inline-in-flow|--conversational))",
    # v1 walks the tenant by hand; `registry prepare` picks the connection,
    # pages the collection and writes `bindings.json` in one call.
    r"is connections list|is resources run list|is triggers \(?(objects|describe)",
    # v1 refreshes the node manifest before searching it.
    r"flow registry \(?pull",
)

# The two billing lookups name only a "Data Service entity", which since #3041
# denotes two node families. Their prompts pin the connector so the graded
# structure is deterministic; the sibling dispute-resolution task pins it in the
# same way. Native Data Fabric authoring is covered by its own task, not these.
CONNECTOR_PINNED_LOOKUPS = {
    "multi_node/billing_invoice_lookup/billing_invoice_lookup.yaml",
    "multi_node/billing_discrepancy_detector/billing_discrepancy_detector.yaml",
}
CONNECTOR_PIN = (
    "on the data service `query-entity-records` activity, "
    "not the native data fabric nodes"
)

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


_REFERENCE_BLOCK = re.compile(r"^reference:\s*\n\s*directory:\s*(\S+)", re.M)


def _referenced_python_files(task_path: Path, criterion: str) -> list[Path]:
    paths = []
    reference_root: Path | None = None
    for token in re.findall(
        r"(?:\$TASK_DIR/|\$REFERENCE_DIR/|\$SKILLS_REPO_PATH/)?[A-Za-z0-9_./-]+\.py", criterion
    ):
        if token.startswith("$TASK_DIR/"):
            path = task_path.parent / token.removeprefix("$TASK_DIR/")
        elif token.startswith("$REFERENCE_DIR/"):
            if reference_root is None:
                match = _REFERENCE_BLOCK.search(task_path.read_text())
                if not match:
                    continue
                reference_root = task_path.parent / match.group(1)
            path = reference_root / token.removeprefix("$REFERENCE_DIR/")
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


def _command_pattern(criterion: str) -> str:
    """A `command_pattern` with its regex escaping flattened to plain words.

    The corpus spells the same command several ways — `\\s+` in a single-quoted
    scalar, `\\\\s+` in a double-quoted one — so matching families against the
    raw text would miss half of them.
    """
    match = re.search(r"(?m)^\s+command_pattern:\s*(.*)$", criterion)
    if match is None:
        return ""
    pattern = match.group(1).replace("\\\\", "\\")
    pattern = re.sub(r"\\s\+?", " ", pattern)
    return re.sub(r"\s+", " ", pattern.replace("\\", ""))


def test_route_specific_command_telemetry_is_weightless() -> None:
    """A criterion that grades WHICH ROUTE ran must not move the score.

    THE GAP THIS EXISTS FOR. `pass_threshold: 0` was read as "this criterion is
    advisory", and the sibling test above enforces only that. It is half the
    idiom; coder_eval's own field docs carry the other half: "weight=0 excludes
    from the score but NOT from the pass/fail gate ... To make a criterion truly
    non-gating, also set pass_threshold=0." So `pass_threshold: 0` with
    `weight: 1.5` never fails a task and always moves its score.

    That only matters where the command itself is route-specific. In the
    2026-09-23 same-ground run those criteria scored 1.0 for v1 and 0.0 for v2,
    dragging tasks that passed every graded check down with them —
    `datafabric_integration_create_get` returned SUCCESS at 0.55 on three
    `flow node add` advisories weighing 5.0 against two graded criteria at 3.0.

    WHAT IS NOT IN `ROUTE_SPECIFIC_COMMANDS`, and why. An earlier revision of
    this test keyed on criterion TYPE — every non-gating `command_executed` —
    and that was wrong. It swept in `solution init`, `flow init`,
    `flow validate`, `flow debug` and `flow eval ...`, which both routes run on
    the same artifact and which the run shows both routes passing (31 of the 54
    observed criteria were BOTH PASS). Zeroing those removes real, satisfiable
    signal and buys no neutrality. `flow registry get|search|list` is out for
    the same measured reason: the SDK arm passes those in the IxP tasks, so the
    registry is not a v1-only surface — only `pull` is listed, as the refresh
    step the SDK loop has no need of.

    A criterion is therefore in scope only when its COMMAND has no counterpart
    in the other route. Where an arm then fails one of the survivors, that is a
    finding about the arm, which is the point.

    `stop_early` criteria are exempt: there `weight` is load-bearing for the
    pass-stop floor, not just for the score (see `ixp/routing.yaml`, whose
    sentinel says so).
    """
    offenders = set()
    for relative, _, text in _tagged_tasks():
        for criterion_type, criterion in _criterion_blocks(text):
            if criterion_type != "command_executed":
                continue
            threshold = re.search(r"(?m)^\s+pass_threshold:\s*([0-9.]+)", criterion)
            if threshold is None or float(threshold.group(1)) > 0:
                continue
            if re.search(r"(?m)^\s+stop_early:", criterion):
                continue
            pattern = _command_pattern(criterion)
            if not any(re.search(family, pattern) for family in ROUTE_SPECIFIC_COMMANDS):
                continue
            weight = re.search(r"(?m)^\s+weight:\s*([0-9.]+)", criterion)
            # An absent `weight` defaults to 1.0, so silence is not compliance.
            if weight is None or float(weight.group(1)) != 0:
                offenders.add(relative)
    assert offenders == set()


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


def test_billing_lookup_prompts_pin_the_data_service_connector() -> None:
    offenders = {
        relative
        for relative in CONNECTOR_PINNED_LOOKUPS
        if CONNECTOR_PIN not in " ".join(_prompt_text(_task_text(relative)).lower().split())
    }
    assert offenders == set()


def test_external_graders_use_package_qualified_shared_imports() -> None:
    """Outside `_shared/`, no grader may resolve a same-named `_shared/` module
    via a bare/ambiguous import. `_setup/` is exempt by design: it is staged
    into the agent's sandbox (never reaches `_shared/`, which is not staged),
    and a `_setup/<name>.py` legitimately shares a stem with a `_shared/<name>.py`
    when pre_run/post_run tooling and its grader need their own separate copies
    of the same helper (see jira_is.py: `_setup/jira_is.py` per Jira task,
    `_shared/jira_is.py` for the graders — intentionally two copies, never one
    importing the other)."""
    shared_modules = {
        path.stem for path in (FLOW_TASKS / "_shared").glob("*.py")
    }
    offenders = set()
    for path in FLOW_TASKS.rglob("*.py"):
        relative = path.relative_to(FLOW_TASKS)
        if relative.parts[0] == "_shared" or "_setup" in relative.parts:
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


def test_paginated_lookup_accepts_both_supported_resolution_routes() -> None:
    text = _task_text("connector_features/paginated_reference_lookup.yaml")
    blocks = [block for kind, block in _criterion_blocks(text) if kind == "command_executed"]
    manual_block, paged_block = blocks[:2]
    patterns = re.findall(r"(?m)^\s+command_pattern:\s*'([^']+)'", text)
    manual_pattern, paged_pattern = map(re.compile, patterns[:2])

    page_one = 'bash -lc "uip is resources run list \\"uipath-salesforce-slack\\" \\"conversations\\" --connection-id id"'
    page_two = page_one[:-1] + ' --query nextPage=token"'
    sdk_command = (
        "npx flow-sdk registry prepare uipath-salesforce-slack "
        "send-message-to-channel --resolve channel:name=simple"
    )
    # The CLI wraps the same resolver as `uip maestro registry prepare`
    # (UiPath/cli#3969) — top-level `maestro registry`, not `maestro flow registry`.
    uip_command = "uip maestro " + sdk_command[len("npx flow-sdk "):]

    # The v1 route is telemetry the SDK arm never produces: advisory, but it
    # still asks for the loop (page 1 alone is not pagination).
    assert "min_count: 2" in manual_block and "pass_threshold: 0.0" in manual_block
    assert manual_pattern.search(page_one) and manual_pattern.search(page_two)
    assert not manual_pattern.search(sdk_command)

    # This is advisory because a command cut off by a turn timeout has unknown
    # status. It still records only successful page-2 work; the artifact check
    # gates the resolved channel id.
    assert "require_success: true" in paged_block and "pass_threshold: 0.0" in paged_block
    assert paged_pattern.search(page_two)
    assert paged_pattern.search(sdk_command)
    assert paged_pattern.search(uip_command) and not manual_pattern.search(uip_command)
    assert not paged_pattern.search(page_one)
    assert not paged_pattern.search("uip maestro flow validate --resolve channel:name=simple")
    assert not paged_pattern.search("echo nextPage=token")
