"""Guard the connector request-shape rules in the maestro-bpmn skill.

These are the rules local validation cannot catch: `validateInputs`
short-circuits to `validateDynamicDirectInputs` for discovery-backed
`Intsvc.*` types, so a wrong target, a wrong operation, or a missing required
parameter passes `validate` AND `pack` and fails only at runtime. This guard asserts them against the
skill's own documented examples: deterministic, no agent, no tenant.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import json

from bpmn_doc_example import NS, REGISTRY_REFERENCE, ROOT, section_blocks

SPEC = ROOT / "skills" / "uipath-maestro-bpmn" / "validator" / "bpmn-spec.json"

BODY_SECTION = '### Body shape: hand-authored files need ONE `target="body"` input'
PARAM_SECTION = "### Required `Parameters` are separate from the body"

# integrationservice-sdk/src/dap/validation/rules.ts: METHOD_TO_OPERATION is a
# closed lexicon, and `uip is resources run` exposes exactly these operations.
OPERATION_LEXICON = {"List", "Retrieve", "Create", "Update", "Delete", "Replace"}


def _inputs(block: ET.Element) -> list[ET.Element]:
    return block.findall(f".//{{{NS['uipath']}}}input")


def _body_blocks() -> list[ET.Element]:
    return section_blocks(REGISTRY_REFERENCE, BODY_SECTION)


def test_each_example_carries_exactly_one_whole_body_input() -> None:
    """Several `target="body"` inputs do not merge; the last one wins.

    Asserted per block, not across them: flattening would stay green if the
    doc regressed to the sibling-input shape this section exists to forbid.
    """

    seen = 0
    for block in _body_blocks():
        bodies = [i for i in _inputs(block) if i.attrib.get("target") == "body"]
        if not bodies:
            continue
        seen += 1
        assert len(bodies) == 1, [b.attrib for b in bodies]
        body = bodies[0]
        assert body.attrib.get("type") == "json", body.attrib
        assert (body.text or "").strip(), f"{body.attrib} carries no body payload"
    assert seen, "the body-shape section documents no target='body' input"


def test_no_documented_connector_input_uses_bodyfield() -> None:
    """`bodyField` is the merged-arguments target; no `Intsvc.*` type uses it."""

    offenders = [
        item.attrib
        for block in _body_blocks()
        for item in _inputs(block)
        if item.attrib.get("target") == "bodyField"
    ]
    assert not offenders, f"bodyField shown on a connector activity: {offenders}"


def test_required_parameters_are_their_own_targeted_inputs() -> None:
    """A required `Parameters` entry is never folded into the body."""

    targeted = [
        item
        for block in section_blocks(REGISTRY_REFERENCE, PARAM_SECTION)
        for item in _inputs(block)
        if item.attrib.get("target") in {"query", "path"}
    ]
    assert targeted, (
        "no required parameter is shown as its own targeted input; omitting one "
        "fails only at runtime with \"required parameter '<name>' not found\""
    )
    for item in targeted:
        assert item.attrib.get("name"), item.attrib


def test_operation_stays_inside_the_closed_lexicon() -> None:
    """`CreateIssue` and friends can never resolve; only the six names do.

    Checks the XML surface as well as the CLI flag: the section's subject is
    the authored node, where `operation` is an input value.
    """

    content = REGISTRY_REFERENCE.read_text(encoding="utf-8")
    for operation in re.findall(r"--operation\s+([A-Za-z]+)", content):
        assert operation in OPERATION_LEXICON, (
            f"--operation {operation} is outside METHOD_TO_OPERATION's lexicon"
        )
    for section in (BODY_SECTION, PARAM_SECTION):
        for block in section_blocks(REGISTRY_REFERENCE, section):
            for item in _inputs(block):
                if item.attrib.get("name") == "operation":
                    assert item.attrib.get("value") in OPERATION_LEXICON, item.attrib


def _spec_entries() -> list[dict]:
    def walk(node):
        if isinstance(node, dict):
            if "extensionType" in node:
                yield node
            for value in node.values():
                yield from walk(value)
        elif isinstance(node, list):
            for value in node:
                yield from walk(value)

    return list(walk(json.loads(SPEC.read_text(encoding="utf-8"))))


def test_spec_notes_do_not_teach_the_shape_the_runtime_rejects() -> None:
    """The spec is what agents author from; documenting around it is not a fix.

    Its notes told authors to add one uipath:input per request field, and to
    take `operation` from the activity's own Name -- both the exact faults
    this section corrects.
    """

    body_types = [
        entry
        for entry in _spec_entries()
        if entry.get("extensionType", "").startswith("Intsvc.")
        and entry.get("inputTarget") == "body"
    ]
    assert body_types, "no Intsvc.* type with inputTarget=body found in the spec"
    teaches_separate = re.compile(
        r"each request field|separate <uipath:input>|one .{0,12}input per field",
        re.I,
    )
    for entry in body_types:
        notes = entry.get("inputNotes") or ""
        assert not teaches_separate.search(notes), (
            f"{entry['extensionType']} inputNotes teach the separate-input "
            f"shape the runtime rejects: {notes!r}"
        )
        if notes:
            assert 'target=\"body\"' in notes, entry["extensionType"]
        discovery = entry.get("discoveryNotes") or ""
        assert "Set operation from Name" not in discovery, entry["extensionType"]
