# Testing API Workflows — Evals & the Test-Until-Green Loop

API Workflows support dataset tests/evals: JSON `(inputs, expectedOutput)` rows run through the workflow and scored by an evaluator. Studio Web's Evaluations panel and this skill share files. The panel uses the normal debug pipeline, shows pass/fail, actual vs expected, and logs, keeps results in memory only, has no results file, and live-reloads external edits to `evals/` in local and cloud workspaces.

## 1. Eval files and contract

Use the existing scope, normally `default`:

```
<PROJECT>/evals/<SCOPE>/eval-sets/<set>.json
<PROJECT>/evals/<SCOPE>/evaluators/<evaluator>.json
<PROJECT>/evals/<SCOPE>/eval-files/                   # panel-managed uploads; leave alone
```

Studio Web creates `evals/default/...` only when enabled and the panel is first opened, seeding `exact-match-evaluator.json` and an empty `evaluation-set.json`. If `<PROJECT>/evals/` is absent, the feature is off: do not create it (SKILL.md rule 22). Preserve names, shapes, bookkeeping fields (`schemaVersion`, `target`, `fileName`, `createdAt`, `updatedAt`), and user edits; patch in place because an open panel edit wins on save.

Dataset shape:

```json
{
  "version": "1.0",
  "id": "eval-set-001",
  "name": "Dataset",
  "evaluatorRefs": ["exact-match-evaluator"],
  "evaluations": [
    {
      "id": "6f1c1b4e-2c3a-4d5e-9f10-111213141516",
      "name": "score 85 passes",
      "inputs": { "score": 85 },
      "evaluationCriterias": {
        "exact-match-evaluator": { "expectedOutput": { "grade": "PASS" } }
      }
    }
  ]
}
```

Exact-match evaluator shape:

```json
{
  "version": "1.0",
  "id": "exact-match-eval-001",
  "name": "Exact Match",
  "description": "Exact Match",
  "evaluatorTypeId": "uipath-exact-match",
  "evaluatorConfig": {
    "name": "Exact Match",
    "targetOutputKey": "*",
    "defaultEvaluationCriteria": { "expectedOutput": {} }
  }
}
```

Rules:

1. Treat `evaluatorRefs` and `evaluationCriterias` keys as evaluator file base names without `.json`, never evaluator `id` values. Do not rename referenced evaluator files. Keep one exact-match evaluator per set unless the project already has more.
2. Put expected output only in `evaluationCriterias["<ref>"].expectedOutput`; write an object shaped like the workflow output. A JSON string is tolerated and parsed, but write an object.
3. Read the project's `evaluatorTypeId`; do not assume one. Studio Web currently supports `uipath-exact-match`; honor another declared type rather than forcing exact-match.
4. `uipath-exact-match` is strict machine deep-equality: ignore key order, but require identical key names and casing, value types, and object shape. `evaluatorConfig.targetOutputKey` is `"*"` or absent for whole-output comparison, a dotted path such as `details.rawScore` for that path (while `expectedOutput` remains a full nested object), or an array for all listed paths. A path missing on either side fails. The designer does not apply `ignoreCase` or `negated`; do not rely on them.
5. Compare the workflow's raw `Response` payload, preserving casing. Wrap a bare primitive or array as `{ "result": <value> }`.
6. Patch files in place. Never regenerate or reshape UI-edited files.
7. Results are not files. Report verdicts in the conversation and never write run results under `evals/`.

## 2. Running rows from the CLI

Run the workflow with each row's inputs and extract raw output from the debug log:

```bash
uip api-workflow run <PROJECT>/Workflow.json \
  --input-arguments '<ROW_INPUTS_JSON>' \
  --no-auth --output json --log-level debug --log-file <LOG_PATH>
```

`Result: "Success"` means completion. Never compare or copy `Data`: it PascalCases every key (`grade` becomes `Grade`). Extract the last raw response from the log:

```bash
grep 'Response task evaluated successfully' <LOG_PATH> | tail -1 \
  | sed 's/^.*successfully for "[^"]*": //' \
  | python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin)["response"]))'
```

Compare that raw object with `expectedOutput` under the declared evaluator's `targetOutputKey`. A non-`Success` run is an `ERROR`, not a score. Derive expected output from `output.schema`; declare the schema first if `output: null`. The `Response` must emit exactly those keys and casing.

Run every row after each change with one outside-project comparator command:

```bash
python3 /tmp/score-evals.py <PROJECT>
```

Write the comparator outside the project, never under `evals/`. It must run `uip api-workflow run` once per row with `--input-arguments`, `--no-auth`, `--output json`, `--log-level debug`, and `--log-file`; require `Result == "Success"`; extract the last `Response task evaluated successfully` response; wrap non-object outputs as `{ "result": raw }`; match evaluator refs by file base name; require `uipath-exact-match`; require `evaluationCriterias[ref].expectedOutput`; honor `targetOutputKey` values `"*"`, dotted strings, and arrays; use strict JSON deep equality (key order ignored, shapes, casing, types, and values equal); print `[PASS]`, `[FAIL]`, or `[ERROR]` per row; and exit 0 only when at least one row exists and every verdict is `PASS`.

