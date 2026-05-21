# `tests/tasks/uipath-review/` — prompt review

Existing test prompts vs. natural-user rewrites. Methodology in [hitl-prompts-review.html](../../hitl-prompts-review.html) and [CLAUDE.md](../../CLAUDE.md).

## Scope of this folder

The `uipath-review` skill is a **read-only auditor** for UiPath artifacts — RPA projects (.xaml/.cs), agents (.py/agent.json), flows (.flow), coded apps, and `.uipx` solutions. It enforces a discover → validate → report workflow, severity-classified findings (Critical / Warning / Info), and a strict "no file edits" rule. The two tests in this folder are a smoke (single project, generic) and an e2e (two projects with deliberately planted antipatterns).

## Insider markers seen in this folder

Both prompts share a common pattern: the user is asked to **scaffold a fixture project** with field-level `project.json` schema, then ask the skill to review it. Specific markers seen:

- **Fixture scaffolding spelled out at the schema level**: `targetFramework "Windows"`, `expressionLanguage "VisualBasic"`, `outputType "Process"`, `main "Main.xaml"`, exact dependency names (`UiPath.System.Activities`). A customer asking for a code review never recites their own `project.json` fields.
- **Skill machine-name referenced verbatim**: "Review the MyProject/ directory using the uipath-review skill" / "exercise the uipath-review skill's full discovery → validation → reporting workflow."
- **Skill-rule callbacks**: "the skill is read-only", "The skill forbids file edits", "Do not run `uip rpa debug` or any execution commands" — these restate Critical Rules from `SKILL.md` instead of letting the skill enforce them.
- **Report-shape contracts in the user voice**: "The report MUST: have a `## Findings` section, contain at least one finding with severity `Critical`, contain at least one finding with severity `Warning`, have a `## Summary` section at the end." These mirror the grader's `file_contains` checks. (The skill *does* produce this shape on its own — surfacing it to the user is harness leakage.)
- **Planted-issue tells in e2e**: "hardcoded password literal inside a LogMessage, like `Message=\"Using password 'Pa55w0rd!'\"`" and "TryCatch where the Catch block is empty — no LogMessage, no Rethrow" — the customer is told what the bugs are. A real customer would just hand over the project and say "find what's wrong."
- **Numbered Step 1 / Step 2 enumeration** in both prompts.
- **Eval-harness verb "exercise"**: "exercise the uipath-review skill's full ... workflow" — pure test-harness intent leakage.
- **Environment-state declarations**: "The `uip` CLI is already available in the environment" — a customer never says this.

What the prompts notably do **not** leak: they don't name `--output json`, don't name specific rule IDs (`ST-SEC-007`, `ST-DBP-003`), and don't dictate `uip rpa validate` vs. `uip rpa build`. Those are entirely the skill's responsibility, and the grader checks for `--output json` and `uip rpa (get-errors|validate)` independently. That's the right division.

## Verdict summary

| Verdict | Count |
|---|---|
| Insider — fixable | 0 |
| Insider — legitimate (CLI/refusal/antipattern coverage) | 0 |
| Mixed | 2 |
| Natural | 0 |

Both prompts are **Mixed**: the fixture-creation step is legitimately synthetic (a smoke/e2e grader has to materialize a project with known issues to grade against), but the **review-step language** is over-loaded with insider markers that don't need to be there. Rewrites below preserve the fixture-creation step (humanized) and naturalize the review ask.

## Per-test review

