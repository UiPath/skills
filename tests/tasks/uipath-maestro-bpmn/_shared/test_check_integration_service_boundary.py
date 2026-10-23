"""Unit tests for check_integration_service_boundary blocker phrasing
and whitespace normalisation.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_integration_service_boundary import check_blockers  # noqa: E402


def test_blockers_present_single_line() -> None:
    notes = (
        "We need connection binding for the Slack connector.\n"
        "Also dynamic schema support is required.\n"
        "See bindings_v2.json for current mappings.\n"
        "Ensure package metadata is not hand-authored.\n"
    )
    result = check_blockers(notes)
    assert all(result.values()), f"Expected all blockers to pass, got: {result}"


@pytest.mark.parametrize(
    ("wrapped_text", "expected_key"),
    [
        ("connection\n   binding", "connection binding"),
        ("connection\r\n\tbinding", "connection binding"),
        ("package\n   metadata", "package metadata"),
        ("package\r\n\tmetadata", "package metadata"),
        ("dynamic\n   input schema", "dynamic schema(s)"),
        ("dynamic\n   schemas", "dynamic schema(s)"),
    ],
    ids=[
        "wrapped-connection-binding-newline",
        "wrapped-connection-binding-crlf-tab",
        "wrapped-package-metadata-newline",
        "wrapped-package-metadata-crlf-tab",
        "wrapped-dynamic-input-schema",
        "wrapped-dynamic-schemas",
    ],
)
def test_blockers_line_wrapped_phrases(
    wrapped_text: str, expected_key: str
) -> None:
    notes = f"Blocker notes: {wrapped_text} is managed by the CLI."
    result = check_blockers(notes)
    assert result[expected_key], (
        f"Expected {expected_key} to be satisfied by {wrapped_text!r}"
    )


def test_blockers_case_insensitive() -> None:
    notes = (
        "CONNECTION BINDING is CLI-owned.\n"
        "DYNAMIC INPUT SCHEMA cannot be authored by hand.\n"
        "Check BINDINGS_V2.JSON and PACKAGE METADATA.\n"
    )
    result = check_blockers(notes)
    assert all(result.values()), (
        f"Expected case-insensitive match, got: {result}"
    )


def test_blockers_missing_detected() -> None:
    notes = "Only connection binding is mentioned here."
    result = check_blockers(notes)
    assert result["connection binding"] is True
    assert result["package metadata"] is False
    assert result["dynamic schema(s)"] is False
    assert result["bindings_v2.json"] is False


@pytest.mark.parametrize(
    "phrasing",
    [
        "dynamic schema",
        "dynamic schemas",
        "dynamic input schema",
        "dynamic request payload schema",
        "dynamic custom activity input schema",
    ],
)
def test_dynamic_schema_variations(phrasing: str) -> None:
    result = check_blockers(phrasing)
    assert result["dynamic schema(s)"] is True
