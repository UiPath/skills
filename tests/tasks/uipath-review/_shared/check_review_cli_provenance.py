#!/usr/bin/env python3
"""Prove the review CLI ran, from the REPORT instead of from command telemetry.

Replaces a `command_executed` criterion on `uip\\s+agent\\s+review`. That form
asks the harness "did a Bash tool call match this regex", and the answer depends
on things the agent's actual work does not:

* coder_eval matches the pattern against only the first 2000 chars of the
  command (`criteria/command_executed.py::_MAX_PATTERN_SEARCH_LEN`, a ReDoS
  guard). Agents batch many commands into one `bash -lc` script, so a CLI call
  late in a long script is simply invisible. Whether it lands inside the window
  is a function of how much unrelated preamble the agent happened to emit.
* `require_success: true` reads the *wrapper's* exit code
  (`agents/codex_agent.py`), and a batched script that opens `set +e` and closes
  `exit 0` always reports success -- even if the CLI inside it failed.

Both failure modes are independent of whether the agent did the work, in both
directions. So derive ground truth instead: re-run the review CLI on the fixture
(which the task's gating read-only criteria prove the agent did not modify) and
require the report to carry the deterministic `RuleId`s it emits.

How strong that evidence is depends on the rule_id, and the checker measures it
rather than assuming: an id that appears NOWHERE in the agent-readable skill
tree (e.g. `LOWCODE_EVAL_SET_EMPTY`) can only have come from running the CLI, so
citing it verbatim proves invocation. An id the skill itself names (e.g.
`CODED_GUARDRAIL_WRONG_IMPORT`, documented in SKILL.md and
`references/agents/agents-coded-rules.md`) could in principle be cited by an
agent that read the source and skipped the CLI -- there the check still verifies
the CLI genuinely emits that finding and that the report carries it verbatim per
Step 2.5a, but it is not proof of invocation. A WARN names that case explicitly
so the criterion detail never overstates what it established.

Exit 0 on PASS; sys.exit(str) on failure.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from report_evidence import cli_identity, declares_unavailable

# Names the report may use for the review CLI, for the shared
# `declares_unavailable` contract check (SKILL.md Critical Rule 11).
REVIEW_CLI_SUBJECT = r"review\s+CLI|uip\s+agent\s+review|uip\s+codedagent\s+review"

# Anchors that attribute a nearby grade letter to the CLI rather than to the
# skill's own judgment grade (the two legitimately differ -- Step 4.5 takes
# min(G_det, G_jud)).
CLI_MENTION = re.compile(r"(uip\s+agent\s+review|uip\s+codedagent\s+review|review\s+CLI|deterministic)", re.IGNORECASE)
GRADE_PROXIMITY = 240


def _run_cli(uip: str, verb: list[str], project: str) -> tuple[bool, dict, str]:
    """Run the review CLI on `project`; return (ok, parsed Data, diagnostic)."""
    argv = [uip, *verb, project, "--output", "json"]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=180)
    except FileNotFoundError:
        return False, {}, f"{uip} not on PATH"
    except subprocess.TimeoutExpired:
        return False, {}, f"{' '.join(argv)} timed out after 180s"
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip()[-400:]
        return False, {}, f"exit {proc.returncode}: {tail}"
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return False, {}, f"non-JSON output ({e}): {proc.stdout.strip()[:400]}"
    if payload.get("Result") != "Success":
        return False, {}, f"Result={payload.get('Result')}: {payload.get('Message', '')[:400]}"
    return True, payload.get("Data") or {}, ""


def _derivable_from_skill(rule_ids: list[str]) -> list[str] | None:
    """Which `rule_ids` the agent could have read out of the skill tree.

    Only the agent-READABLE tree counts: `$TASK_DIR` is chmod-000 during the
    agent turn, and `tests/runs/` is gitignored scratch that does not exist in a
    clean checkout, so neither is a source the agent could have used.
    """
    repo = os.environ.get("SKILLS_REPO_PATH")
    if not repo:
        return None
    skills = Path(repo) / "skills" / "uipath-review"
    if not skills.is_dir():
        return None
    text = ""
    for f in skills.rglob("*.md"):
        try:
            text += f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
    return [r for r in rule_ids if r in text]


def _grade_evidenced(text: str, grade: str) -> bool:
    """True if `grade` appears as a standalone token near a CLI attribution."""
    letter = re.compile(rf"(?<![A-Za-z]){re.escape(grade)}(?![A-Za-z])")
    for m in CLI_MENTION.finditer(text):
        window = text[max(0, m.start() - GRADE_PROXIMITY) : m.end() + GRADE_PROXIMITY]
        if letter.search(window):
            return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="ReviewSol/SampleAgent")
    ap.add_argument("--report", default="_review_report.md")
    ap.add_argument(
        "--verb",
        default="agent review",
        help="CLI verb: 'agent review' (low-code) or 'codedagent review' (coded).",
    )
    args = ap.parse_args()

    report = Path(os.getcwd()) / args.report
    if not report.is_file():
        sys.exit(f"FAIL: {report} not found")
    text = report.read_text(encoding="utf-8", errors="replace")

    uip = os.environ.get("UIP", "uip")
    print(f"Checker resolved `{uip}` -> {cli_identity(uip)}")
    ok, data, why = _run_cli(uip, args.verb.split(), args.project)

    if not ok:
        # Ground truth is unobtainable. Do not silently pass (that is the hole
        # this check exists to close) and do not hard-fail on infra (that just
        # trades one flake for another): hold the report to the contract the
        # skill defines for exactly this case.
        print(f"WARN: could not establish ground truth -- `{uip} {args.verb}` unavailable ({why})")
        if declares_unavailable(text, REVIEW_CLI_SUBJECT):
            print("OK: report declares the review CLI unavailable under 'Rules Skipped'")
            print("PASS")
            return
        sys.exit(
            f"FAIL: the review CLI could not be run at check time ({why}), and the report does "
            "not declare it unavailable under 'Rules Skipped'. Either the CLI was skipped, or "
            "the harness lost CLI access -- both need a human look."
        )

    grade = str(data.get("Grade") or "")
    score = data.get("Score")
    rule_ids = sorted({str(i.get("RuleId")) for i in (data.get("Issues") or []) if i.get("RuleId")})
    print(f"Ground truth from `{uip} {args.verb} {args.project}`: Grade={grade} Score={score} Issues={rule_ids}")

    if rule_ids:
        missing = [r for r in rule_ids if r not in text]
        if missing and declares_unavailable(text, REVIEW_CLI_SUBJECT):
            # The report claims the CLI was unavailable, but this checker just
            # ran it. Either the agent resolved a DIFFERENT `uip` (a host with
            # several installs plus a login shell / per-task HOME will do this),
            # or the claim is false. Both are real problems and neither may pass
            # -- accepting the declaration unconditionally would let any agent
            # skip Step 2.5a by writing one line. Name the likelier cause so the
            # environment can be checked first.
            sys.exit(
                f"FAIL: report declares the review CLI unavailable under 'Rules Skipped', but this "
                f"checker ran it successfully via {cli_identity(uip)} and got {missing}. Either the "
                f"agent resolved a different `uip` than the checker (compare `which -a uip`; a login "
                f"shell or a per-task HOME from sandbox.mock_path_dirs can pick a stale one), or the "
                f"report's unavailability claim is false. Fix the environment before reading this as "
                f"a skill regression."
            )
        if missing:
            sys.exit(
                f"FAIL: report omits deterministic rule_id(s) the review CLI emitted: {missing}. "
                "These appear in no judgment catalog, so the report cannot have been produced "
                "from a run that executed the CLI (SKILL.md Critical Rule 9 / Step 2.5a requires "
                "carrying every CLI finding verbatim)."
            )
        print(f"OK: report carries every CLI-emitted rule_id verbatim: {rule_ids}")
        derivable = _derivable_from_skill(rule_ids)
        if derivable is None:
            pass  # no SKILLS_REPO_PATH: cannot judge strength, so claim nothing
        elif derivable:
            print(
                f"WARN: {derivable} also appear(s) in the agent-readable skill tree, so citing them "
                "does not by itself prove the CLI ran -- this criterion verifies the CLI emits them "
                "and the report carries them verbatim, not that the agent invoked it."
            )
        elif rule_ids:
            print(f"OK: {rule_ids} appear nowhere in the skill tree -- citation proves the CLI ran")
    else:
        # Nothing deterministic to carry, so fall back to the other CLI-only
        # facts. Keep this branch: sibling fixtures can legitimately be clean.
        if not (grade and _grade_evidenced(text, grade)) and not (score is not None and str(score) in text):
            sys.exit(
                f"FAIL: the review CLI returned no findings, and the report evidences neither its "
                f"grade ({grade!r}) nor its score ({score!r}) -- no trace that Step 2.5a ran."
            )
        print(f"OK: CLI returned no findings; report evidences its grade/score (Grade={grade} Score={score})")

    if grade and not _grade_evidenced(text, grade):
        # Step 4.5 reads G_det from the CLI; the report format only *requires*
        # printing it when it differs from the final grade, so this is a signal,
        # not a gate.
        print(f"WARN: report does not attribute grade {grade} to the review CLI near a CLI mention")

    print("PASS")


if __name__ == "__main__":
    main()
