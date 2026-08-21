# Script-ification Findings — uipath-maestro-flow

The skill teaches four capabilities (Author, Operate, Diagnose, Evaluate) over a 28-plugin
node-type catalog. Most of that is domain judgment or `uip` CLI surface. Twelve procedures are
deterministic: they take a `.flow` file (or a stated formula/table) and have exactly one correct
output. Those are now scripts under `scripts/`.

Line numbers below refer to the skill's own files, which are the specification each script
implements. Re-check them after editing the skill.

## Scripts

Three commands; everything else is an imported module under `scripts/_flow/` with no command line.
The 12 procedures map onto them as follows.

| Command | Procedures it covers | Type |
|---|---|---|
| `flow_edit.py apply --plan` | primitive `.flow` mutations, composite graph rewrites, inline-agent input wiring, node-ownership enforcement at edit time | TRANSFORM-PIPELINE / BUILD-MODEL |
| `audit_flow.py` | port + wiring legality, `=js:` prefix contract, Jint constructs, resource `bindings[]`, the "not caught by validate" set — plus `--fix-plan` / `--apply` for the mechanical repairs | VALIDATE/CHECK · DETECT · BUILD-MODEL |
| `diagnose_run.py` | diagnostic priority ladder + faulting-element→node correlation | TRANSFORM-PIPELINE / EXTRACT |

Internal modules: `_flow/lib.py` (loader, graph helpers, finding/report), `_flow/plan.py` (the op
applier), `_flow/topology.py`, `_flow/expressions.py`, `_flow/jint.py`, `_flow/bindings.py`,
`_flow/runtime_gaps.py`, `_flow/agent_inputs.py`. Standard library only.

Two procedures are **not** scripts any more, because a table in the docs is cheaper than a tool
call: node-ownership lookup (the two tables in `author/CAPABILITY.md` 26–47, now enforced by
`flow_edit`'s refusal to author a CLI-owned type) and connector `parameterValues` key encoding (the
substitution table in `plugins/connector/impl.md` 400–409). Mermaid plan validation is likewise
back to the 12 rules + 11-step procedure in `planning-arch.md` 502–548.

### Why this shape — measured, not assumed

Two coder_eval runs (`maestro-flow-*-sonnet-5`, `maestro-flow-*-sonnet-4-6`; reports under
`tmp/experiments/analysis/`) compared the first version of these scripts against the unscripted
skill. The first version shipped 13 CLIs and one mutation per invocation. It **raised** cost:
+$16.95 (+12.4%) on Sonnet 5 and +$6.84 (+8.7%) on Sonnet 4.6, even though on 4.6 it cut
tool-result tokens 14% and thinking 0.4%. The cause was turns: +15.4%/+15.2% cost-model turns, and
an empirical **$0.0298 (Sonnet 5) / $0.0200 (Sonnet 4.6) per added assistant turn** against a mean
`flow_edit` payload of 248/104 tokens — a turn costs 12–20× the payload it carries. Specifically:

- 373 (S5) / 146 (4.6) one-mutation `flow_edit` calls; batching to one call per task would have
  removed 351 / 131 turns ≈ **$10.47 (62%) / $2.63 (38%)** of the regression.
- 30 (S5) tasks paged `--help` or `scripts/*.py` source and carry **+$17.47** — and the files they
  paged (`audit_expressions.py`, `flow_lib.py`, `check_topology.py`, `check_runtime_gaps.py`) were
  labelled "internal" and had **zero invocations**.
- Tasks running `audit_flow` ≥2 times carry +$21.11 with **+343k output tokens** — findings were
  re-planned rather than applied.

Hence: one plan per call, repairs emitted as an applicable plan, three commands with no readable
internals, and the op vocabulary inline in SKILL.md so no `--help` round-trip is needed.

## 1. `audit_flow.py` — orchestrator

