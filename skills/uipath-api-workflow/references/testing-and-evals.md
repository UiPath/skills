# Testing API Workflows — Evals & the Test-Until-Green Loop

API Workflows have a **dataset-test / eval** capability: a set of `(inputs, expectedOutput)` rows the workflow is run against and scored by exact-match. The dataset lives as **plain JSON files in the project** (Unified Eval layout), so it is shared between:

- the **StudioWeb designer** — an "Evaluations" section at the bottom of the API-workflow canvas (local workspace only) that runs each row at debug and shows pass/fail + output + logs, and
- **this skill / an agent** — which drives the same files headlessly via `uip api-workflow run`.

Because the tests are files, the agent can author them, run them, read results, fix the workflow, and repeat — a **test-until-green loop**.

---

## 1. The eval files (the contract)

All under the project's `evals/` folder. Match these shapes exactly (they are the UiPath Unified Eval format).

**`evals/eval-sets/default.json`** — the dataset:
```jsonc
{
  "version": "1.0",
  "id": "default",
  "name": "Evaluations",
  "evaluatorRefs": [ "ApiWfExactMatch" ],
  "evaluations": [
    {
      "id": "<uuid-or-stable-id>",
      "name": "case 1",
      "inputs": { "invoiceId": "A-100" },
      "evaluationCriterias": {
        "ApiWfExactMatch": { "expectedOutput": { "total": 250, "status": "paid" } }
      }
    }
  ]
}
```

**`evals/evaluators/exact-match.json`** — how to score:
```jsonc
{
  "version": "1.0",
  "id": "ApiWfExactMatch",
  "description": "Exact match of the workflow output against the expected output.",
  "evaluatorTypeId": "uipath-exact-match",
  "evaluatorConfig": {
    "name": "ApiWfExactMatch",
    "targetOutputKey": "*",
    "ignoreCase": false,
    "negated": false,
    "defaultEvaluationCriteria": { "expectedOutput": {} }
  }
}
```

**`evals/eval-runs/last-run.json`** — results (written after each run; overwritten):
```jsonc
{
  "version": "1.0",
  "ranAt": "<ISO timestamp>",
  "setId": "default",
  "rows": [
    { "rowId": "…", "name": "case 1", "inputs": {…}, "expectedOutput": {…},
      "actualOutput": {…}, "verdict": "pass|fail|error", "error": "…",
      "logs": [ { "type": "task_completed", "name": "HTTP Request", "executionTimeMs": 464, "output": {…} } ] }
  ]
}
```

**Rules.**
- Expected output goes in `evaluationCriterias["ApiWfExactMatch"].expectedOutput`, **not** at the row top level.
- `targetOutputKey: "*"` compares the **whole** workflow output object; a named key compares just `output[key]`.
- Exact-match semantics: structural deep-equal (key order irrelevant), optional `ignoreCase` for string values, optional `negated` to invert. Match these when you compute a verdict so it agrees with the designer/backend.
- The workflow's "output" for comparison is the whole-workflow output — the same object `uip api-workflow run … --output json` returns (Orchestrator-`OutputArguments`-shaped: a bare primitive/array is wrapped `{ "result": <value> }`).
- Only **local workspace** projects use these files (the designer panel is local-only). Keep them in the project so they travel with it and are agent/CLI-readable.

---

## 2. Running a test row from the CLI

Run the workflow with a row's inputs and compare the output to its expected output:

```bash
uip api-workflow run <workflow.json> \
  --input-arguments '<row.inputs as JSON>' \
  --no-auth --output json
```

- `--no-auth` is fine for control-flow-only workflows and `Http` kind activities using `connectionId: "ImplicitConnection"`. **IntSvc (vendor connector) activities need auth** — those runs have real side effects (emails sent, tickets created). See rules 20–21 in SKILL.md: never run autonomously, and never run with auth without an explicit "yes".
- Parse the JSON output, extract the workflow result, and exact-match it against `expectedOutput` (per §1).
- Write/refresh `evals/eval-runs/last-run.json` with each row's `actualOutput` + `verdict` (+ `error`). The designer's "Evaluations" panel loads this file **on open** (it live-reloads the dataset — eval-sets/evaluators — but not the results file), so CLI-written results show up the next time the panel is opened, and always to the user via the file itself.

