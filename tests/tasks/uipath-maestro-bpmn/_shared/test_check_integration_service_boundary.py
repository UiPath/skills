"""Unit tests for check_integration_service_boundary blocker phrasing,
concept matching, artifact inspection, and whitespace normalisation.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_integration_service_boundary import (  # noqa: E402
    check_artifact_bindings,
    check_blockers,
)


def test_blockers_present_single_line() -> None:
    notes = (
        "We need connection binding for the Slack connector.\n"
        "Also dynamic schema support is required.\n"
        "See bindings_v2.json for current mappings.\n"
        "Ensure package metadata is not hand-authored.\n"
    )
    result = check_blockers(notes)
    assert all(result.values()), (
        f"Expected all blockers to pass, got: {result}"
    )


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


@pytest.mark.parametrize(
    "phrasing",
    [
        "Slack connection … resource binding",
        "Slack connection ... resource binding",
        "Slack connector resource binding",
        "resource binding for Slack connection",
        "connection is not bound",
        "binding for connection",
        "connectors require binding",
    ],
)
def test_connection_binding_concept_paraphrases(phrasing: str) -> None:
    notes = f"Notice: {phrasing} is a blocker."
    result = check_blockers(notes)
    assert result["connection binding"] is True


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


@pytest.mark.parametrize(
    "phrasing",
    [
        "package metadata",
        "package and activity metadata",
        "package configuration metadata",
    ],
)
def test_package_metadata_variations(phrasing: str) -> None:
    result = check_blockers(phrasing)
    assert result["package metadata"] is True


def test_check_artifact_bindings_fallback(tmp_path: Path) -> None:
    required = {
        "connection binding": False,
        "dynamic schema(s)": True,
        "bindings_v2.json": False,
        "package metadata": True,
    }
    # When no artifact file is on disk, status is unchanged
    res = check_artifact_bindings(required, root_dir=str(tmp_path))
    assert res["connection binding"] is False
    assert res["bindings_v2.json"] is False

    # When bindings_v2.json exists with connection resources,
    # both are satisfied
    artifact = tmp_path / "bindings_v2.json"
    artifact.write_text(
        json.dumps({
            "version": "2.0",
            "resources": {
                "slack_service": {
                    "type": "uipath:connection",
                    "connector": "Slack",
                }
            },
        }),
        encoding="utf-8",
    )
    res = check_artifact_bindings(required, root_dir=str(tmp_path))
    assert res["bindings_v2.json"] is True
    assert res["connection binding"] is True
