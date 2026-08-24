"""Parity guard for the canonical/twin pair that carries the case product model.

`uipath-planner` is the canonical home for case knowledge and guidance. `uipath-maestro-case`
carries an operational twin of the same product rules, because this repo requires every skill to
function with its siblings absent and forbids a skill from reading another skill's files
(CLAUDE.md § Architecture, .claude/rules/skill-structure.md § Content Rules). The duplication is
therefore mandated, not accidental — which makes silent DRIFT the real risk.

This test pins the invariants both sides must state. It deliberately checks that each side makes
the claim in ITS OWN words rather than comparing text: the two docs speak to different audiences
(design-time authoring vs build-time emission), so byte-parity would be wrong and brittle. A
concept is satisfied when at least one of its accepted phrasings appears on that side; deleting a
rule from either side fails the test, while rewording it does not.
"""

import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")
CANONICAL = os.path.join(ROOT, "skills", "uipath-planner", "references", "case-design-layers-guide.md")
TWIN = os.path.join(ROOT, "skills", "uipath-maestro-case", "references", "sla-response-shapes.md")
CANONICAL_FIELDS = CANONICAL
TWIN_FIELDS = os.path.join(ROOT, "skills", "uipath-maestro-case", "references", "registry-discovery.md")


def read(path: str) -> str:
    with open(path, encoding="utf-8") as handle:
        return handle.read()


# (concept, [accepted phrasings on the canonical side], [accepted phrasings on the twin side])
SLA_RESPONSE_MODEL = [
    (
        "the closed response set",
        [r"`notify-only`", r"`start-task`", r"`enter-stage`", r"`exit-stage`", r"`exit-case`"],
        [r"notify-only", r"start-task", r"enter-stage", r"exit-stage", r"exit-case"],
    ),
    (
        "a start-task response has no interrupting value",
        [r"a task entry interrupts nothing", r"task-entry row"],
        [r"has no interrupting cell at all", r"task-entry rule"],
    ),
    (
        "response follows what happens to active work, not the SLA's scope",
        [r"never whether it interrupts", r"pauses, takes over, or reroutes"],
        [r"never the SLA's scope", r"stops, pauses, takes over, or reroutes"],
    ),
    (
        "an `any` escalation reference is invalid",
        [r"`any` escalation reference \| invalid"],
        [r'escalationId: "any"'],
    ),
    (
        "a dangling SLA reference is invalid",
        [r"Dangling SLA reference \| invalid"],
        [r"[Dd]angling"],
    ),
    (
        "a task with no entry condition never starts",
        [r"Task with empty or absent entry conditions \| valid — and the task never starts"],
        [r"A task with no entry condition never starts"],
    ),
    (
        "start-task authored as stage re-entry re-runs the stage",
        [r"stage re-entry re-runs every task whose `Run Only Once` is `No`"],
        [r"`start-task` authored as stage re-entry"],
    ),
]

FIELD_NAME_INVARIANT = [
    (
        "`--output json` PascalCases object keys, so names must not be read from them",
        [r"PascalCase object \*\*keys\*\* recursively", r"never read names off a `--output json` envelope"],
        [r"PascalCases object keys recursively"],
    ),
    (
        "the case-preserving names come from elsewhere, not the envelope",
        [r"Outputs\.ResponseFields\[\]\.Name"],
        [r"case-preserving", r"entry-points\.json"],
    ),
]


def assert_pair(concepts, canonical_path, twin_path):
    canonical, twin = read(canonical_path).lower(), read(twin_path).lower()
    missing = []
    for concept, canonical_forms, twin_forms in concepts:
        if not any(re.search(f.lower(), canonical) for f in canonical_forms):
            missing.append(f"CANONICAL ({os.path.basename(canonical_path)}) no longer states: {concept}")
        if not any(re.search(f.lower(), twin) for f in twin_forms):
            missing.append(f"TWIN ({os.path.basename(twin_path)}) no longer states: {concept}")
    assert not missing, "canonical/twin drift:\n  " + "\n  ".join(missing)


def test_sla_response_model_stated_on_both_sides():
    assert_pair(SLA_RESPONSE_MODEL, CANONICAL, TWIN)


def test_field_name_invariant_stated_on_both_sides():
    assert_pair(FIELD_NAME_INVARIANT, CANONICAL_FIELDS, TWIN_FIELDS)


def test_both_sides_declare_the_twin_relationship():
    """Neither page may present itself as the only source, or the next editor will not know to sync."""
    canonical, twin = read(CANONICAL), read(TWIN)
    assert "Canonical + twin" in canonical, "planner Layer 4 lost its canonical/twin declaration"
    assert "uipath-maestro-case" in canonical, "planner no longer names the twin skill"
    assert "Twin of a canonical page" in twin, "maestro page lost its twin declaration"
    assert "uipath-planner" in twin, "maestro page no longer names the canonical skill"


def test_neither_side_links_into_the_other_skills_files():
    """Self-containment: sibling references are by skill NAME, never by file path."""
    for path in (CANONICAL, TWIN, TWIN_FIELDS,
                 os.path.join(ROOT, "skills", "uipath-planner", "references", "case-design-lane-guide.md"),
                 os.path.join(ROOT, "skills", "uipath-maestro-case", "SKILL.md")):
        text = read(path)
        offenders = re.findall(r"\]\((?:\.\./)+uipath-[a-z-]+/[^)]+\)", text)
        assert not offenders, f"{os.path.basename(path)} links into another skill's files: {offenders}"