---

## 3. The test-until-green loop (interactive protocol)

**Ask before each fork — do not assume.** Steps 1–2 are the two mandatory up-front questions; ask BOTH immediately after Phase-0 discovery and BEFORE writing/editing the workflow. Do not defer them to after authoring, and do NOT collapse them into a vague "how do you want to verify it?" prompt — that skips the update-tests decision and hides the loop-vs-once choice. Ask these two specific questions:

1. **Tests — decide during discovery, as soon as you've read the `evals/` folder:**
   - **Eval set exists** (`evals/eval-sets/default.json` present) → ask: *"I found an existing eval set with N test case(s). Before I start — should I update/add cases, or use them as-is?"* Apply requested changes, else keep as-is. Ask this the moment discovery finds the tests — it is not gated behind the loop-mode answer.
   - **No eval set** → ask: *"There are no tests yet — want me to create some?"* If yes, elicit `(inputs, expectedOutput)` cases from the user (or propose them from the workflow's input/output schema for confirmation) and write `evals/eval-sets/default.json` + `evals/evaluators/exact-match.json` in the §1 shapes.

2. **Loop mode — ask the intent literally, right after the tests question:**
   > "Do you want me to work in **loop mode** — re-author the workflow and re-run the evals until every case passes (test-driven)? Or author once and you verify manually?"

   "Loop mode" = TDD: author → run evals → fix → repeat until green (step 3). Ask this proactively on the first authoring prompt (create OR edit); you do not need the workflow to exist yet, only the intent to author one. If the user declines, proceed with normal authoring and don't re-ask every turn; a later explicit "test this" / "run until it passes" re-enters here. Before the first run, ensure the workflow actually exists (init/build if necessary — see rules 19–19a).

3. **Run the loop** (respecting the auth/consent rules in §2):
   - For each row: run it (§2), capture output, compute the verdict.
   - **All pass** → stop; report the green result and where `last-run.json` is.
   - **Any fail/error** → triage the failure (Structure > Expression > Activity Config > Logic — see SKILL.md Core Principle 4), **fix the workflow**, then re-run. Repeat.
   - **Report progress each iteration** — e.g. "iteration 2: 3/4 rows pass; fixing row 'unpaid invoice' (expected status `unpaid`, got `paid`)".
   - **Stop conditions:** all green; OR no progress after a few iterations (don't loop forever — cap it, like the Infinite Loop Prevention rule); OR the user interjects. Always leave `last-run.json` reflecting the final state.

4. **Concurrency / interruptibility (optional but preferred):** run the run-and-await portion in a **background subagent** so the main thread stays responsive and can report progress. **If a new user message arrives that changes the workflow or the intent, stop/kill the in-flight test subagent, incorporate the change, then restart the loop.** Never keep scoring against a workflow the user has just asked you to change.

---

## 4. Notes & gotchas

- **Consent is the loop's gate.** The user's "yes, loop until green" authorizes repeated `--no-auth` runs. For workflows whose activities have side effects (IntSvc/vendor, or authed HTTP), call that out and get explicit consent before looping — each iteration re-triggers the side effect.
- **Keep the dataset in sync with the schema.** If you change the workflow's input/output arguments, the rows' `inputs`/`expectedOutput` may need updating — offer to update the eval set.
- **Same files, two front-ends.** A user may have authored or run these evals in the StudioWeb "Evaluations" panel; your CLI runs and their UI runs share `evals/…`. Don't reshape the files — read/patch them in place.
- **Exact-match only (today).** The v1 evaluator is `uipath-exact-match`. Fuzzy/LLM-judge evaluators exist in the Unified catalog but are not part of this local loop.
