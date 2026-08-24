"""Unit tests for audit_sdd.py's schema field-name casing guard and model-facts loader.

The casing guard exists because a `--output json` envelope PascalCases object keys
recursively (`request_body` -> `RequestBody`, `poText` -> `PoText`), so an SDD that reads
field names off those keys wires to fields the resource does not have. Runtime matching is
byte-for-byte, so the mismatch only surfaces in Studio Web ("RequestBody not found, did you
mean request_body") after the case is built.

These tests pin the guard's precision as much as its recall: it fires ONLY when a read path
contradicts this same document's Section 4 schema list, never on casing that merely looks
unusual.
"""

import os
import sys

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..",
        "skills", "uipath-planner", "scripts",
    ),
)

from audit_sdd import field_casing_findings, field_key, load_model_facts  # noqa: E402


def sdd(section_2: str, output_fields: str) -> str:
    return (
        "# SDD — Probe\n\n## Section 2: Stages & Tasks\n\n"
        + section_2
        + "\n\n## Section 4: Integrations\n\n"
        "| Operation | Activity Type ID | Method | Output Fields |\n"
        "|---|---|---|---|\n"
        f"| Assess | <UNRESOLVED> | POST | {output_fields} |\n"
    )


# --- recall: the reported defect ---------------------------------------------------------

def test_reported_defect_every_wrong_reference_is_caught():
    """The observed SDD had Section 4 right and Section 2 wrong, in five places."""
    text = sdd(
        "**Output Schema:**\n\n| Field | Binding / Value |\n|---|---|\n"
        "| RequestBody | -> contractPayload |\n\n"
        "- `=js:(vars.assess.CounterpartyProfile !== null)`\n"
        "- `=js:vars.assess.AuthorityLevel`\n"
        "- `=js:(response.UnusualClauses.length > 0)`\n"
        "- `=js:(response.DeviationFlags === true)`\n",
        "request_body: string, counterparty_profile: object, authority_level: string, "
        "unusual_clauses: array, deviation_flags: boolean",
    )
    findings = field_casing_findings(text)
    assert len(findings) == 5
    assert all("byte-for-byte" in f for f in findings)
    assert any("'RequestBody'" in f and "'request_body'" in f for f in findings)


def test_registry_discovery_potext_trap():
    """The exact example maestro-case's registry-discovery.md warns about."""
    findings = field_casing_findings(sdd("- `=js:(response.PoText !== null)`", "poText: string"))
    assert len(findings) == 1
    assert "'PoText'" in findings[0] and "'poText'" in findings[0]


def test_every_read_path_form_is_covered():
    forms = {
        "schema cell": "| Amount | -> total |",
        "response path": "- `=js:response.Amount`",
        "vars sub-field": "- `=js:vars.claim.Amount`",
        "trigger path": "- `=trigger.Amount`",
        "cross-task ref": '- `<- "Stage"."Task".Amount`',
        "xref": "- `vars.$xref('Stage','Task','Amount')`",
    }
    for label, line in forms.items():
        assert field_casing_findings(sdd(line, "amount: number")), f"{label} not covered"


# --- precision: must stay silent ---------------------------------------------------------

def test_casing_carried_verbatim_is_clean():
    text = sdd(
        "| request_body | -> contractPayload |\n- `=js:(response.unusual_clauses.length > 0)`",
        "request_body: string, unusual_clauses: array",
    )
    assert field_casing_findings(text) == []


def test_legitimate_pascalcase_is_not_flagged():
    """An app may declare `Decision`. Unusual-looking casing is not a defect."""
    assert field_casing_findings(sdd("- `=js:(response.Decision === \"Approved\")`", "Decision: string")) == []


def test_two_resources_declaring_both_casings_are_left_alone():
    """Section 4 listing both spellings means the document declares both as real."""
    text = (
        "# SDD — X\n\n## Section 2: Stages & Tasks\n\n"
        "- `=js:vars.a.Amount` and `=js:vars.b.amount`\n\n"
        "## Section 4: Integrations\n\n"
        "| Operation | Activity Type ID | Method | Output Fields |\n|---|---|---|---|\n"
        "| A | x | POST | Amount: number |\n| B | y | POST | amount: number |\n"
    )
    assert field_casing_findings(text) == []


def test_field_absent_from_section_4_is_not_guessed_at():
    """No schema list to contradict -> no finding. The prose rule and <UNRESOLVED> own this."""
    assert field_casing_findings(sdd("- `=js:response.SomethingElse`", "amount: number")) == []


def test_reserved_handles_are_never_treated_as_fields():
    text = sdd("- `=js:response.result` and `=response`", "result: string")
    assert field_casing_findings(text) == []


def test_no_section_4_means_no_check():
    assert field_casing_findings("# SDD — X\n\n## Section 2: Stages & Tasks\n\n- `=js:response.Amount`\n") == []


# --- the equivalence class ---------------------------------------------------------------

def test_field_key_collapses_separators_and_case():
    assert field_key("request_body") == field_key("requestBody") == field_key("RequestBody")
    assert field_key("po-text") == field_key("poText")
    assert field_key("amount") != field_key("amounts")


# --- B1: the loader must never disarm itself silently ------------------------------------

def test_load_model_facts_reports_a_clean_parse():
    facts, degraded = load_model_facts()
    assert degraded is None, f"layers guide no longer parses: {degraded}"
    assert facts["task_types"] and facts["yes_when"] and facts["name_pattern"] is not None


def test_load_model_facts_returns_a_two_tuple_contract():
    """Callers rely on the reason string to emit a finding instead of no-op'ing."""
    result = load_model_facts()
    assert isinstance(result, tuple) and len(result) == 2
    assert isinstance(result[0], dict)
    assert result[1] is None or isinstance(result[1], str)