**Procedure.** `failure-modes.md` 329–336 lists what `uip maestro flow validate` catches and
338–345 lists what it misses ("**Not caught** — these still surface only at `flow debug` or in
deployed runs"). Every not-caught item is a structural predicate over the parsed `.flow`, so all
five local audits can run in one call before validate.

**Script.** Runs the five audit modules against one file, prints a per-check summary, writes the
full finding list to `--json-out`, and with `--fix-plan` / `--apply` turns the mechanically
repairable findings into plan ops it can apply itself before re-auditing. Exit 0 when no
error-severity finding remains, 1 otherwise.

```bash
python3 scripts/audit_flow.py MySolution/MyFlow/MyFlow.flow --json-out /tmp/findings.json
python3 scripts/audit_flow.py MyFlow.flow --apply                     # repair the mechanical set, re-audit
python3 scripts/audit_flow.py MyFlow.flow --fix-plan /tmp/fixes.json  # repairs as a flow_edit plan
python3 scripts/audit_flow.py MyFlow.flow --only expressions,jint     # subset
```

Turn cost before: each of these defects surfaced at `flow debug` (consent-gated, real side
effects) and then took the diagnose ladder to attribute — 5+ turns each. After: one call.

---

## 2. Port + wiring legality — `audit_flow.py --only topology`

**Procedure.** The Standard Port Reference (`planning-arch.md` 214–251) is a closed table of 31
node types → port names, plus dynamic `case-{id}` / `branch-{id}` and the implicit `error` port
(line 252). The 12 wiring rules (256–271) are graph invariants: trigger never a target, End never
a source, no dangling nodes ("Verify every node in the node table appears in the edge table as
either a source or target", line 270), decision exactly two branches, cycles only via `loopBack`.

**Where it runs.** Inside `audit_flow.py` (module `_flow/topology.py`). Reports `BAD_SOURCE_PORT`, `BAD_TARGET_PORT`, `TRIGGER_AS_TARGET`,
`TERMINAL_AS_SOURCE`, `NO_INCOMING`, `NO_OUTGOING`, `DANGLING_NODE`, `DECISION_BRANCHES`,
`SWITCH_CASES`, `ILLEGAL_CYCLE`, `ERROR_EDGE_WITHOUT_FLAG`, `MISSING_TARGET_PORT`,
`SOURCE_HANDLE`, `UNKNOWN_NODE_REF`, duplicate ids. Unknown node types are reported as `info`
and their ports are not checked, so a new plugin does not produce false errors.

```bash
python3 scripts/audit_flow.py MyFlow.flow --only topology
```

**Source conflict encoded:** the HITL QuickForm completion port is `completed` in
`planning-arch.md` 249 and `failure-modes.md` 132–148, but `outcome-completed` in
`plugins/hitl/impl.md` 79 and 204. Both spellings are accepted.

---

## 3. `=js:` prefix contract — `audit_flow.py --only expressions`

**Procedure.** `node-output-wiring.md` 11: "**Any string that references `$vars.*`,
`$metadata.*`, or `$self.*` MUST start with `=js:`. Otherwise it is a literal string at
runtime.**" The 14-row matrix at 55–76 says which fields require the prefix and which forbid it
(decision `inputs.expression`, switch `inputs.cases[].expression`, HTTP branch
`conditionExpression`, script body). Anti-patterns at 113–120 add the invented
`nodes.X.output.Y` form, `{ }` interpolation in connector/HTTP inputs, and a quoted `=js:`.
Line 109 is the exception: Transform `inputs.collection` is a path string *without* `=js:`.

**Where it runs.** Inside `audit_flow.py` (module `_flow/expressions.py`). Walks every string in `nodes[].inputs` / `nodes[].outputs` plus
`variables.variableUpdates`, dispatching by node type and JSON path. Errors:
`MISSING_JS_PREFIX`, `JS_ON_CONDITION`, `INVENTED_NODES_SYNTAX`, `BRACE_INTERPOLATION`,
`QUOTED_JS_PREFIX`. Warnings: `UNPREFIXED_REF` (a `$vars` reference in a field the matrix does
not cover — could be a documented plugin path field), `TRANSFORM_COLLECTION_PREFIXED`.

```bash
python3 scripts/audit_flow.py MyFlow.flow --only expressions
```

The CLI's `expression-prefix-validator` covers the missing-prefix half only; the
wrongly-prefixed conditions and the brace-interpolation cases are caught nowhere else.

---

## 4. Jint constructs — `audit_flow.py --only jint`

**Procedure.** `variables-and-expressions.md` 530–537 enumerates the unsupported set (`fetch`,
`XMLHttpRequest`, `setTimeout`, `setInterval`, `document`, `window`, `console`, `require`,
`import`, `eval`, `Function`, `async`/`await`, `Promise`, bare `Date`). `plugins/script/impl.md`
31–42 adds the eight script-node rules: no `function main()` wrapper, top-level `return` of an
object, no `console.log`, no external calls, 30-second timeout, never name a variable
`aggregate`.

**Where it runs.** Inside `audit_flow.py` (module `_flow/jint.py`). Scans `core.action.script` bodies and every `=js:` expression.

```bash
python3 scripts/audit_flow.py MyFlow.flow --only jint
```

None of this is caught by `flow validate` — an `await` or `console.log` faults the cloud run.

---

## 5. Resource-node `bindings[]` — `audit_flow.py --only bindings` / `--fix-plan`

**Procedure.** `file-format.md` 546: "Add **two entries** per resource node (one for `name`, one
for `folderPath`)", shared on `(resourceKey, name)`, with `resourceKey` / `resourceSubType`
copied verbatim from the definition's `model.bindings`. Line 553: without them
"`uip maestro flow debug` fails with \"Folder does not exist or the user does not have access to
the folder\" even though `uip maestro flow validate` passes."

**Where it runs.** Inside `audit_flow.py` (module `_flow/bindings.py`). For every `uipath.core.*` node it reads the definition's `model.bindings` and the
`<bindings.NAME>` placeholders in `model.context[]`, then checks the top-level `bindings[]` for a
matching `(resourceKey, name)`. `--emit` prints the missing entries; `--apply` appends them and
refuses (exit 2) when the definition does not supply `resource` / `resourceSubType`, which is the
case where the exact shape has to come from the resource plugin's `impl.md`.

```bash
python3 scripts/audit_flow.py MyFlow.flow --only bindings
python3 scripts/audit_flow.py MyFlow.flow --fix-plan /tmp/fixes.json   # emits the missing pairs
```

---

## 6. What `flow validate` does not catch — `audit_flow.py --only runtime-gaps`

**Procedure.** The residual not-caught list. `failure-modes.md` 158–166 names the two
error-handling shapes (flag with no handler; error path rejoining the happy path or sharing the
success terminal) and 172–201 ships the audit as a copy-paste `python3` heredoc — that logic is
ported here, so the heredoc is no longer inline in the reference. 111–125 gives the layout
thresholds (inline agents 288×96, containers 560×320, everything else 96×96, sticky notes
exempt). 60–98 gives the `variables.nodes[]` contract. 132–148 the unwired HITL port.
`file-format.md` 244 the ids-must-start-with-a-letter rule.

**Where it runs.** Inside `audit_flow.py` (module `_flow/runtime_gaps.py`); `--apply` repairs the
mechanical subset. Reports `FLAG_WITHOUT_ERROR_EDGE`, `ERROR_EDGE_WITHOUT_FLAG`,
`ERROR_REJOINS_HAPPY_PATH`, `ERROR_SHARES_SUCCESS_TERMINAL`, `LAYOUT_SIZE_MISMATCH`,
`MISSING_LAYOUT`, `MISSING_NODE_VARIABLE`, `HITL_PORT_UNWIRED`, `BAD_NODE_ID`, `BAD_EDGE_ID`,
`MISSING_OUTPUT_MAPPING`.

```bash
python3 scripts/audit_flow.py MyFlow.flow --only runtime-gaps
```

**Not scripted:** reused reference IDs (`failure-modes.md` 219–246). Whether an id belongs to the
bound connection is not decidable from the file — `--reference-fields` only lists
reference-id-looking connector fields as `info` so the agent can re-resolve them.

---

## 7. `flow_edit.py apply --plan` (structural mutations)

**Procedure.** `editing-operations-json.md` 13: "When editing the `.flow` file with `Edit` /
`Write`, **you** are responsible for everything the CLI normally handles". The pre-flight
checklist (26–41) and the primitive recipes (99–325) fix exactly which arrays each operation
touches — line 101: "**Tool:** `Edit` (insert into `nodes[]` + `definitions[]` +
`variables.nodes` + `layout.nodes`)" — plus the delete cascade (190–197), the edge id pattern and
four criticals (207–221), and the Edit-only variable operations (255–325).

