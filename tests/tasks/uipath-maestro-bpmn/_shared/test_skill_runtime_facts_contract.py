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
* Every authored expression is `=js:`: the designer opens a plain `=` in its
  C# editor (PO.Frontend `JAVASCRIPT_PATH_PREFIX`).
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


# A quoted plain expression: a variable or metadata read, or a literal, without `=js:`.
PLAIN_EXPR = re.compile(r"[\"'`]=(vars\.|metadata\.|true\b|false\b|null\b|\d|\")")
# A real canvas import keeps the canvas's own (C#) expressions; the rule quotes
# the wrong form once, to warn against it; the canvas writes a start-event row
# that maps a process input, and a human-task form field's value, plain.
CANVAS_IMPORT = "InvoiceApproval.bpmn.ts"
FORM_VALUE = re.compile(r"value: '=vars\.[\w.\[\]<>]+'|source: '=vars\.\w+',\s*var:")
# Plain forms the skill names on purpose: the wrong form it warns against, the
# hint `check` prints, and the start-event row and human-task form value the canvas writes plain.
QUOTED_PLAIN = ('`=vars.d.toLowerCase() == "approve"`', "`value` (`=vars.<id>`:", "(`=vars.<inputId>`)")


def _strip(line: str, phrases: tuple[str, ...]) -> str:
    for phrase in phrases:
        line = line.replace(phrase, "")
    return line


@pytest.mark.parametrize("path", [p for p in DOCS if p.name != CANVAS_IMPORT], ids=_id)
def test_authored_exprs_are_js(path: Path) -> None:
    hits = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if PLAIN_EXPR.search(re.sub(FORM_VALUE, "", _strip(line, QUOTED_PLAIN)))
    ]
    assert not hits, f"{_id(path)} writes a plain `=` expression (opens in the C# editor): {hits}"


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
    ("references/bpmn-runtime.md", "RULE:bpmn.variables.output-end-mapping"),
    ("references/bpmn-runtime.md", "A process returns only what its end event maps"),
    ("references/bpmn-runtime.md", "RULE:bpmn.orchestrator.in-solution-process"),
    ("references/bpmn-runtime.md", "RULE:bpmn.expression.js-everywhere"),
    ("references/bpmn-runtime.md", "Write every expression you author as `=js:` JavaScript, in any field"),
    ("references/bpmn-runtime.md", "RULE:bpmn.hitl.no-completer-identity"),
    ("references/patterns/high-volume-batch-guide.md", "Name the loop the way Studio Web does: `itemVar: 'iterator[0]'`"),
    ("references/patterns/high-volume-batch-guide.md", "the inner key stays `item`"),
    ("SKILL.md", "A process returns only what its end event maps"),
    ("references/operate.md", "not by `Globals`"),
    ("references/patterns/high-volume-batch-guide.md", "1-based"),
    ("references/patterns/high-volume-batch-guide.md", "the response is a bare array of records, `[]` when none"),
    ("references/connectors.md", "A connection is a sender's identity"),
]


def test_loop_sketches_name_the_iterator_the_way_the_canvas_does() -> None:
    # Studio Web writes inputElement="iterator[N]" and reads iterator[N].item. With any other
    # itemVar, `iterator[0]` reads null (debug run, itemVar 'item' and 'invoice').
    text = _read("references/patterns/high-volume-batch-guide.md") + _read("references/patterns/composing-guide.md")
    item_vars = re.findall(r"loop: \{[^}]*itemVar: '([^']+)'", text)
    assert item_vars, "the loop sketches no longer declare an itemVar"
    assert all(re.fullmatch(r"iterator\[\d+\]", v) for v in item_vars), item_vars


@pytest.mark.parametrize("rel,phrase", REQUIRED, ids=[f"{r}:{p}" for r, p in REQUIRED])
def test_runtime_fact_is_still_taught(rel: str, phrase: str) -> None:
    assert phrase in _read(rel), f"{rel} no longer says {phrase!r}"
