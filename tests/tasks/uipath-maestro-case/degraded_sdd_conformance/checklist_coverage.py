#!/usr/bin/env python3
"""Measure which planner conformance-checklist items the CLI enforces.

Seeds one single-construct violation per checklist item
(skills/uipath-planner/references/case/case-sdd-conformance-checklist.md) into
the planner-written sla_from_sdd fixture, then asks the installed `uip`:

- `sdd validate` exits non-zero → "validate"
- `sdd validate` warns only → "validate-warns"
- `sdd convert` refuses, or reports an Unresolved kind the seed does not → "convert"
- none of those → "silent", tagged by whether `sdd parse`'s Model changes:
  "model identical" (invisible to the build) or "model changes" (the defect is
  carried into the build unreported).

Each row that converts also records `build_validate`: the findings plain
`uip maestro case validate` raises on the converted plan beyond the seed
plan's own. Those arrive after the planner's handoff, so they do not count as
gate coverage; they show where the defect is caught later, if anywhere.

This is a measurement, not a pass/fail test: the checklist cannot be deleted
(skills S4) until every item reads "validate". Mutations are generated from
the seed each run, and a mutation that no longer applies is reported rather
than skipped, so a moved seed cannot fake coverage.

Run from repo root with the build under test on PATH:
    python3 tests/tasks/uipath-maestro-case/degraded_sdd_conformance/checklist_coverage.py \
        --out tests/tasks/uipath-maestro-case/degraded_sdd_conformance/checklist_coverage.json
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = HERE.parent / "sla_from_sdd" / "fixtures" / "sdd.md"


def rep(old, new):
    def f(s):
        assert old in s, f"missing: {old!r}"
        return s.replace(old, new, 1)
    return f


def rep_all(old, new):
    def f(s):
        assert old in s, f"missing: {old!r}"
        return s.replace(old, new)
    return f


def drop_line_after(anchor, prefix):
    def f(s):
        i = s.index(anchor)
        j = s.index("\n" + prefix, i)
        return s[:j] + s[s.index("\n", j + 1):]
    return f


def after(anchor, old, new):
    def f(s):
        j = s.index(old, s.index(anchor))
        return s[:j] + new + s[j + len(old):]
    return f


# (checklist item, what the mutation violates, mutation)
MUTATIONS = [
    (1, "title not `# SDD —`", rep("# SDD — WarrantyClaimTriage", "# Design — WarrantyClaimTriage")),
    (2, "`### Process App Views` missing", rep("### Process App Views\n", "")),
    (2, "Planner Handoff marker missing", rep("<!-- planner-handoff:v1 -->\n", "")),
    (3, "summary-only `## Business Rules`", rep("## Section 1: Case Definition", "## Business Rules\n\nApprovals follow policy.\n\n## Section 1: Case Definition")),
    (4, "Case Variables header columns renamed", rep("| sourceTriggers | sourceFields |", "| Source Triggers | Source Fields |")),
    (5, "stage block missing **Type:** Stage", drop_line_after("### Stage 1: Intake", "**Type:** Stage")),
    (6, "no Activation Mode in the Tasks table or the block", lambda t: drop_line_after("##### Task 1.1", "**Activation Mode:**")(rep("| 1 | Validate Claim Details | api-workflow | sequential |", "| 1 | Validate Claim Details | api-workflow | — |")(t))),
    (7, "literal \\n in content", rep("| case-entered | — | No | Claim received |", "| case-entered | — | No | Claim\\nreceived |")),
    (8, "task Type not a legal literal", after("### Stage 1: Intake", "| api-workflow |", "| external-workflow |")),
    (9, "stage entry uses a task-entry rule", rep('| selected-stage-completed("Intake") | =js:(vars.paperworkComplete === true) |', "| runs-sequentially | =js:(vars.paperworkComplete === true) |")),
    (10, "return-to-origin in Case Exit Conditions", rep("| Case closed as rejected |", "| return-to-origin |")),
    (11, "task name contains `:`", rep_all("Assess Damage", "Assess: Damage")),
    (12, "task display name duplicated across stages", rep_all("Record Rejection", "Issue Settlement")),
    (13, "sla-status-change names an undeclared SLA title", rep('sla-status-change("Intake","Intake SLA")', 'sla-status-change("Intake","Nope SLA")')),
    (13, "sla-status-change call never closes", rep('sla-status-change("Assessment","Assessment SLA")', 'sla-status-change("Assess (`assess`)')),
    (14, "selector names an undeclared stage", rep('selected-stage-completed("Intake")', 'selected-stage-completed("Intakes")')),
    (15, "stage entry references its own stage", rep('selected-stage-completed("Intake") | =js:(vars.paperworkComplete', 'selected-stage-completed("Assessment") | =js:(vars.paperworkComplete')),
    (16, "=vars.X not in Case Variables", rep("| productSerial | string | =vars.productSerial |", "| productSerial | string | =vars.productSerialNo |")),
    (20, "Recipient without a typed prefix", rep("**Recipient:** Role: Claims Handlers", "**Recipient:** Claims Handlers")),
    (21, "stage entry table with no body row", after("### Stage 3: Settlement", '| selected-stage-completed("Assessment") | =js:(vars.assessorDecision === "Settle") | No | Settle approved |\n', "")),
    (22, "no case-entered anywhere", rep("| case-entered | — | No | Claim received |", '| selected-stage-exited("Assessment") | — | No | Claim received |')),
    (23, "Case Triggers has no rows", rep("| T02 | Manual | Manual | N/A |\n", "")),
    (24, "no Case Exit row marks the case complete", rep("| required-stages-completed | — | Case exited | Yes | Claim resolved |", "| required-stages-completed | — | Case exited | No | Claim resolved |")),
    (25, "wait-for-user exit without a user-selected-stage entry", rep("| required-tasks-completed | — | exit-only | Yes | Settlement complete |", "| required-tasks-completed | — | wait-for-user | Yes | Settlement complete |")),
    (26, "required-tasks-completed with no Required task", rep("| 1 | Lead Escalation Review | action | parallel | stage enters | Yes |", "| 1 | Lead Escalation Review | action | parallel | stage enters | No |")),
    (27, "stage entry equals a Case Exit row", after("### Stage 3: Settlement", '| selected-stage-completed("Assessment") | =js:(vars.assessorDecision === "Settle") | No |', '| selected-stage-completed("Claim Rejected") | — | No |')),
    (29, "case SLA below 15 minutes", rep("| Case-Level SLA | 5 d |", "| Case-Level SLA | 5 min |")),
    (17, "consumed Variable never produced (its Outputs row removed)", rep("| response.damageCategory | -> damageCategory |\n", "")),
    (18, "Out variable with no Default and no producer", rep("| claimOutcome | Out | string | | | Pending | Final disposition returned to the caller |", "| claimOutcome | Out | string | | | Pending | Final disposition returned to the caller |\n| reviewSummary | Out | string | | | | Summary returned to the caller |")),
    (19, "Buttons Maps To an undeclared variable", rep('| Settle | assessorDecision = "Settle" |', '| Settle | assessorVerdict = "Settle" |')),
    (28, "unguarded exit row shares its WHEN with the guarded completion row", rep('| required-tasks-completed | =js:(vars.assessorDecision !== "Reject") | exit-only | Yes | Assessment complete |', '| required-tasks-completed | =js:(vars.assessorDecision !== "Reject") | exit-only | Yes | Assessment complete |\n| required-tasks-completed | — | exit-only | No | Leave assessment |')),
    (35, "user-selected-stage entry on a lane a decision routes to", rep('| selected-stage-exited("Assessment") | =js:(vars.assessorDecision === "Reject") | Yes | Rejected by assessor |', '| selected-stage-exited("Assessment") | =js:(vars.assessorDecision === "Reject") | Yes | Rejected by assessor |\n| user-selected-stage | — | No | Pick the rejected lane |')),
    (36, "secondary lane entered on any exit of a stage that also completes normally", rep('| selected-stage-exited("Assessment") | =js:(vars.assessorDecision === "Reject") | Yes | Rejected by assessor |', '| selected-stage-exited("Assessment") | — | Yes | Rejected by assessor |')),
    (34, "either/or persona", rep("| Claims Assessor | — |", "| Claims Assessor or Claims Lead | — |")),
]


# Draft-parity items compare the final against the draft it finalized. No CLI
# command takes the draft, so no mutation of the final alone can reach them:
# they are measured as "needs-draft", never "silent", and stay with the
# planner's checklist walk until a draft-aware check exists.
NEEDS_DRAFT = [
    (30, "stage/task inventory differs from the draft's"),
    (31, "a draft `=js:` expression missing or rewritten in the final"),
    (32, "a draft comparator + amount policy not encoded in an executable cell"),
    (33, "the draft file deleted or renamed"),
]


EXCLUDED = [
    (5, "stage/task block missing **Design Rationale:**",
     "not checked by decision (Cliff, 2026-10-02): a design document does not owe rationale prose. When present, the build copies it into the plan as `rationale:` and convert uses it as a task description that has none; its absence breaks nothing"),
]


def uip(verb, path, *extra):
    r = subprocess.run(["uip", "maestro", "case", "sdd", verb, str(path), "--output", "json", *extra],
                       capture_output=True, text=True, timeout=120)
    try:
        return r.returncode, json.loads(r.stdout)
    except json.JSONDecodeError:
        return r.returncode, {"Message": r.stdout[:200]}


def unresolved(path, work):
    """Unresolved items as (kind, where) pairs — a new item of a kind the seed
    already has still counts — plus the build-side findings of plain
    `uip maestro case validate` on the converted plan."""
    plan = work / (path.stem + ".caseplan.json")
    code, out = uip("convert", path, "--out", str(plan))
    if code != 0:
        return None, None, (out.get("Message") or "")[:160]
    r = subprocess.run(["uip", "maestro", "case", "validate", str(plan), "--output", "json"],
                       capture_output=True, text=True, timeout=120)
    built = [(i.get("Code"), i.get("Severity")) for i in (json.loads(r.stdout).get("Data") or {}).get("Issues") or []]
    return {(u["kind"], u["where"]) for u in out["Data"]["Unresolved"]}, built, None


def diff(a, b, path="", out=None):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            diff(a.get(k), b.get(k), f"{path}.{k}", out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            diff(x, y, f"{path}[{i}]", out)
    elif a != b:
        out.append(path)


def new_findings(built, base_built):
    left = list(base_built)
    extra = []
    for b in built:
        if b in left:
            left.remove(b)
        else:
            extra.append(f"{b[0]} ({b[1]})")
    return extra


def measure(item, desc, mutate, seed_text, base_items, base_built, base_model, work):
    row = {"item": item, "violation": desc}
    try:
        text = mutate(seed_text)
    except (AssertionError, ValueError) as exc:
        return {**row, "verdict": "mutation-did-not-apply", "detail": str(exc)}
    doc = work / f"m{item}.md"
    doc.write_text(text, encoding="utf-8")
    code, out = uip("validate", doc)
    issues = (out.get("Data") or {}).get("Issues") or []
    if code != 0:
        codes = [i["Code"] for i in issues if i.get("Severity") == "error"]
        return {**row, "verdict": "validate", "detail": codes or (out.get("Message") or "")[:160]}
    if issues:
        return {**row, "verdict": "validate-warns", "detail": [i["Code"] for i in issues]}
    items, built, refusal = unresolved(doc, work)
    if refusal:
        return {**row, "verdict": "convert", "detail": f"refused: {refusal}"}
    row["build_validate"] = new_findings(built, base_built)
    if items - base_items:
        return {**row, "verdict": "convert", "detail": sorted({k for k, _ in items - base_items})}
    changed = []
    diff(base_model, uip("parse", doc)[1]["Data"]["Model"], "", changed)
    return {**row, "verdict": "silent", "detail": "model changes: " + ", ".join(changed[:4]) if changed else "model identical"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, help="write the rows as JSON here")
    ap.add_argument("--cli-head", default="", help="commit of the CLI build under test, recorded in --out")
    args = ap.parse_args()
    seed_text = SEED.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        code, _ = uip("validate", SEED)
        if code != 0:
            sys.exit("seed does not validate clean on this build; fix the seed choice first")
        base_items, base_built, _ = unresolved(SEED, work)
        base_model = uip("parse", SEED)[1]["Data"]["Model"]
        rows = [measure(i, d, m, seed_text, base_items, base_built, base_model, work) for i, d, m in MUTATIONS]
        rows += [{"item": i, "violation": d, "verdict": "excluded", "detail": why} for i, d, why in EXCLUDED]
        rows += [{"item": i, "violation": d, "verdict": "needs-draft", "detail": "no CLI command reads the draft"} for i, d in NEEDS_DRAFT]
    for r in rows:
        print(f"{r['item']:>3}  {r['verdict']:<22} {r['violation']:<52} {r['detail']}  build: {r.get('build_validate')}")
    tally = {v: sum(r["verdict"] == v for r in rows) for v in sorted({r["verdict"] for r in rows})}
    print(tally)
    if args.out:
        args.out.write_text(json.dumps({"cli_head": args.cli_head, "seed": str(SEED.relative_to(HERE.parents[3])),
                                        "tally": tally, "rows": rows}, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
