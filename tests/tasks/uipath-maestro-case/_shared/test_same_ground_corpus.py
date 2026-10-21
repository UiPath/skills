"""Permanent cross-loop grading contracts for Maestro Case eval tasks."""

from __future__ import annotations

import re
from pathlib import Path


CASE_TASKS = Path(__file__).resolve().parent.parent


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


def _tagged_tasks() -> list[tuple[str, str]]:
    tasks = []
    for path in sorted(CASE_TASKS.rglob("*.yaml")):
        text = path.read_text()
        if "uipath-maestro-case" in _block(text, "tags"):
            tasks.append((path.relative_to(CASE_TASKS).as_posix(), text))
    return tasks


def test_skill_telemetry_is_advisory_across_the_case_corpus() -> None:
    offenders = set()
    for relative, text in _tagged_tasks():
        for criterion_type, criterion in _criterion_blocks(text):
            if criterion_type != "skill_triggered":
                continue
            threshold = re.search(r"(?m)^\s+pass_threshold:\s*([0-9.]+)", criterion)
            if threshold is None or float(threshold.group(1)) > 0:
                offenders.add(relative)
    assert offenders == set()


_CASE_SPEC_PROBE = "uip maestro case spec --type activity --activity-type-id t1 --connection-id c1"
_SDK_CONNECTOR_PROBES = (
    "uip maestro registry pull --output json",
    "uip maestro registry prepare uipath-salesforce-slack --action send-message-to-channel --connection-id c1",
    # A real resolution chained before a help call still counts: the help
    # exclusion stays inside its own command segment.
    "uip maestro registry pull --output json && uip maestro registry prepare --help",
)
# Reading usage resolves nothing, so a help call must not earn the criterion.
_CONNECTOR_HELP_PROBES = (
    "uip maestro case spec --help",
    "uip maestro registry prepare --help",
    "uip maestro registry pull -h | sed -n 1,80p",
)
_MUTATING_PROBE = "uip maestro case tasks add --stage-id s1 --type process --output json"
_HELP_PROBES = (
    "uip maestro case tasks add --help",
    "uip maestro case tasks add -h | sed -n 1,80p",
    "uip maestro case stages add-connector --help",
)


def _command_patterns(criterion: str) -> list[str]:
    match = re.search(r"(?m)^\s+command_pattern:\s*'((?:[^']|'')*)'", criterion)
    return [match.group(1).replace("''", "'")] if match else []


def test_connector_resolution_criteria_accept_either_loop() -> None:
    """Resolving a connector is `case spec` in the JSON loop and the connector
    library (`maestro registry pull` / `prepare`) in the SDK loop.

    A required criterion that names only `case spec` grades the JSON loop's
    mechanism, not the outcome; the typeId/connectionId the task needs is
    checked by the task's caseplan grader. A `--help` / `-h` call on those
    verbs reads usage and resolves nothing, so it must not satisfy the
    criterion.
    """
    offenders = []
    for relative, text in _tagged_tasks():
        for criterion_type, criterion in _criterion_blocks(text):
            if criterion_type != "command_executed":
                continue
            for pattern in _command_patterns(criterion):
                compiled = re.compile(pattern, re.DOTALL)
                if not compiled.search(_CASE_SPEC_PROBE):
                    continue
                offenders.extend(
                    f"{relative}: /{pattern}/ misses {probe!r}"
                    for probe in _SDK_CONNECTOR_PROBES
                    if not compiled.search(probe)
                )
                offenders.extend(
                    f"{relative}: /{pattern}/ matches {probe!r}"
                    for probe in _CONNECTOR_HELP_PROBES
                    if compiled.search(probe)
                )
    assert offenders == []


def test_mutating_verb_guards_ignore_help_calls() -> None:
    """A `--help` / `-h` call reads usage; it mutates nothing.

    The SDK loop checks a verb's flags before deciding not to use it, so a
    guard that counts `tasks add --help` fails a loop that never mutated.
    Every negative criterion that catches a real case-authoring mutation must
    let the same verb's help call through, in the same command segment.
    """
    offenders = []
    for relative, text in _tagged_tasks():
        for criterion_type, criterion in _criterion_blocks(text):
            if criterion_type != "command_not_executed":
                continue
            for pattern in _command_patterns(criterion):
                compiled = re.compile(pattern, re.DOTALL)
                if not compiled.search(_MUTATING_PROBE):
                    continue
                offenders.extend(
                    f"{relative}: /{pattern}/ matches {probe!r}"
                    for probe in _HELP_PROBES
                    if compiled.search(probe)
                )
    assert offenders == []
