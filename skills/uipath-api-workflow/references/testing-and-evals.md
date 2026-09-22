# Testing API Workflows — Evals & the Test-Until-Green Loop

API Workflows have a **dataset-test / eval** capability: a set of `(inputs, expectedOutput)` rows the workflow is run against, each scored by an evaluator. The dataset is **plain JSON files inside the project** (`evals/…`), so it is shared between:

- **Studio Web's designer** — the **Evaluations** panel in the bottom dock of an API-workflow project (local *and* cloud workspaces; feature-flagged). It runs each row through the normal debug pipeline, scores it, and shows pass/fail, actual vs expected, and the run's logs. Results live in memory only — there is **no results file**.
- **This skill / an agent** — which authors the same files, runs the rows headlessly with `uip api-workflow run`, scores them the same way, and reports.

Because the tests are files, the agent can author them, run them, fix the workflow, and repeat — a **test-until-green loop**. The panel live-reloads external edits to `evals/` (local: file watcher; cloud: file-system notifications), so what you write shows up there.

---

## 1. The eval files (the contract)

```
<PROJECT>/evals/<SCOPE>/eval-sets/<set>.json          # datasets — one file per eval set
<PROJECT>/evals/<SCOPE>/evaluators/<evaluator>.json   # scorers — one file per evaluator
<PROJECT>/evals/<SCOPE>/eval-files/                   # panel-managed uploads — leave alone
```

`<SCOPE>` is `default` unless the project already uses another one. Studio Web creates the folder when the Evaluations feature is enabled and the panel is first opened, seeding `evals/default/evaluators/exact-match-evaluator.json` and an empty `evals/default/eval-sets/evaluation-set.json`. **A project without an `evals/` folder has the feature turned off — leave it that way (SKILL.md rule 22).** When you add rows or files inside an existing folder, use the same names and shapes.

**`evals/default/eval-sets/evaluation-set.json`** — the dataset:

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

**`evals/default/evaluators/exact-match-evaluator.json`** — how rows are scored:

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

**Rules.**

1. **Refs are file base names, not ids.** Every entry of `evaluatorRefs` and every key of a row's `evaluationCriterias` is the evaluator's **file name without `.json`** (`exact-match-evaluator` above) — not its `id`. Renaming the evaluator file orphans every row ("No expected output could be matched to this evaluator" → fail). Keep one exact-match evaluator per set unless the project already has more.
2. **Expected output goes in `evaluationCriterias["<ref>"].expectedOutput`**, never at the row top level. It is an object shaped like the workflow output (a JSON string is tolerated and parsed, but write an object).
3. **Score with the evaluator the PROJECT declares — read `evaluatorTypeId`, don't assume.** Studio Web's panel supports exactly one type today, **`uipath-exact-match`**; if a project ever declares another, honor it instead of forcing exact-match.
4. **`uipath-exact-match` is a strict machine deep-equal, not a "looks right" judgment.** Key order is ignored; **key names, their exact casing, value types, and object shape must all equal the workflow's RAW output**. `{ "sum": 5 }` ≠ `{ "Sum": 5 }` → fail, even though the number is right. `evaluatorConfig.targetOutputKey` picks what is compared: `"*"` (or absent) compares the whole output object with the whole `expectedOutput`; a dotted path such as `details.rawScore` compares `output.details.rawScore` with `expectedOutput.details.rawScore` (so `expectedOutput` stays a full nested object); an array compares every listed path. A path missing on both sides is a **fail**, not a vacuous pass. `ignoreCase` / `negated` are not applied by the designer — don't rely on them.
5. **"Output" means the workflow's Response payload, raw.** Original key casing, as the `Response` expression produces it. A bare primitive or array is wrapped as `{ "result": <value> }`.
6. **Patch the files in place.** The panel adds bookkeeping fields (`schemaVersion`, `target`, `fileName`, `createdAt`, `updatedAt`) — keep whatever is there, never reshape or regenerate a file the user may have edited in the UI. An open edit form in the panel still wins on save (last writer wins).
7. **Results are not files.** Report verdicts in the conversation; do not write run results under `evals/` — nothing reads them.

---

## 2. Running a test row from the CLI

Run the workflow with the row's inputs, then read the **raw** output from the debug log:

```bash
uip api-workflow run <PROJECT>/Workflow.json \
  --input-arguments '<ROW_INPUTS_JSON>' \
  --no-auth --output json --log-level debug --log-file <LOG_PATH>
```

