"""Guard the operate, diagnose and evaluate contract of the BPMN skill.

The builder-SDK skill (V2) replaced the classic XML skill (V1, kept under
`classic/` only for its graders). A V1 -> V2 parity pass found rules V1 taught
for running and diagnosing a process that V2 had dropped, and ported them. This
test keeps both halves:

* `V1_RULES` - the V1 operate/diagnose rules V2 must keep teaching.
* `V2_RULES` - what V2 does better than V1. A later port from V1 must not
  replace these with the V1 wording.
* `V1_ONLY` - V1 instructions that are wrong for V2 (hand-edited XML, V1 file
  paths). They must not come back with a port.

Each entry is a phrase the reference must contain, not a full sentence, so a
rewording that keeps the rule passes. When a rule is reworded on purpose,
update its phrase here in the same PR.

Run from repo root:
    pytest tests/scripts/test_bpmn_operate_diagnose_contract.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL = REPO_ROOT / "skills" / "uipath-maestro-bpmn"


def _read(rel: str) -> str:
    # Collapse whitespace so a phrase still matches after the paragraph reflows.
    return re.sub(r"\s+", " ", (SKILL / rel).read_text(encoding="utf-8"))


V1_RULES = [
    # diagnose
    ("references/diagnose.md", "One literal command per read, never a loop"),
    ("references/diagnose.md", "No loop, function, alias or shell variable stands in for the verb"),
    ("references/diagnose.md", "chain the literal reads in one Bash call, one per line"),
    ("references/diagnose.md", "Name the read; do not run it now"),
    ("references/diagnose.md", "the read alone is the next action"),
    ("references/diagnose.md", "upload, publish and deploy are never the next action"),
    ("references/diagnose.md", "as an Operate decision outside the diagnosis"),
    ("references/diagnose.md", "When the request says not to ask for approval, do not ask"),
    ("references/diagnose.md", "Fetch the deployed asset **before writing the diagnosis, every time**"),
    ("references/diagnose.md", "do not read them by any means"),
    ("references/diagnose.md", "start from the first root fault"),
    ("references/diagnose.md", "**Never start with traces**"),
    ("SKILL.md", "one literal command per read and never a loop"),
    # operate
    ("references/operate.md", "## When pack, upload or import fails"),
    ("references/operate.md", "Never hand-edit a generated file to get past the error"),
    ("references/operate.md", '`{ "version": "2.0", "resources": [ … ] }` with one entry per dependency'),
    ("references/operate.md", "An empty `resources` array is right only for a process with no dependencies"),
    ("references/operate.md", "when one was not imported, say so in the reply"),
    ("references/operate.md", "**Never reuse a previous run's inputs silently.**"),
    ("references/operate.md", "Never retry a faulted instance before reading its incidents and deployed asset"),
    ("references/operate.md", "After every lifecycle command, fetch the instance again"),
    ("references/operate.md", "never use the deprecated `update-metadata`"),
    ("references/operate.md", '**"Publish" means Studio Web upload**'),
    ("references/operate.md", "Never use `debug` as validation"),
    # evaluate
    ("references/evaluate.md", "`--output-schema` is required"),
    ("references/evaluate.md", "`eval run start` is a deploy, not just a trigger"),
    ("references/evaluate.md", "pass **both** `--solution-id` and `--project-id`"),
    ("references/evaluate.md", "Simulate every side-effecting component"),
]

V2_RULES = [
    # diagnose: fix-owner labels and builder-aware failure modes
    ("references/diagnose.md", "`BPMN source` (the `.bpmn.ts`"),
    ("references/diagnose.md", "`Generated package metadata` (the four files `refresh` writes)"),
    ("references/diagnose.md", "`Integration Service enrichment` (connector metadata"),
    ("references/diagnose.md", "`Cloud configuration` (folder, process, release"),
    ("references/diagnose.md", "do not invent variants"),
    ("references/diagnose.md", "These are the ones that survive both"),
    ("references/diagnose.md", "`EXPR_UNDECLARED_REF`"),
    ("references/diagnose.md", "compare with the local `.bpmn.ts` and its compiled `.bpmn`"),
    # operate: upload overwrite safety, standalone publish, offline checks
    ("references/operate.md", "### Check the cloud copy before editing"),
    ("references/operate.md", '`Data.Action: "Overwritten"`'),
    ("references/operate.md", '`"Imported"` on a later upload means that id was lost'),
    ("references/operate.md", "### Standalone process publish"),
    ("references/operate.md", "uip maestro bpmn process publish <project-path> --folder-key <FOLDER_KEY>"),
    ("references/operate.md", "`flow-debug`"),
    ("references/operate.md", "the fix is in the `.bpmn.ts`"),
    # evaluate
    ("references/evaluate.md", "## Before the first eval command"),
]

V1_ONLY = [
    # V1 file layout; V2 has no such files.
    ("references/operate.md", "operate/CAPABILITY.md"),
    ("references/operate.md", "registry-workflow.md"),
    ("references/operate.md", "shared/project-layout.md"),
    ("references/diagnose.md", "diagnose/CAPABILITY.md"),
    ("references/diagnose.md", "troubleshooting-guide.md"),
    ("references/diagnose.md", "registry-workflow.md"),
    # V1 fixed the XML; V2 fixes the source and recompiles.
    ("references/operate.md", "fix `.bpmn` in Author"),
    ("references/diagnose.md", "Fix the BPMN binding source or rerun"),
    ("references/diagnose.md", "If CLI unavailable: add"),
]


@pytest.mark.parametrize(("rel", "phrase"), V1_RULES, ids=[p for _, p in V1_RULES])
def test_v1_rule_kept(rel: str, phrase: str) -> None:
    assert phrase in _read(rel), f"{rel} lost the V1 rule: {phrase!r}"


@pytest.mark.parametrize(("rel", "phrase"), V2_RULES, ids=[p for _, p in V2_RULES])
def test_v2_improvement_kept(rel: str, phrase: str) -> None:
    assert phrase in _read(rel), f"{rel} lost the V2 rule: {phrase!r}"


@pytest.mark.parametrize(("rel", "phrase"), V1_ONLY, ids=[p for _, p in V1_ONLY])
def test_v1_only_instruction_not_back(rel: str, phrase: str) -> None:
    assert phrase not in _read(rel), f"{rel} brought back a V1-only instruction: {phrase!r}"


def test_diagnosis_lifecycle_list_matches_operate() -> None:
    # Every lifecycle verb operate.md documents must be on diagnose.md's
    # "never the next action" list, so a new verb cannot slip into a diagnosis.
    operate = _read("references/operate.md")
    manage = operate.split("## Manage a running instance", 1)[1].split(" ## ", 1)[0]
    diagnose = _read("references/diagnose.md")
    start = diagnose.index("Retry, cancel, pause")
    never = diagnose[start : diagnose.index("are never the next action", start)].lower()
    reads = {"get", "list"}
    verbs = set(re.findall(r"uip maestro bpmn instance (\w+) ", manage)) - reads
    assert verbs, "operate.md lists no instance lifecycle commands"
    words = {"goto": "cursor movement"}
    for verb in sorted(verbs):
        assert words.get(verb, verb) in never, f"diagnose.md does not rule out {verb!r} as a next action"
