"""Guard the runtime facts live runs established for the BPMN skill (V2).

Each fact below was settled by a debug run on a test tenant or by the
PO.Frontend / PO.BpmnEngine source, and the skill was wrong about it before.
A later edit that brings the old wording back fails here.

* An error event sub-process stores its default capture as a JSON string, so
  every field read goes through JSON.parse.
* A business rule's result is keyed by the OutputArguments property name, not
  the entry point's display name.
* `registry prepare` writes under `.flow-sdk/`, and `compile` reads it from the
  current directory, so it runs where `prepare` ran.
* Only an Enabled connection may be bound.
* Outlook `saveAsDraft` must be set explicitly.
* Retry is activity configuration, never a drawn loop.

Run from repo root:
    pytest tests/tasks/uipath-maestro-bpmn/_shared/test_skill_runtime_facts_contract.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL = REPO_ROOT / "skills" / "uipath-maestro-bpmn"

DOCS = sorted(
    p for p in SKILL.rglob("*") if p.is_file() and p.suffix in {".md", ".ts"}
)


def _read(rel: str) -> str:
    return re.sub(r"\s+", " ", (SKILL / rel).read_text(encoding="utf-8"))


# A field read straight off an error net's capture, such as
# `vars.failures_Error.message`, not preceded by `JSON.parse(`.
NET_FIELD_READ = re.compile(r"(?<!JSON\.parse\()vars\.failures_Error\.(?:code|message|detail|category|status)\b")


# The one place the skill quotes the wrong read on purpose, to warn against it.
WARNING = "A plain `vars.failures_Error.message` reads undefined"


@pytest.mark.parametrize("path", DOCS, ids=lambda p: str(p.relative_to(SKILL)))
def test_error_net_capture_is_parsed_before_a_field_read(path: Path) -> None:
    text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8")).replace(WARNING, "")
    hits = NET_FIELD_READ.findall(text)
    assert not hits, (
        f"{path.relative_to(SKILL)} reads a field straight off vars.failures_Error; "
        "the capture is a JSON string, so read it through JSON.parse(vars.failures_Error)"
    )


@pytest.mark.parametrize("path", DOCS, ids=lambda p: str(p.relative_to(SKILL)))
def test_business_rule_is_not_keyed_by_display_name(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert "=result.<Decision>." not in text, (
        f"{path.relative_to(SKILL)} keys a business-rule result by `<Decision>`; "
        "the key is the OutputArguments property name"
    )


REQUIRED = [
    ("references/bpmn-runtime.md", "JSON **string**"),
    ("references/bpmn-runtime.md", "not the entry point's `DisplayName`"),
    ("references/bpmn-runtime.md", "RULE:bpmn.activity.retry"),
    ("references/connectors.md", "./.flow-sdk/bindings.json"),
    ("references/connectors.md", "from the directory you ran `prepare` in"),
    ("references/connectors.md", "Bind only an Enabled connection"),
    ("references/connectors.md", "uip is connections ping"),
    ("references/connectors.md", "Always set `saveAsDraft`"),
    ("SKILL.md", "never a drawn loop"),
]


@pytest.mark.parametrize("rel,phrase", REQUIRED, ids=[f"{r}:{p}" for r, p in REQUIRED])
def test_runtime_fact_is_still_taught(rel: str, phrase: str) -> None:
    assert phrase in _read(rel), f"{rel} no longer says {phrase!r}"