Inside Studio Web, ask the user to press **Run** in Evaluations, whose verdicts are authoritative. With explicit consent (SKILL.md rule 21), invoke `RunProject` once per row with that row's `inputs`; treat its host result as raw output. Derive `expectedOutput` from it or `output.schema` with exact casing.

`--no-auth` is acceptable for control-flow-only workflows and `Http` activities using `connectionId: "ImplicitConnection"`. IntSvc/vendor connector activities need auth and may cause real side effects; never run them autonomously or with auth without an explicit “yes” (SKILL.md rules 20–21).

## 3. Test-until-green protocol (SKILL.md rule 22)

Apply this protocol only when `<PROJECT>/evals/` exists. Its absence means the feature is off: skip steps 2–5 and author normally. Questions precede authoring; create or edit no workflow or eval file before the user answers. Ask the following as one numbered list. Skip steps 2–3 only if the user already answered or explicitly said “don't ask for confirmation”; that waives questions, not run consent (SKILL.md rule 21). If the request does not ask to run or loop, author once and provide the command.

1. **Discover.** Inspect `<project>/evals/`, a sibling of `Workflow.json`, not the workspace or solution root. If present, read `evals/<SCOPE>/eval-sets/*.json` and `evals/<SCOPE>/evaluators/*.json`; report row count and expectations.
2. **Ask about tests.** If rows exist, ask: *“I found an existing eval set with N test case(s) [one line each: inputs → expectedOutput]. Should anything change — add, edit or remove cases — or use them as-is?”* Apply requested changes; otherwise preserve them. If empty or only the seeded evaluator, ask: *“There are no test cases yet — want me to add some? I'd suggest: [2–3 proposed `(inputs → expectedOutput)` cases derived from the request].”* If yes, add rows and any missing evaluator using §1 shapes and raw output keys.
3. **Ask about loop mode in the same turn:**

   > “Do you want me to work in **loop mode** — run the tests and re-try (fix the workflow, re-run) until every case passes? Or author once and you verify manually?”

   End the turn. Ask on the first authoring prompt, whether creating or editing. Before the first run, ensure the workflow is in an `init`-scaffolded project (SKILL.md rules 19–19a).
4. **Author tests first, then run.** Once answered:
   1. Declare `input.schema` and `output.schema` in `Workflow.json`, including exact property casing.
   2. Write or update the eval set from those schemas.
   3. Author the workflow so `Response` emits exactly `output.schema`.
   4. In loop mode, run and score every row in one command: `python3 /tmp/score-evals.py <PROJECT>`. Loop mode consents to repeated `--no-auth` runs; authenticated or side-effecting connector runs still require their own “yes”.
   5. Use evaluator verdicts, not visual judgment. On `FAIL` or `ERROR`, first inspect keys, casing, types, and shape (`sum` vs `Sum`, missing wrapper, string vs number); fix the workflow when it violates `output.schema`, and fix a row when it contradicts requested behavior. Otherwise triage Structure > Expression > Activity Config > Logic (SKILL.md Core Principle 4), fix the workflow, and rerun.
   6. Report each iteration, for example: `iteration 2: 3/4 rows pass; fixing row 'unpaid invoice' (expected status 'unpaid', got 'paid')`.
   7. Stop when all rows pass, the user interjects, or there is no progress after a few iterations; cap the loop per Infinite Loop Prevention in SKILL.md. Always provide a per-row final summary with `PASS`/`FAIL`/`ERROR`, inputs, actual output, expected output, and error details where applicable.
   8. Stay in the main thread. Re-read `evals/` before every iteration. If a new user message changes the workflow or intent, incorporate it before scoring again.
5. **Future behavior changes.** Before editing a later behavior change, ask: *“This change would make these expectations stale: [rows]. Update them to the new behavior, or keep them and flag the mismatch?”* Then edit, rerun, and report updated rows and reasons. Pure refactors or behavior-preserving schema-only renames need no question, but rerun afterward.

## 4. Notes and gotchas

- “Yes, loop until green” authorizes repeated `--no-auth` runs only. Authenticated or side-effecting IntSvc/vendor and HTTP runs require explicit consent; every iteration can repeat side effects.
- Keep datasets synchronized with both schema and behavior. Input/output additions, removals, or renames can invalidate row shapes. Logic changes with an unchanged schema—thresholds, rounding, branch order, or defaults—can invalidate `expectedOutput`. Re-derive expectations after behavior edits; never alter the workflow merely to satisfy a stale test, and never silently rewrite user tests. Decide per row whether the workflow or expectation is authoritative and report changes.
- The project's evaluator is authoritative: read `evals/<SCOPE>/evaluators/*.json` and use its `evaluatorTypeId`.
- “The agent said it passed” is not panel evidence. PascalCased CLI `Data`, casing, and shape differences commonly hide failures; when judgments disagree, the evaluator wins.
- Studio Web and the CLI share `evals/…`. Users may edit or run rows between turns, so reread the files before each loop iteration.
