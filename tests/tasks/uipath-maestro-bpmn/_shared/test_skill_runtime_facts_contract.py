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
* Retry is activity configuration, never a drawn loop, and an `errorMapping`
  row names a declared error's id, never a bare status code: `code: '429'`
  validates and retries nothing.

Run from repo root:
    pytest tests/tasks/uipath-maestro-bpmn/_shared/test_skill_runtime_facts_contract.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
SKILL = REPO_ROOT / "skills" / "uipath-maestro-bpmn"
STUDIOWEB = REPO_ROOT / "skill-flavors" / "studioweb" / "uipath-maestro-bpmn"

# The canonical skill and its Studio Web overrides, so an override cannot bring
# the old wording back either.
DOCS = sorted(
    p
    for root in (SKILL, STUDIOWEB)
    for p in root.rglob("*")
    if p.is_file() and p.suffix in {".md", ".ts"}
)


def _id(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def _read(rel: str) -> str:
    return re.sub(r"\s+", " ", (SKILL / rel).read_text(encoding="utf-8"))


# Any lowercase field read straight off an `<id>_Error` variable, such as
# `vars.failures_Error.message`. Net captures are JSON strings; connector and
# HTTP `<id>_Error` shapes are unverified, so both are banned until a live run
# settles them. The correct net read, `JSON.parse(vars.failures_Error).message`,
# and a script task's PascalCase `Error` row (`.Message`) are not matched. A net
# capture renamed with `errorVar` is not caught here.
NET_FIELD_READ = re.compile(r"vars\.\w+_Error\.(?:code|message|detail|category|status|traceId|response|element)\b")


# The one place the skill quotes the wrong read on purpose, to warn against it.
WARNING = "A plain `vars.failures_Error.message` reads undefined"


@pytest.mark.parametrize("path", DOCS, ids=_id)
def test_error_net_capture_is_parsed_before_a_field_read(path: Path) -> None:
    text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8")).replace(WARNING, "")
    hits = NET_FIELD_READ.findall(text)
    assert not hits, (
        f"{_id(path)} reads a field straight off an `<id>_Error` variable; "
        "a net capture is a JSON string (JSON.parse first), and other tasks' Error shapes are unverified"
    )


@pytest.mark.parametrize("path", DOCS, ids=_id)
def test_business_rule_is_not_keyed_by_display_name(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert "=result.<Decision>." not in text, (
        f"{_id(path)} keys a business-rule result by `<Decision>`; "
        "the key is the OutputArguments property name"
    )


# An `errorMapping` row whose code is a bare status (`code: '429'`). The engine
# reads the row's code as a declared error's id, so this retries nothing.
BARE_STATUS_MAPPING = re.compile(r"errorMapping:\s*\[[^\]]*code:\s*['\"]\d{3}['\"]")
# The one place the skill quotes the wrong row on purpose, to warn against it.
MAPPING_WARNING = "`code: '429'` passes `check` and `validate` and retries nothing"


@pytest.mark.parametrize("path", DOCS, ids=_id)
def test_error_mapping_names_a_declared_error(path: Path) -> None:
    text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8")).replace(MAPPING_WARNING, "")
    assert not BARE_STATUS_MAPPING.search(text), (
        f"{_id(path)} maps a bare status code in errorMapping; "
        "the row's code is a declared bpmn:error id, so a status code retries nothing"
    )


REQUIRED = [
    ("references/bpmn-runtime.md", "JSON **string**"),
    ("references/bpmn-runtime.md", "not the entry point's `DisplayName`"),
    ("references/bpmn-runtime.md", "`<decisionKey>` is the property name under `OutputArguments.properties`"),
    ("references/bpmn-runtime.md", "RULE:bpmn.activity.retry"),
    ("references/bpmn-runtime.md", "is the **id of a declared `bpmn:error`**"),
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
