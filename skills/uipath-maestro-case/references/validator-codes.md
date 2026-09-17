# Validator codes — what each one means and which check owns it

Companion to [implementation.md § Step 12](implementation.md). Step 12 defines the **checks**; this file maps the **codes** `uip maestro case validate --strict --sdd` emits onto them, with what each code is actually saying.

For codes whose *names mislead* — the four that have sent repairs at the wrong element — see [phased-execution.md § Findings whose names mislead](phased-execution.md#findings-whose-names-mislead). Read that first when a finding does not match the element it names.

```bash
uip maestro case validate "<caseplan.json path>" --strict --sdd sdd.md --output json
```

An unknown-option response means the installed CLI predates `--strict`/`--sdd` — see [case-commands.md § Version guard](case-commands.md#version-guard----strict----sdd-require-cli-1202).

## The catalog

### Check 4

After value bindings (Step 9.8), connector-rule upgrades (Step 10.5), and marker resolution (Step 11.5), **first run `uip maestro case validate "<caseplan.json path>" --strict --sdd sdd.md --output json`** (unknown-option response → [case-commands.md § Version guard](case-commands.md#version-guard----strict----sdd-require-cli-1202)). Its `STRICT_*` codes are the machine-checked half of this pass: `CASE_MGMT_XREF_UNRESOLVED` (an error on every profile, as is `CASE_MGMT_PLANNING_NOTATION` for a `<-`/`->` input value) is Check 4

### Check 1 — input bindings

`STRICT_INPUT_UNBOUND` (empty value, warning) / `STRICT_INPUT_REF_FORM` / `CASE_MGMT_REFERENCE_UNBOUND` (a `vars.<x>` that matches no variable or output — an error on every profile) / `STRICT_SDD_PRODUCER_MISMATCH`, `STRICT_SDD_INPUT_FORM_MISMATCH`, `STRICT_SDD_EXPRESSION_MISMATCH` (the row's expression, with its `$xref` markers resolved, differs from the plan's beyond whitespace/quote style — Rule 7 carries expressions verbatim) `CASE_MGMT_INPUT_BODY_ON_PLAIN_TASK` (an input on any non-connector task carries `body` — only connector envelopes have a `body`; every other task's input value lives in `value`, and an input with no `value` key is `STRICT_SDD_INPUT_EMPTY` under `--sdd` — an error on every profile), `STRICT_SDD_LITERAL_MISMATCH` (an input whose SDD row carries an object literal arrives with fields absent — an error naming the field count and the first missing key; a present field holding a different value is a warning — carry the row's literal whole, never a subset) and `STRICT_SDD_INPUT_EMPTY` (errors under `--sdd`: an input not wired to the producer its SDD row names, wired in a different form, or left empty/absent when the row carries a value — only `--sdd` can tell an unfinished plan from a finished one that omits things, which is why an empty input is merely `STRICT_INPUT_UNBOUND`, a warning, under bare `--strict`) are Check 1

### Check 8 and 10

`STRICT_OUTPUT_*` (a missing output type or a self-referencing output), `CASE_MGMT_OUTPUT_ID_MISSING` (an output with no `id`), `CASE_MGMT_OUTPUT_ORIGINAL_VAR_MISSING` (a non-custom task output with `source`/`target` whose `id` differs from its `var` — a `->` reassignment — must carry `originalVar` equal to its `id`; the designer's converter reads it — an error on every profile; formal arguments under `variables.inputs[]`/`outputs[]` are out of scope), `CASE_MGMT_OUTPUT_VAR_ID_CASE_MISMATCH` (an output whose `id` and `var` differ only in letter case — a bare output declares one name once, so `AgentExpenseRequest` / `agentExpenseRequest` is a slip, not a rename; a real `->` rename changes the word and is legitimate), `CASE_MGMT_OUTPUT_ID_DUPLICATE` (one output `id` on two tasks — the id is the write target, so the second write lands on the first task's variable; both errors on every profile) and `CASE_MGMT_OUTPUT_VAR_ID_MISMATCH` (an output whose `var` differs from its `id` beyond a collision suffix) are Checks 8 and 10

### Check 12

`STRICT_CONNECTOR_*`, `CASE_MGMT_CONNECTOR_INPUT_FLATTENED`, `CASE_MGMT_CONNECTOR_INPUT_STRINGIFIED`, `CASE_MGMT_CONNECTOR_INPUT_VALUE_NOT_BODY`, `CASE_MGMT_CONNECTOR_INPUT_TARGET_MISMATCH` `CASE_MGMT_CONNECTOR_RESOURCE_KEY_UNRESOLVED` (the context entry `resourceKey` carries the connection key itself, never a binding id or a `=bindings.` reference — the `connection` entry may reference a binding, `resourceKey` may not) and `CASE_MGMT_CONNECTOR_RESOURCE_KEY_MISMATCH` (that `resourceKey` equals the resolved key of the binding its own `connection` entry names — on tasks and on connector rules. The finding says which binding owns the key it found: when the key belongs to another declared connection, the `connection` entry and the `resourceKey` disagree about which connector the context is for — decide from the SDD row which connection this task or rule waits on and make both fields name it; never copy the named binding's key over a `resourceKey` that was right, that repairs the plan into one that is consistently wrong. When the key belongs to nothing, it is the objectName copied into the slot — set it from the cached spec's connection key) (errors on every profile: a connector task's `data.inputs[]` are exactly the spec's envelope entries — `pathParameters`, `queryParameters`, `body`, each with `name` equal to `target` and its fields as an object under `body`, never under `value` and never as a JSON string) are Check 12

### Check 11 — container placement

. **Container placement is the skill's check, not the CLI's:** the plan does not record which container each field belongs to, so populate exactly the envelope entries whose `CaseShape.Inputs[].Body` is non-empty in the cached `case spec` response (`tasks/spec-cache*.json`), copy that `Body` object field-for-field, and leave the other containers `{}` — for Outlook `Get Email List` the spec puts `parentFolderId`, `limit` and `filter` in `body` and leaves `queryParameters` empty; splitting or moving them passes every CLI rule and fails at runtime. `CASE_MGMT_BINDING_KEY_SHARED` (an `agent`/`process`/`rpa` task pair sharing one `resourceKey` — three resources cannot be one binding; two `action` tasks on one app is legitimate reuse) is Check 11

### Check 11 — binding keys

`CASE_MGMT_BINDING_KEY_MISMATCH`, `STRICT_BINDINGS_TASK_UNBOUND` (a task with resolved identity whose `name`/`folderPath` are not `=bindings.` references), `STRICT_BINDINGS_ID_DUPLICATE` (two root binding entries under one id — `=bindings.<id>` resolves to the first match by array order), `CASE_MGMT_BINDING_PAIR_INCOMPLETE` (a non-connector `resourceKey` must be shared by exactly one `name` entry and one `folderPath` entry — never one key per entry), `CASE_MGMT_ACTION_RECIPIENT_SHAPE` (an action task's `recipient` is an object `{Type, Value}`, never a bare string), `CASE_MGMT_RESOURCE_TASK_LITERAL_BINDING` (a resource task's `name`/`folderPath` are `=bindings.<id>` references, never literal strings), `STRICT_SDD_SLA_EXTRA` (more SLA rules on a scope than the SDD declares — one declared SLA with two escalations is one rule with two `escalationRule` entries, not two rules), `CASE_MGMT_SLA_RULE_UNKNOWN_KEY` (an SLA rule's keys are exactly `id, displayName, expression, count, unit, escalationRule` — `duration`/`type` are not keys; the duration is `count` + `unit`), `CASE_MGMT_SLA_ID_DUPLICATE` (one SLA rule `id` on two holders — a stage, a task, or the case level; `sla-status-change` rules key on `slaId`, so a shared id is ambiguous at runtime: mint a fresh `sla_` id per entry, never copy an SLA rule between holders — an error on every profile), `STRICT_SDD_SLA_DURATION_MISMATCH` (`count`/`unit` vs the SDD's Case Metadata `Case-Level SLA` row or a stage's SLA duration) `STRICT_SDD_SLA_CONDITIONAL_MISSING` (a row of the SDD's conditional SLA table — `Variable SLA Rules` / `Stage Conditional SLA Rules` and their sibling headings — has no `slaRules` entry with that expression and `count`/`unit`; a condition-based SLA is the conditional rows followed by the default row, never the default alone), `CASE_MGMT_SLA_RULE_UNREACHABLE` (an unconditional `=js:true` rule with rules after it — the first rule whose expression holds applies, so everything below it is dead; conditional rows first, default last — an error on every profile) and `STRICT_SDD_BINDING_FOLDER_MISMATCH` (a folderPath default that is not the task's `**Folder Path:**` / `**Deployment Folder:**`, or a folder key GUID where a path belongs) are Check 11

### Check 1 — SDD variable parity

`STRICT_SDD_VARIABLE_EXTRA` (a root case variable the SDD declares neither in Case Variables nor through an Outputs `->`/`=` cell) is Check 1

### Check 13

`STRICT_SDD_CONDITION_EXPRESSION_MISMATCH` (error: a rule's `conditionExpression` differs from its SDD row's IF cell; parentheses count), `STRICT_SDD_CONDITION_MISSING` (a row whose resolved IF expression matches no rule on the target), `STRICT_SDD_CONDITION_RULE_MISMATCH` / `STRICT_SDD_CONDITION_SELECTOR_MISSING` / `STRICT_SDD_CONDITION_SELECTOR_MISMATCH` (WHEN cell vs `rule` and its selector — a `selectedStageIds`/`selectedTasksIds` that points at a different stage or task than the cell names), `STRICT_SDD_CONDITION_EXIT_TYPE_MISMATCH` / `STRICT_SDD_CONDITION_FLAG_MISMATCH` (Exit Type, Interrupting, Marks cells) and `STRICT_SDD_CONDITION_EXPRESSION_UNDECLARED` (a `conditionExpression` on a rule whose SDD row's IF cell is `—`: the SDD entered or exited ungated, the plan added a gate) are Check 13

### Check 9 — condition rows

— rows are joined to rules by the WHEN cell (predicate plus target), not by Display Name, because builders renumber boilerplate names; `STRICT_SDD_TIMER_VALUE_MISMATCH` / `STRICT_SDD_TIMER_TYPE_MISMATCH` (a `wait-for-timer` task's `timeDuration` / `timerType` vs the task block's `**Value:**` / `**Timer:**`) are Check 9

### Check 9 — task configuration

`STRICT_SDD_TASK_DESCRIPTION_MISSING` (a warning under `--sdd`: the SDD writes prose for a task and the plan's `description` is empty, and the message names which SDD line to copy) is Check 18, `TASK_NOT_CONFIGURED` (a warning on every profile: a task with `data: {}`) is Check 9's raw signal, and `--sdd` refines it — `STRICT_SDD_PLACEHOLDER_RESOLVED` (error) when the SDD resolved that resource, `STRICT_SDD_PLACEHOLDER_TASK` (warning) when the SDD left it unresolved, in which case leave the `data: {}` alone, and `STRICT_STAGE_NO_TASKS` means Step 9 never ran for that stage. Repair every reported element with a targeted Edit and re-run until `Status: "Valid"` with `Profile: "strict"`; max 3 rounds, then **AskUserQuestion** with the remaining codes. If the installed CLI rejects `--strict`, run the default profile and say so in the completion report. Then invoke the end-of-Phase-3 validator — Checks 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15 — for everything strict does not cover (producer presence, type mismatch, selector integrity, entry-rule presence, sidecar parity). Phase 2 conditions and SLA remain in place throughout.

<!-- END: validator-codes.md -->
