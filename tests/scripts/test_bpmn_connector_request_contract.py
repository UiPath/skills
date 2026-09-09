"""Guard the connector request-shape rules in the maestro-bpmn skill.

These rules are the ones local validation cannot catch: `validateInputs`
short-circuits to `validateDynamicDirectInputs` for discovery-backed
`Intsvc.*` types, so a wrong target, a wrong operation, or a missing required
parameter passes `validate` AND `pack` and fails only at runtime. Until now
the only thing that caught them was the tenant-gated escalation e2e, which
never runs on a pull request. This guard asserts the same rules against the
skill's own documented examples: deterministic, no agent, no tenant.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = (
    ROOT / "skills" / "uipath-maestro-bpmn" / "references" / "registry-workflow.md"
)
NS = {"uipath": "http://uipath.org/schema/bpmn"}

# integrationservice-sdk/src/dap/validation/rules.ts: METHOD_TO_OPERATION is a
# closed lexicon, and `uip is resources run` exposes exactly these operations.
OPERATION_LEXICON = {"List", "Retrieve", "Create", "Update", "Delete", "Replace"}


def _blocks() -> list[ET.Element]:
    """Parse every XML example, wrapped so the doc's fragments resolve.

    A block that will not parse even wrapped is a defect in the doc: agents
    copy these verbatim, and an unescaped `<placeholder>` in an attribute
    makes the file not well-formed.
    """

    content = REFERENCE.read_text(encoding="utf-8")
    parsed, broken = [], []
    for xml in re.findall(r"```xml\n(.*?)\n```", content, re.DOTALL):
        wrapped = f'<doc xmlns:uipath="{NS["uipath"]}">{xml}</doc>'
        try:
            parsed.append(ET.fromstring(wrapped))
        except ET.ParseError as error:
            broken.append((xml.splitlines()[0][:80], str(error)))
    assert not broken, f"registry-workflow.md has XML examples that do not parse: {broken}"
    assert parsed, "registry-workflow.md has no parseable XML examples"
    return parsed


def _inputs(root: ET.Element) -> list[ET.Element]:
    if root.tag == f"{{{NS['uipath']}}}input":
        return [root]
    return root.findall(f".//{{{NS['uipath']}}}input")


def test_body_example_is_a_single_whole_body_input() -> None:
    """Several `target="body"` inputs do not merge; the last one wins."""

    bodies = [
        item
        for block in _blocks()
        for item in _inputs(block)
        if item.attrib.get("target") == "body"
    ]
    assert bodies, "the body-shape section documents no target='body' input"
    for body in bodies:
        assert body.attrib.get("type") == "json", body.attrib
        # The whole request object rides in element content, not in siblings.
        assert (body.text or "").strip(), f"{body.attrib} carries no body payload"


def test_no_documented_connector_input_uses_bodyfield() -> None:
    """`bodyField` is the merged-arguments target; no `Intsvc.*` type uses it."""

    offenders = [
        item.attrib
        for block in _blocks()
        for item in _inputs(block)
        if item.attrib.get("target") == "bodyField"
    ]
    assert not offenders, f"registry-workflow.md shows bodyField on a connector: {offenders}"


def test_required_parameters_are_their_own_targeted_inputs() -> None:
    """A required `Parameters` entry is never folded into the body."""

    targeted = [
        item
        for block in _blocks()
        for item in _inputs(block)
        if item.attrib.get("target") in {"query", "path"}
    ]
    assert targeted, (
        "registry-workflow.md no longer shows a required parameter as its own "
        "targeted input; that omission fails only at runtime with "
        "\"Value for required parameter '<name>' not found\""
    )
    for item in targeted:
        assert item.attrib.get("name"), item.attrib


def test_operation_guidance_uses_the_closed_lexicon() -> None:
    """`CreateIssue` and friends can never resolve; only the six names do."""

    content = REFERENCE.read_text(encoding="utf-8")
    for operation in re.findall(r"--operation\s+([A-Za-z]+)", content):
        assert operation in OPERATION_LEXICON, (
            f"--operation {operation} is outside METHOD_TO_OPERATION's lexicon "
            f"{sorted(OPERATION_LEXICON)}"
        )
