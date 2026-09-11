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