- `Result: "Success"` means the run completed; `Data` is the output **with every key PascalCased** (`grade` → `Grade`, `details.rawScore` → `Details.RawScore`). **Never compare against or copy from `Data`** — a row derived from it passes for you and fails in the panel (this is the `sum` vs `Sum` failure).
- The raw output is the `response` of the last `Response task evaluated successfully for "<key>": {…}` line in the log file:

  ```bash
  grep 'Response task evaluated successfully' <LOG_PATH> | tail -1 \
    | sed 's/^.*successfully for "[^"]*": //' \
    | python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin)["response"]))'
  ```

- Deep-equal that object against the row's `expectedOutput` under the evaluator's `targetOutputKey` (§1 rule 4). A run whose `Result` is not `Success` is an **error** verdict — triage it, don't score it.
- **Derive `expectedOutput` from `output.schema`** (exact property names and casing) — declare the schema first if the project has none (`init` leaves `output: null`); the Response must emit exactly those keys. Mismatched keys/casing here is the usual reason "the agent said it passed" while every row fails in the panel.

**Batch comparator — score every row in one command.** Do not eyeball outputs and do not hand-roll a comparison per row: write this once to a file **outside the project** (e.g. `/tmp/score-evals.py` — never under `evals/`, the panel reads that folder) and run it after each change. It mirrors the panel: raw output from the debug log, strict deep-equal under the evaluator's `targetOutputKey`, refs matched as file base names.

```python
#!/usr/bin/env python3
"""score-evals.py <project-dir>: run every eval row with `uip api-workflow run --no-auth` and
score it like Studio Web's Evaluations panel (uipath-exact-match, strict deep-equal on the RAW
output). Exit 0 only when every row passes."""
import json, re, subprocess, sys, tempfile
from pathlib import Path

LINE = re.compile(r'Response task evaluated successfully for "[^"]*": (\{.*\})\s*$')

def run(wf, inputs):
    log = tempfile.NamedTemporaryFile(suffix=".log", delete=False).name
    p = subprocess.run(["uip", "api-workflow", "run", str(wf), "--input-arguments", json.dumps(inputs),
                        "--no-auth", "--output", "json", "--log-level", "debug", "--log-file", log],
                       capture_output=True, text=True, timeout=120)
    try:
        env = json.loads(p.stdout)
    except json.JSONDecodeError:
        return None, f"non-JSON CLI output: {p.stdout[:200]}"
    if env.get("Result") != "Success":
        return None, f"run failed: {env.get('Message')}"
    raw = None
    for line in Path(log).read_text(errors="replace").splitlines():
        m = LINE.search(line)
        if m:
            raw = json.loads(m.group(1)).get("response")
    return (raw if isinstance(raw, dict) else {"result": raw}), None

def eq(a, e):  # lodash isEqual for JSON: bool != number, key order ignored, shapes must match
    if isinstance(a, bool) or isinstance(e, bool):
        return isinstance(a, bool) and isinstance(e, bool) and a == e
    if isinstance(a, dict) and isinstance(e, dict):
        return a.keys() == e.keys() and all(eq(a[k], e[k]) for k in a)
    if isinstance(a, list) and isinstance(e, list):
        return len(a) == len(e) and all(eq(x, y) for x, y in zip(a, e))
    if isinstance(a, (int, float)) and isinstance(e, (int, float)):
        return a == e
    return type(a) is type(e) and a == e

def at(v, path):
    for seg in [s for s in path.split(".") if s]:
        if not isinstance(v, dict) or seg not in v:
            return KeyError
        v = v[seg]
    return v

def match(actual, expected, target):
    if isinstance(target, list):
        return bool(target) and all(match(actual, expected, t) for t in target)
    if isinstance(target, str) and target not in ("", "*"):
        a, e = at(actual, target), at(expected, target)
        return a is not KeyError and e is not KeyError and eq(a, e)
    return eq(actual, expected)

project = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
evaluators = {p.stem: json.loads(p.read_text()) for p in project.glob("evals/*/evaluators/*.json")}
ok_all, n = True, 0
for set_path in sorted(project.glob("evals/*/eval-sets/*.json")):
    es = json.loads(set_path.read_text())
    for row in es.get("evaluations", []):
        actual, err = run(project / "Workflow.json", row.get("inputs") or {})
        for ref in es.get("evaluatorRefs", []):
            n += 1
            ev, crit = evaluators.get(ref), (row.get("evaluationCriterias") or {}).get(ref)
            label = f"{set_path.name} :: {row.get('name') or row.get('id')} ({ref})"
            if ev is None or ev.get("evaluatorTypeId") != "uipath-exact-match":
                verdict, detail = "ERROR", f"evaluator {ref!r} missing or not uipath-exact-match (refs are file base names)"
            elif not isinstance(crit, dict) or "expectedOutput" not in crit:
                verdict, detail = "ERROR", f"no evaluationCriterias[{ref!r}].expectedOutput"
            elif err:
                verdict, detail = "ERROR", err
            else:
                exp = crit["expectedOutput"]
                exp = json.loads(exp) if isinstance(exp, str) else exp
                target = (ev.get("evaluatorConfig") or {}).get("targetOutputKey", "*")
                verdict = "PASS" if match(actual, exp, target) else "FAIL"
                detail = f"actual={json.dumps(actual)} expected={json.dumps(exp)}"
            ok_all &= verdict == "PASS"
            print(f"[{verdict:5}] {label} inputs={json.dumps(row.get('inputs'))} {detail}")
sys.exit(0 if n and ok_all else 1)
```