**Script.** One plan file, one call: every op is applied in memory and the file is written once at
2-space indent, and nothing is written unless every op succeeds. Single-op subcommands remain for a
genuine one-off tweak and go through the same applier.

```bash
uip maestro flow registry get core.control.end --output json > /tmp/end.json
python3 scripts/flow_edit.py add-node --flow MyFlow.flow --id done \
    --type core.control.end --definition-file /tmp/end.json --label Done
python3 scripts/flow_edit.py add-edge --flow MyFlow.flow \
    --source buildPayload --source-port success --target done --target-port input
python3 scripts/flow_edit.py add-variable --flow MyFlow.flow --id total --direction out --type number
python3 scripts/flow_edit.py add-output-mapping --flow MyFlow.flow --end-node done \
    --var total --source '=js:$vars.buildPayload.output.total'
python3 scripts/flow_edit.py set-input --flow MyFlow.flow --node route --key expression \
    --value '$vars.buildPayload.output.total > 0'
python3 scripts/flow_edit.py delete-node --flow MyFlow.flow --id filterRows
```

Enforced from the skill: refuses a CLI-owned node type (exit 3) and points at
`uip maestro flow node add`; refuses ids that do not start with a letter; refuses a
`--type-version` that does not string-match the definition's `version`; requires `--target-port`;
sets `inputs.errorHandlingEnabled` when an `error` edge is added; refuses a `variableUpdates`
entry for a non-`inout` variable. `--outputs auto` writes the documented skeleton — `null` source
for triggers, `error`-only for Orchestrator-job families (`file-format.md` 156),
`=result.response` / `=Error` otherwise.

