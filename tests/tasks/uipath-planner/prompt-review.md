# `tests/tasks/uipath-planner/` — prompt review

Existing test prompts vs. natural-user rewrites. Methodology in [hitl-prompts-review.html](../../hitl-prompts-review.html) and [CLAUDE.md](../../CLAUDE.md).

## Scope of this folder

The `uipath-planner` skill is the upstream task planner — it reads SDDs from `uipath-solution` or elicits non-PDD requests, derives multi-skill task lists, and emits live `TaskCreate` calls. It has two lanes — **Lane A (PDD-driven)** and **Lane B (Non-PDD)** — and explicitly does not execute work itself. This folder currently contains a single smoke test that exists only to verify the skill body actually got loaded into the agent's context.

## Insider markers seen in this folder

- **Skill-activation probe**: prompt asks the agent to "Load the appropriate UiPath skill for this work" — a skill-rule callback.
- **Verbatim-token extraction**: instructs the agent to echo "the EXACT names of the two lanes the planner defines" — a known SKILL.md-only string (`Lane A — PDD-driven` / `Lane B — Non-PDD`) used as proof of activation.
- **Internal tool name named in user voice**: `Do NOT call AskUserQuestion` — `AskUserQuestion` is a specific internal Claude tool the planner uses for elicitation, not something a customer would name.
- **Eval-harness verbs stacked**: `Do NOT analyze any document. Do NOT generate any plan or tasks file. Do NOT ask me clarifying questions. Do NOT call AskUserQuestion.` followed by `Stop after writing lanes.txt.`
- **Eval-grader file contract**: `write to lanes.txt … one per line`.

## Verdict summary

| Verdict | Count |
|---|---|
| Insider — fixable | 0 |
| Insider — legitimate (CLI/refusal/antipattern coverage) | 1 |
| Mixed | 0 |
| Natural | 0 |

## Per-test review

### All tests

| Test | Verdict | Existing prompt (gist) | Recommended natural-user rewrite |
|---|---|---|---|
| `skill-planner-smoke-skill-activation` | Insider — legitimate | "Help me plan a UiPath solution from scratch — a multi-step process that spans several skills. Load the appropriate UiPath skill for this work. Do NOT analyze any document. Do NOT generate any plan or tasks file. Do NOT ask me clarifying questions. Do NOT call AskUserQuestion. After loading the skill, write to `lanes.txt` the EXACT names of the two lanes the planner defines, one per line. Use the names exactly as they appear in the skill body. Stop after writing `lanes.txt`." | _Keep as-is — this is an activation smoke test. Its entire purpose is to verify that `uipath-planner`'s SKILL.md was loaded into context, which it proves by extracting tokens (`Lane A — PDD-driven` / `Lane B — Non-PDD`) that only exist in the skill body. The `Do NOT` block exists because the planner would otherwise immediately call `AskUserQuestion` (Lane B Step 1), generate a plan, and burn the test; suppressing planner behaviour to isolate "did the body load" is the right call here. The `lanes.txt` file write is the eval grader's contract._ One small nit: the natural-sounding lead-in ("Help me plan a UiPath solution from scratch — a multi-step process that spans several skills.") is doing the activation-trigger work, and it reads fine as customer phrasing, so the prompt's existing two-layer shape (natural trigger + harness scaffolding) is actually well-designed. |

## Notes for the PR description

- **Single-test folder, and that test is the right kind of insider.** Activation smoke tests are an established harness pattern — their job is to prove the skill body got loaded, not to measure planning judgment. The author got the shape right: a natural-sounding opening that legitimately triggers the planner skill, followed by an explicit "don't run the workflow, just prove you loaded" block.
- **The activation token is well-chosen.** The two lane names appear verbatim in `SKILL.md` (`Lane A — PDD-driven`, `Lane B — Non-PDD`) and aren't fabricatable from general UiPath knowledge — a model that didn't load the body genuinely cannot produce them. Compare to weaker activation probes that ask for tokens any well-trained model could guess.
- **Folder coverage is thin.** Only one test exists for a skill with two lanes, an Entry Guard, a PDD hard-block, a 5-`AskUserQuestion` cap, and a mandatory-Testing-task rule. Future tests that exercise the **judgment** side of the planner (e.g. "here's a PDD path — what do you do?" expecting the hard-block to `uipath-solution`; or "here's an ambiguous request — does the agent batch its elicitation properly?") would be valuable, and those should be written in natural customer voice without the activation-test scaffolding.
- **Naming is good** — `skill-planner-smoke-skill-activation` follows the same `skill-<name>-<lifecycle>-<purpose>` pattern seen in `uipath-tasks` and is unambiguous about what the test does.