### All tests

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-review-rpa-project` (smoke) | Mixed | "Step 1 — Create a minimal RPA project at `./MyProject/` with `project.json` (name 'MyProject', targetFramework 'Windows', expressionLanguage 'VisualBasic', dependency on `UiPath.System.Activities`, outputType 'Process', main 'Main.xaml') and `Main.xaml` — a minimal Sequence containing a single LogMessage activity with text 'Hello'. Step 2 — Review the MyProject/ directory using the uipath-review skill. Do NOT modify any files in MyProject/ during the review (the skill is read-only). Produce a review report at `./review_report.md`. The report must contain: a `## Findings` section with at least one finding, severity markers for each finding (Critical, Warning, or Info), a `## Summary` section at the end. Important: The `uip` CLI is already available. Do not run `uip rpa debug`. The skill forbids file edits — only read and analyze." | "I've got a very small UiPath RPA project under `./MyProject/` — just a Sequence with one Log Message that says 'Hello'. Can you put together a quality review of it and write the findings up in `./review_report.md`? I'd like each issue called out with a severity so I know what's actually blocking vs. nice-to-have, and a short summary at the end. Don't run it or change anything in the project — just review it. (If `./MyProject/` doesn't exist yet on your sandbox, please scaffold a minimal Windows / VisualBasic RPA project there first so you have something to review.)" |
| `skill-review-multi-project-solution` (e2e) | Mixed | "You will audit a small UiPath solution with two RPA projects. The goal is to exercise the uipath-review skill's full discovery → validation → reporting workflow. Step 1 — Create the fixture at `./MySolution/` with `ProjectA/` (project.json: name 'ProjectA', targetFramework 'Windows', expressionLanguage 'VisualBasic', dependency `UiPath.System.Activities`, outputType 'Process', main 'Main.xaml' + Main.xaml: a Sequence with a hardcoded password literal inside a LogMessage like `Message=\"Using password 'Pa55w0rd!'\"`) and `ProjectB/` (similar to ProjectA + Main.xaml: a Sequence with a TryCatch where the Catch block is empty — no LogMessage, no Rethrow). Step 2 — Review `./MySolution/` using the uipath-review skill. Do NOT modify any files inside MySolution/ during review (the skill is read-only). The user has no PDD — proceed without one. Produce a structured review report at `./review_report.md`. The report MUST: have a `## Findings` section, contain at least one finding with severity 'Critical', contain at least one finding with severity 'Warning', mention the hardcoded password or 'credential' issue in ProjectA (Critical severity), mention the empty Catch block or 'swallow' issue in ProjectB (Warning severity), have a `## Summary` section at the end. Important: The `uip` CLI is already available. Do not run `uip rpa debug`. Do not modify files in MySolution/. Discover both projects before reviewing either one." | "We've inherited a small UiPath solution under `./MySolution/` — two RPA projects sitting side by side (`ProjectA/` and `ProjectB/`). Before we hand it off to ops I'd like a proper quality audit: walk both projects, flag whatever looks risky, and write the whole thing up in `./review_report.md` with severities so we can prioritize. There's no PDD, so this is purely a technical review — and please don't touch the project files, just review them. (For setup: if `./MySolution/` isn't already on disk, please scaffold the two RPA projects so the review has something to chew on. To make the audit realistic, give `ProjectA` a Main.xaml that logs a password in plaintext, and give `ProjectB` a Main.xaml with an empty TryCatch — those are exactly the kinds of issues we're trying to catch.)" |

## Notes for the PR description

- **The folder is consistent**: both prompts use the same "scaffold a fixture, then ask the skill to review it" template, with the same insider tells. Fix one, fix both — the patterns to remove (verbatim `project.json` schema, skill machine-name, "the skill is read-only", report-shape contracts, "exercise the workflow") repeat across both files.
- **The grader does *not* depend on most of the insider language.** The `file_contains` checks need the words "Findings", "Critical", "Warning", "Summary", "ProjectA", "password", "ProjectB", "Catch" to appear in `review_report.md` — but the **skill itself produces those sections and labels by design** (see `SKILL.md` "Required report structure"). The prompt does not need to dictate them; doing so just teaches the agent to copy-paste headings instead of running the skill.
- **The `--output json` and `uip rpa validate` checks are well-designed**: the grader checks the agent's tool-call pattern, not the user-prompt wording, so the prompt is correctly silent on those flags. This is a good split — keep it.
- **The "planted issue" telegraphing in the e2e is the biggest fidelity hit.** Telling the user-voice prompt that ProjectA contains a `'Pa55w0rd!'` literal and ProjectB contains an empty Catch lets the agent shortcut the entire review by string-searching for those tokens instead of actually running validation + analyzer. The fixture-creation step still has to specify the planted issues (the grader needs them), but the **review-step ask** should treat the issues as unknown. The rewrites above split fixture-creation from the review ask explicitly, in parentheses, signalling that the planted detail is sandbox plumbing, not part of the user's question.
- **Both tests are flagged as `e2e` / `smoke` and use a `tempdir` sandbox.** Wrapping the fixture-creation in a parenthetical "if it isn't already on disk, please scaffold..." preserves the test's ability to run on a clean tempdir while letting the review ask sound like the user pointing at an existing project.