Run it as the whole iteration: `python3 /tmp/score-evals.py <PROJECT>` — one tool call, every row, panel-equivalent verdicts.
- **Inside Studio Web** (no local CLI): rows run through the host instead — ask the user to press **Run** in the Evaluations panel (its verdicts are authoritative), or, with explicit consent (rule 21), invoke `RunProject` once per row with that row's `inputs`; the host result is the raw output. Derive `expectedOutput` from it or from `output.schema`, exactly as above.
- `--no-auth` is fine for control-flow-only workflows and `Http` activities using `connectionId: "ImplicitConnection"`. **IntSvc (vendor connector) activities need auth** and have real side effects (emails sent, tickets created) — rules 20–21 in SKILL.md apply: never run autonomously, never with auth without an explicit "yes".

---

## 3. The test-until-green loop (interactive protocol)

This is SKILL.md **rule 22**, and it applies **only to projects that have an `evals/` folder** — its absence means the Evaluations feature is not enabled for the project, so steps 2–5 are skipped and the workflow is authored normally. Where it applies it is test-driven development: the questions come before any authoring, the eval set is written **before** the workflow, and the workflow is then authored to make the rows pass. The turn **ends** at step 3 — the workflow is not written or edited, and no eval file is created, until the user has answered. Ask the questions as written, one numbered list, never a vague "how do you want to verify it?". With `evals/` present, skip steps 2–3 only when the user already answered or explicitly asked not to be prompted ("don't ask for confirmation"); then keep an existing eval set as-is and add tests only if they were requested. "Don't ask" waives the questions, not the run consent (SKILL.md rule 21): run the rows only when the request itself asks for a run or a loop ("run the evaluations", "fix it until every case passes"); otherwise author once and hand over the command to run them.

1. **Look for the `evals/` folder** (Phase 0 discovery) — `<project>/evals/`, a sibling of `Workflow.json` inside the project directory; list that directory, not the workspace or solution root. **Absent → stop here:** the feature is off for this project; no test or loop-mode question, no folder creation — author normally. Present → read `evals/<SCOPE>/eval-sets/*.json` and `evals/<SCOPE>/evaluators/*.json` (§1) and note the row count and what the rows expect.

2. **Ask about the tests:**
   - **Eval set has rows** → *"I found an existing eval set with N test case(s) [one line each: inputs → expectedOutput]. Should anything change — add, edit or remove cases — or use them as-is?"* Apply requested changes, else keep as-is.
   - **Eval set is empty** (or the folder holds only the seeded evaluator) → *"There are no test cases yet — want me to add some? I'd suggest: [2–3 proposed `(inputs → expectedOutput)` cases derived from the request]."* If yes, add the rows (and the evaluator if missing) in the §1 shapes (raw output keys — §2).

3. **Ask about loop mode — in the same turn, right after question 2:**
   > "Do you want me to work in **loop mode** — run the tests and re-try (fix the workflow, re-run) until every case passes? Or author once and you verify manually?"

   Then **end the turn**. Ask on the first authoring prompt, create OR edit; the workflow need not exist yet. If the user declines, author normally and don't re-ask every turn; a later "test this" / "run until it passes" re-enters here. Before the first run, make sure the workflow lives in an `init`-scaffolded project (rules 19–19a).