The anchoring discipline in `greenfield.md` 279–302 exists because the file was mutated by text
substitution; parsing it removes that failure mode. `layout` values stay placeholders —
`uip maestro flow format` still owns final layout.

---

## 8. Composite graph rewrites — plan ops inside `flow_edit.py apply`

**Procedure.** The composite recipes state their own tool-call counts — 331: "**Tool:** `Edit` ×
3 (delete old edge, add new node, add 2 new edges)"; 352: "**Tool:** `Edit` × 4 (delete node,
sweep edges, prune orphan definitions, add reconnect edge)" — plus insert-decision (339–349) and
replace-trigger (386–405).

**Where it runs.** Each composite is one op in the `flow_edit` plan vocabulary
(`insert-between`, `insert-decision`, `remove-reconnect`, `replace-trigger-scheduled`), so a
composite costs no extra call and can sit in the same plan as the surrounding edits.

```bash
cat > /tmp/plan.json <<'JSON'
{"ops":[{"op":"insert-decision","upstream":"buildPayload","id":"hasTotal","definitionFile":"/tmp/decision.json",
         "expression":"$vars.buildPayload.output.total > 0","trueTarget":"notify","falseTarget":"skip"}]}
JSON
python3 scripts/flow_edit.py apply --flow MyFlow.flow --plan /tmp/plan.json
```

`replace-mock-with-resource` is deliberately absent: steps 5–7 of that recipe
(`editing-operations-json.md` 360–385) need the resolved field values and the binding shape from
the resource plugin — that is the agent's judgment. Use `flow_edit` primitives plus
`audit_flow.py --fix-plan`.

---

## 9. Node ownership — doc tables, enforced by `flow_edit`

**Procedure.** `author/CAPABILITY.md` 24: "Every node in a `.flow` file has exactly one author.
The validator enforces this." Two closed tables (26–38 user-owned, 40–47 CLI-owned) plus the
never-`Write`-over-CLI-owned-nodes rule (54).

**Decision.**

```text
no script: the ownership tables live in author/CAPABILITY.md 26-47, and flow_edit refuses to
author a CLI-owned type (exit 3, naming `uip maestro flow node add`).
```

---

## 10. Mermaid plan rules — doc rules, no script

**Procedure.** `planning-arch.md` 504: "LLM-generated mermaid frequently contains syntax errors.
After generating the diagram, **check every rule below** before presenting it to the user. Fix
violations before outputting." 12 syntax rules (506–523) including the reserved-word list (510)
and forbidden characters (512–516), 6 structural rules (525–532), and an 11-step procedure
(534–548).

**Decision.** Kept in the docs — the rules are shorter to read than a tool call is to make.

```text
no script: the 12 syntax rules + 11-step procedure stay in planning-arch.md 502-548.
```

Structural rules that need the plan's intent (edge direction matches the flow, parallel branches
fork and converge) are not checked — those stay with the agent.

---

## 11. `parameterValues` key encoding — doc table, no script

