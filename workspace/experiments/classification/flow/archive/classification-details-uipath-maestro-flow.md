# Classification Details — uipath-maestro-flow

**Classification: Partial**

The skill has an enormous surface area (20+ plugin types in author alone, plus operate, diagnose, evaluate). Roughly 30 of its ~35 distinct operations are CLI calls, consent-gated actions, or generative/judgment-intensive editing steps. One genuine codifiable procedure is identified (eval set structure validation); the skill's own CLI (`flow validate`, `flow format`) already handles the static correctness checks for the `.flow` file itself.

---

## What the Skill Teaches

| # | Operation / workflow | Codifiable? | Notes |
|---|---------------------|-------------|-------|
| 1 | `uip maestro flow init` — scaffold a new flow project | No | CLI call |
| 2 | Registry search / list / get — discover node types | No | CLI calls; selection requires judgment |
| 3 | Add user-owned nodes (Edit/Write to `.flow`) — triggers, control-flow, logic, HITL, patterns, agents, queues, resource nodes | No | Generative; shape is driven by requirements |
| 4 | Add CLI-owned nodes (`node add` + `node configure`) — connector, connector-trigger, managed HTTP | No | CLI calls; connector key + operation selected from registry |
| 5 | Configure IS connections + resource IDs (`uip is connections list`, `uip is resources run list`) | No | CLI calls; connection choice and resource lookup require judgment |
| 6 | Wire nodes with edges (`targetPort` required on every edge) | No | Editing; wiring decisions are generative |
| 7 | Manage variables and expressions (`variables`, `=js:` prefix rules) | No | Editing with explicit rules, but content is generative |
| 8 | Script node authoring (Jint ES2020 JS) | No | Creative |
| 9 | Transform node authoring (filter / map / group-by) | No | Declarative but content-driven |
| 10 | Subflow creation | No | Editing |
| 11 | `flow validate` — local correctness check | No | CLI call (already scripted by the CLI itself) |
| 12 | `flow format` — layout normalization | No | CLI call |
| 13 | Plan generation before building | No | Planning; open-ended |
| 14 | `solution resources refresh` — sync resource declarations | No | CLI call |
| 15 | `solution upload` — push to Studio Web | No | CLI call; consent gate |
| 16 | `flow pack` + `solution publish` — deploy to Orchestrator | No | CLI calls; explicit consent required |
| 17 | `flow debug` — cloud end-to-end run | No | CLI call; consent gate |
| 18 | `process run` — trigger deployed process | No | CLI call |
| 19 | `job status` / `job traces` — check or stream execution | No | CLI calls |
| 20 | Instance lifecycle — pause / resume / cancel / retry | No | CLI calls; retry requires prior diagnosis |
| 21 | Read incidents — identify error category + faulting element | No | CLI call + interpretation |
| 22 | Fetch runtime variable state at failure | No | CLI call + interpretation |
| 23 | Correlate faulting element ID to `.flow` node | No | JSON lookup; trivial one-liner |
| 24 | Recognize known failure modes (MST-9107, MST-9061, etc.) | No | Pattern matching on incident output; `flow validate` already catches MST-9107 + MST-9061 |
| 25 | `eval set create` — define a new eval set | No | CLI call |
| 26 | Add simulation data points — define synthetic test cases | No | CLI + JSON editing |
| 27 | Add recording data points — replay past runs | No | CLI call |
| 28 | **Define evaluators (7 types) — validate structure before submit** | **Yes — VALIDATE** | 7 types with explicit required fields documented in `evaluators-guide.md`; malformed JSON causes API rejection |
| 29 | `eval run start` — launch evaluation | No | CLI call |
| 30 | `eval run status` — poll run state | No | CLI call |
| 31 | `eval run results` — fetch per-data-point scores | No | CLI call |
| 32 | `eval run compare` — diff two run scores | No | CLI call |

---

## Codifiable Procedures

### 28. Eval set evaluator structure validation — VALIDATE

**Source:** `references/evaluate/references/evaluators-guide.md` — per-type JSON shapes for all 7 evaluator types

**What it does:** Given an eval set config JSON file (the argument to `uip maestro flow eval set add-evaluator`), parse the `evaluators` array and validate each entry against its type's required fields:

| Type | Required fields |
|------|----------------|
| `exact-match` | `expected` (string) |
| `semantic` | `expected` (string) |
| `task-completion` | `criteria` (array of strings or criteria objects with `description`/`weight`) |
| `flow-shape` | `expectedShape` (object with at least one of `nodes`, `edges`, `triggers`) |
| `structured-output` | `expectedSchema` (JSON Schema object with `type`) |
| `custom-judge` | `promptTemplate` (string) |
| `resource-call-check` | `resources` (array of objects with `nodeType` and `callCount`) |

Exit 1 with a per-evaluator error list if any required field is missing or has the wrong type. Exit 0 if all evaluators are valid.

**Why it's mechanical:** Every field requirement is explicitly stated in the guide. No judgment on content — only structural presence and type checking.

**Turn savings:** Prevents the agent from submitting a malformed eval set JSON that the API silently rejects or returns an opaque error for — typically saves 1-2 turns of API round-trips + diagnosis.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** The skill's teaching is dominated by generative authoring work and CLI-call sequences:
- The Author capability alone covers 20+ plugin types, each with its own node-specific configuration. This is design/coding work, not a scripted procedure.
- The CLI already handles the two most mechanically-checkable correctness rules: `flow validate` catches MST-9107 (`=js:` prefix violations), missing edge `targetPort`, missing `definitions` entries, and unmapped End node outputs; `flow format` handles layout normalization and `variables.nodes[]` regeneration.
- Operate and Diagnose are entirely CLI calls interleaved with consent gates and interpretation steps — none is scripted.
- Evaluate is mostly CLI calls; the comparison CLI already computes `ScoreDelta` between two runs.

These represent ~33 of the ~35 distinct operations taught by the skill.

**Why not None:** One genuine VALIDATE procedure exists — eval set evaluator structure validation — with explicit JSON-shape rules per evaluator type that are not enforced by any existing CLI pre-flight. The `evaluators-guide.md` provides 7 complete type schemas that are directly implementable as a schema checker.

**Why not more:** The two most obvious VALIDATE candidates for the `.flow` format itself (`=js:` missing, missing `definitions`, unmapped `out` variables) are already fully handled by `uip maestro flow validate`. Implementing them as standalone scripts would duplicate the CLI with no turn savings.

**Evidence locations:**
- Codifiable: `references/evaluate/references/evaluators-guide.md` — 7 evaluator type schemas
- Non-codifiable authoring (generative): `references/author/CAPABILITY.md` §Node ownership, §Workflow, plugin tree under `references/author/references/plugins/`
- Non-codifiable flow validation (already CLI): `references/author/CAPABILITY.md` Critical Rule #8 ("Validate once at the end — `uip maestro flow validate`"), rules #11–#14 (all caught by `flow validate` / `flow format`)
- Non-codifiable operate: `references/operate/CAPABILITY.md` — all CLI calls with consent gates
- Non-codifiable diagnose: `references/diagnose/CAPABILITY.md` — priority ladder of CLI calls with interpretation
- Non-codifiable eval comparison: `references/evaluate/references/running-guide.md` §Compare Two Runs — `eval run compare` already outputs `ScoreDelta`