4. **Author tests-first, then run the loop** once the user has answered. Order matters because `uip api-workflow init` scaffolds `input: null` / `output: null` — there is nothing to derive row keys from until you write it:
   1. **Declare `input.schema` and `output.schema` in `Workflow.json`** — the property names and their exact casing. This is the contract both the rows and the Response follow (`grade`, not `Grade`).
   2. **Write/update the eval set** (§1), deriving every `inputs` key and `expectedOutput` key from those schemas.
   3. **Author the workflow** so the Response emits exactly the `output.schema` keys.
   4. **Run** — in loop mode, which is also the consent for `--no-auth` runs (connector/authed runs still need their own "yes", §2) — iterate:
   - **One iteration = one command.** Run and score every row in a single bash invocation with the comparator in §2 (`python3 score-evals.py <PROJECT>`); never one tool call per row plus one to read the output — a 5-row × 3-iteration loop is ~3 calls that way instead of ~30. Runs are cheap (≈1 s per row); tool calls are what cost.
   - For each row the comparator prints `PASS` / `FAIL` / `ERROR` with the **raw** output and the expectation, scored by **the evaluator the project declares** (§1). Never substitute your own "the number looks right" judgment for its verdict.
   - **All pass** → stop and report the green result (rows, inputs, actual outputs).
   - **Any fail/error** → **first check for a key / casing / shape mismatch** between the raw output and `expectedOutput` (`sum` vs `Sum`, a missing wrapper object, a string where a number is expected). Decide which side is wrong: the workflow's output key must match its `output.schema` — fix the workflow; a row that contradicts the requested behavior — fix the row (§4). Otherwise triage the run (Structure > Expression > Activity Config > Logic — SKILL.md Core Principle 4), fix the workflow, re-run.
   - **Report progress each iteration** — e.g. "iteration 2: 3/4 rows pass; fixing row 'unpaid invoice' (expected status `unpaid`, got `paid`)".
   - **Stop conditions:** all green; OR no progress after a few iterations (cap it — see Infinite Loop Prevention in SKILL.md); OR the user interjects. Always end with a per-row summary of the final state.
   - **Stay in the main thread.** The loop is seconds of compute; a background subagent only adds turns and hides progress. If a new user message changes the workflow or the intent, incorporate the change before the next iteration — never keep scoring against a workflow the user has just asked you to change.

5. **Future edits — behavior changes can break the tests.** When a later request changes what the workflow *does* (a threshold, rounding, branch order, a new default) and an eval set exists, ask **before editing**: *"This change would make these expectations stale: [rows]. Update them to the new behavior, or keep them and flag the mismatch?"* Then edit, re-run the rows, and report which rows you updated and why (§4). A pure refactor or a schema-only rename that leaves behavior unchanged needs no question — just re-run the rows afterwards.

---

## 4. Notes & gotchas

- **Consent is the loop's gate.** "Yes, loop until green" authorizes repeated `--no-auth` runs. For workflows with side effects (IntSvc/vendor, authed HTTP), say so and get explicit consent before looping — each iteration re-triggers the side effect.
- **Keep the dataset in sync — with the schema AND the behavior.** Two distinct triggers:
  - **Schema change** — renamed/added/removed input or output arguments: the rows' `inputs` / `expectedOutput` shapes may no longer fit. Offer to update them.
  - **Logic change (easy to miss)** — a behavior change with an **unchanged** schema can still make existing `expectedOutput`s wrong: flip a threshold `>5` → `>=5`, change rounding, reorder branches, and a row that expected `pass` now correctly yields `fail`. **After any edit that changes behavior, re-derive the expected outputs — never "fix" the workflow to satisfy a now-stale test, and never silently rewrite a row the user did not ask to change.** Decide per row whether the expectation or the workflow is the source of truth, and say which rows you updated and why.
- **The project's evaluator is authoritative.** Read `evals/<SCOPE>/evaluators/*.json` and score by its `evaluatorTypeId`; today that is always `uipath-exact-match` (strict deep-equal).
- **"The agent said it passed" ≠ the panel passes.** An LLM eyeballing a run judges *meaning* (2+3=5 → looks right) and forgives key casing and shape; the evaluator does a byte-exact deep-equal and does not — and the CLI's PascalCased `Data` hides exactly that class of mismatch. When they disagree, the evaluator is right: fix the key/casing/shape.
- **Same files, two front-ends.** The user may author or run these rows in Studio Web's Evaluations panel between your turns; your CLI runs and their UI runs share `evals/…`. Re-read the files before each loop iteration rather than trusting an in-memory copy.