**Procedure.** `plugins/connector/impl.md` 400: "**Token encoding rule.** Tokens are encoded via
`NamingHelper.getValidIdentifier` … Substitutions (applied longest-first)" — `:::`→`_sub_`,
`[*]`→`_array`, `::`→`_sub_`, `.`→`_sub_`, with worked outputs at 409. 411–418: the same values
must appear raw in `bodyParameters`/`queryParameters` and encoded in `parameterValues`, and the
on-wire shape is `[[key, value], …]` tuples, not an object map (`SKILL.md` 108).

**Decision.**

```text
no script: the longest-first substitution table stays in plugins/connector/impl.md 400-409.
```

Prints `parameterValues` (encoded tuples) and `runtimeParameters` (the raw-keyed copy) so both
halves of the contract go into `--detail`. Whether the activity has a parent-field-driven schema
at all (`impl.md` 363–376) is read from the registry metadata by the agent.

---

## 12. Inline-agent input wiring — `flow_edit.py agent-inputs`

**Procedure.** `plugins/inline-agent/impl.md` 50: "**The CLI does not derive the input wiring** —
`uip agent refresh` does **not** scan prompts, derive `inputSchema`, or populate
`agentInputVariables`; you author all three … Flatten rule: `$vars.<trigger>.output.<var>` →
`<trigger>__output__<var>`." The artifact table (62–67), the trigger-variable prerequisite
(54–60), and the anti-patterns (124–131) fix every field.

**Script.**

```bash
python3 scripts/flow_edit.py agent-inputs emit --source '$vars.start.output.invoiceNumber'
python3 scripts/flow_edit.py agent-inputs check --flow MyFlow.flow --agent-json agent/agent.json
# or write the node side directly: {"op":"agent-inputs","node":"triage","sources":["$vars.start.output.invoiceNumber:string"]}
```

`emit` never writes `contentTokens` — `uip agent refresh` regenerates those from `content`
(impl.md 71–83). `check` compares delivery / contract / prompt tokens three ways and flags
`BINDING_MISSING` (a `value` entry instead of `binding`), `FLATTEN_MISMATCH`, `TYPE_MISMATCH`,
`RAW_VARS_TOKEN`, `TRIGGER_INPUT_UNDECLARED`.

---

## 13. `diagnose_run.py` (diagnostic ladder)

**Procedure.** `troubleshooting-guide.md` 9: "Investigate in this order — each step adds context,
stop when you have enough to diagnose the root cause". Steps 1–5 are fixed and each call's
arguments come from the previous call's JSON, so the agent cannot batch them: `job status` →
`instance incidents` → `incident get` → `instance variables` → correlation (line 62: "Map the
element ID to the corresponding node, check its `inputs`, upstream edges, and the variable values
flowing into it"), with traces last (77–85).

**Script.**

```bash
python3 scripts/diagnose_run.py --job-key <JOB_KEY> --flow MyFlow.flow --out /tmp/diag.json
python3 scripts/diagnose_run.py --instance-id <ID> --folder-key <KEY> --flow MyFlow.flow --asset
python3 scripts/diagnose_run.py --job-key <JOB_KEY> --dry-run      # show the ladder, call nothing
```

Read-only: it never runs `flow debug`. Exit 0 report produced, 4 a CLI call failed, 5 no incident
found. `--cli` overrides the command prefix (`uip flow` on CLI < 0.3.4). Traces and
`instance asset` are opt-in. Interpreting the incident against the failure-mode catalog stays
with the agent.

---

## Not script-ified

| Area | Why |
|---|---|
| Capability routing, dropdown/consent protocol, narration | conversational policy |
| Maestro-fit gate, node selection ladders, topology patterns, plan prose | requirements judgment |
| 28 plugin families' input semantics | per-node-type domain knowledge |
| Connector configuration (connection bind → describe → reference resolution → `--detail`) | live-tenant calls and field elicitation |
| Ship / debug / process / job / instance lifecycle | `uip` CLI; already one chained call |
| Evaluate CRUD, run, compare | `uip` CLI; `--only-failed` already implements the failure rules |
| `flow validate` / `format` / `migrate` checks | implemented by the CLI |

## Tests

`script-tests/run_all.sh` runs one suite per script (fixtures are fabricated in temp dirs;
`diagnose_run` uses a fake CLI stub). All 13 suites pass.
