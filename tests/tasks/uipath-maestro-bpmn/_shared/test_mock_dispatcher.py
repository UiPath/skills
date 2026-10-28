"""Unit tests for the shared mock `uip` dispatcher's rule matching.

A rule stops at the identifier so the agent's flags may follow in any order.
Matching whole tokens is what keeps that from also accepting a mistyped
identifier and handing back a valid canned response.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

DISPATCHER = Path(__file__).resolve().parent / "mock_template" / "mocks" / "uip"


def _load_matches():
    spec = importlib.util.spec_from_loader(
        "mock_uip", importlib.machinery.SourceFileLoader("mock_uip", str(DISPATCHER))
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._matches


matches = _load_matches()

RULE = "maestro bpmn job status job-triage-001"


@pytest.mark.parametrize(
    "argv",
    [
        "maestro bpmn job status job-triage-001",
        "maestro bpmn job status job-triage-001 --output json",
        "maestro bpmn job status job-triage-001 -f folder-public --output json",
        "maestro bpmn job status job-triage-001 --folder-key folder-public --output json",
        "maestro bpmn job status job-triage-001 --output json --folder-key folder-public",
    ],
)
def test_trailing_flags_match_in_any_order(argv: str) -> None:
    assert matches(RULE, argv)


@pytest.mark.parametrize(
    "argv",
    [
        "maestro bpmn job status job-triage-001-wrong --output json",
        "maestro bpmn job status job-triage-0011 --output json",
        "maestro bpmn job status xjob-triage-001 --output json",
        "maestro bpmn job status job-triage-002 --output json",
        "maestro bpmn job statuses job-triage-001 --output json",
    ],
)
def test_a_neighbouring_identifier_falls_through(argv: str) -> None:
    assert not matches(RULE, argv)


def test_an_interrupted_run_does_not_match() -> None:
    assert not matches(RULE, "maestro bpmn job --output json status job-triage-001")


def test_an_empty_rule_never_matches() -> None:
    assert not matches("", "maestro bpmn job status job-triage-001")
