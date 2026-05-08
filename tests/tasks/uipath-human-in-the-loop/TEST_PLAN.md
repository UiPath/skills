# uipath-human-in-the-loop — Coding Agent Test Plan

| Field | Value |
|---|---|
| **Surface** | `uipath-human-in-the-loop` skill |
| **Repo** | `UiPath/skills` |
| **Status** | Active — May 2026 |

---

## What This Document Covers

Agent-facing test scenarios for the `uipath-human-in-the-loop` skill — detects HITL signals in natural language, designs HITL node schemas, and authors/wires nodes into UiPath Flow JSON files via `uip` CLI.

**Out of scope**: UiPath Orchestrator task execution (runtime), Form Task designer, Maestro non-HITL nodes.

---

## CLI Capability Boundaries

| Operation | Status |
|---|---|
| Deploy or execute a flow at runtime | NOT TESTED — tests validate authored `.flow` JSON only |
| Run a live HITL approval from a robot | NOT TESTED |
| AppTask surface (`e2e_07`) | SKIPPED — requires live tenant with deployed Action App |

---

## Node v1.0 — What the Tests Verify

All tests target `uipath.human-in-the-loop` v1.0 (the current manifest). Key invariants:

| Property | v1.0 value | Common mistake |
|---|---|---|
| Output variable | `$vars.<nodeId>.output` | Using `.result` (v1.0.0 behavior) |
| Output access key | field `id` property | Using field `variable` property |
| Status variable | `$vars.<nodeId>.status` | Expecting `"completed"` string |
| Status value | outcome `action` value (`"Continue"` / `"End"`) | Comparing to `"completed"` |
| Available handles | `completed` only | Wiring `cancelled` or `timeout` (removed in v1.0) |
| Definition shape | `version: "1.0"`, `shape: "square"` | `"1.0.0"` / `"rectangle"` |

---

## Variable Binding Accuracy

The two most common developer mistakes around HITL variable binding:

### 1. fieldId vs variable property

The HITL runtime result object keys are the field's **`id`** property, not the `variable` property.

```json
{ "id": "dec1", "variable": "approvalResult", "direction": "output" }
```

Correct access: `$vars.nodeId.output.dec1`
Wrong access: `$vars.nodeId.output.approvalResult`

The `variable` property creates a separate workflow-global variable (`$vars.approvalResult`) — this is a different access path, not the output object property.

### 2. binding on input vs output fields

- **Input fields** (`"direction": "input"`): MUST have `binding` pointing to upstream node output. Read from `variables.nodes` to construct `"=js:$vars.<nodeId>.output.<field>"`.
- **Output fields** (`"direction": "output"`): MUST NOT have `binding`. The human fills these in.
- **InOut fields** (`"direction": "inOut"`): MUST have `binding` (pre-fills from upstream) AND appear in `$vars.<nodeId>.output` after the human submits (same as output fields).

---

## Test Structure

| Tier | Purpose | Cadence |
|---|---|---|
| **Smoke** | Skill-trigger routing, negative guards — offline, tempdir sandbox | Every PR |
| **Quality** | Schema design accuracy, variable binding, handle wiring, options | Every PR |
| **E2E** | Full authoring lifecycle: Discover → Plan → Build → Verify — no step-by-step guidance | Pre-release |

**Scenario types:**

| Symbol | Meaning |
|---|---|
| 🟢 Green path | All operations expected to succeed |
| 🟤 Brown | Update / wiring / schema-evolution focus |
| 🔴 Negative | Operations expected to fail — verifies correct error handling |
| ⏭ Skipped | File exists but `skip: true` — blocked on infrastructure |

---

## File Inventory & Status

### Smoke — 8 files, all present ✅

| Status | File | Task ID | What it tests | Type |
|---|---|---|---|---|
| ✅ Present | [smoke_01_explicit.yaml](smoke_01_explicit.yaml) | `skill-hitl-smoke-explicit` | Explicit HITL request → detects pattern, proposes schema with inputs/outputs/outcomes | 🟤 Brown |
| ✅ Present | [smoke_02_approval_gate.yaml](smoke_02_approval_gate.yaml) | `skill-hitl-smoke-approval-gate` | Business language "approve before send" → proactive approval gate detection | 🟢 Green |
| ✅ Present | [smoke_03_escalation.yaml](smoke_03_escalation.yaml) | `skill-hitl-smoke-escalation` | AI confidence below threshold → escalation pattern, insertion point identified | 🟢 Green |
| ✅ Present | [smoke_04_writeback.yaml](smoke_04_writeback.yaml) | `skill-hitl-smoke-writeback` | AI writes to SAP without prompt → agent proactively flags write-back validation need | 🟢 Green |
| ✅ Present | [smoke_05_compliance.yaml](smoke_05_compliance.yaml) | `skill-hitl-smoke-compliance` | GDPR deletion + audit trail language → compliance/sign-off pattern detected | 🟢 Green |
| ✅ Present | [smoke_06_data_enrichment.yaml](smoke_06_data_enrichment.yaml) | `skill-hitl-smoke-data-enrichment` | OCR fields blank → data enrichment pattern; agent uses `inOuts` (not `outputs`) for fill-in fields | 🟢 Green |
| ✅ Present | [smoke_07_neg_automated.yaml](smoke_07_neg_automated.yaml) | `skill-hitl-smoke-neg-automated` | Fully automated single-supplier pipeline with explicit no-review sign-off → `hitl_needed: false` | 🔴 Negative |
| ✅ Present | [smoke_08_neg_admin.yaml](smoke_08_neg_admin.yaml) | `skill-hitl-smoke-neg-admin` | Action Center reassignment question (runtime admin) → `hitl_authoring_needed: false`, no flow authoring | 🔴 Negative |

### Quality — 8 of 11 present ✅ (3 pending)

| Status | File | Task ID | What it tests | Type |
|---|---|---|---|---|
| ✅ Present | [quality_01_approval_gate_schema.yaml](quality_01_approval_gate_schema.yaml) | `skill-hitl-quality-approval-gate-schema` | Invoice approval schema design (inputs/outputs/outcomes); agent must produce schema and stop — no CLI commands before user approves | 🟤 Brown |
| ❌ **Missing** | `quality_02_escalation_schema.yaml` | — | Escalation chain: 3+ outcomes (Approve/Escalate/Reject); agent designs schema and stops before CLI | — |
| ❌ **Missing** | `quality_03_inouts_data_enrichment_schema.yaml` | — | inOut vs output distinction: human sees+fills vs human fills from scratch | — |
| ✅ Present | [quality_04_all_handles.yaml](quality_04_all_handles.yaml) | `skill-hitl-quality-completed-handle-and-result` | Wire `completed` handle → downstream script node; agent references `$vars.<id>.output` by field ID; validate | 🟢 Green |
| ✅ Present | [quality_05_priority_and_timeout.yaml](quality_05_priority_and_timeout.yaml) | `skill-hitl-quality-priority-timeout` | HIGH priority + `PT48H` timeout duration (ISO 8601); validate `FinanceCompliance` flow | 🟤 Brown |
| ❌ **Missing** | `quality_06_confirm_before_cli_rule.yaml` | — | Adversarial: user says "skip the review" — agent must still propose schema and withhold CLI | — |
| ✅ Present | [quality_07_runtime_vars.yaml](quality_07_runtime_vars.yaml) | `skill-hitl-quality-runtime-vars` | Both `$vars.<id>.output` AND `$vars.<id>.status` referenced in downstream script; validate `ReviewAndRoute` | 🟢 Green |
| ✅ Present | [quality_08_variable_binding_fieldid.yaml](quality_08_variable_binding_fieldid.yaml) | `skill-hitl-quality-variable-binding-fieldid` | Agent uses field `id` (not `variable`) to access output fields; `$vars.nodeId.output.approved` not `.legalApproval` | 🟢 Green |
| ✅ Present | [quality_09_dev_mistake_wrong_type.yaml](quality_09_dev_mistake_wrong_type.yaml) | `skill-hitl-quality-dev-mistake-wrong-type` | Agent infers correct types from description: boolean for yes/no, number for amounts, date for deadlines | 🟢 Green |
| ✅ Present | [quality_10_dev_mistake_binding_direction.yaml](quality_10_dev_mistake_binding_direction.yaml) | `skill-hitl-quality-dev-mistake-binding-direction` | Input fields get binding from upstream; output fields get NO binding; bindings use `variables.nodes` paths | 🟢 Green |
| ✅ Present | [quality_11_inout_field_access.yaml](quality_11_inout_field_access.yaml) | `skill-hitl-quality-inout-field-access` | inOut fields: pre-filled via binding AND appear in `$vars.nodeId.output` after submit (same as output) | 🟢 Green |

### E2E — 7 of 7 present (1 skipped) ✅⏭

| Status | File | Task ID | What it tests | Type |
|---|---|---|---|---|
| ✅ Present | [e2e_01_invoice_approval_greenfield.yaml](e2e_01_invoice_approval_greenfield.yaml) | `skill-hitl-e2e-invoice-approval-greenfield` | SharePoint → HITL → SAP; full Discover→Plan→Build→Verify; wires `completed`, captures `$vars.output` | 🟤 Brown |
| ✅ Present | [e2e_02_ai_escalation_brownfield.yaml](e2e_02_ai_escalation_brownfield.yaml) | `skill-hitl-e2e-ai-escalation-brownfield` | Inserts HITL escalation node into existing `ComplaintTriage` flow on low-confidence path; wires `completed` | 🟤 Brown |
| ✅ Present | [e2e_03_gdpr_compliance_greenfield.yaml](e2e_03_gdpr_compliance_greenfield.yaml) | `skill-hitl-e2e-gdpr-compliance-greenfield` | GDPR deletion flow from scratch; P7D timeout duration (ISO 8601); wires `completed` | 🟢 Green |
| ✅ Present | [e2e_04_multi_hitl_brownfield.yaml](e2e_04_multi_hitl_brownfield.yaml) | `skill-hitl-e2e-multi-hitl-brownfield` | Inserts **two** HITL nodes into `HROnboarding` flow (doc review + IT access); both completed handles wired | 🟤 Brown |
| ✅ Present | [e2e_05_expense_approval_brownfield.yaml](e2e_05_expense_approval_brownfield.yaml) | `skill-hitl-e2e-expense-approval-brownfield` | Inserts single HITL node between two existing nodes in minimal `ExpenseApproval` flow; wires `completed` | 🟤 Brown |
| ✅ Present | [e2e_06_invoice_approval_greenfield_simple.yaml](e2e_06_invoice_approval_greenfield_simple.yaml) | `skill-hitl-e2e-invoice-approval-greenfield-simple` | Creates `InvoiceApproval` project from scratch (`uip solution new` + `flow init`); wires `completed`; validates | 🟢 Green |
| ⏭ **Skipped** | [e2e_07_apptask_brownfield.yaml](e2e_07_apptask_brownfield.yaml) | `skill-hitl-e2e-apptask-brownfield` | AppTask surface (`inputs.type = "custom"`): inserts HITL backed by deployed Action App; `skip: true` — blocked on live tenant + `~/.uipath/.auth` | 🟤 Brown |

---

## Coverage Map — Real-World Optimization

Each quality test targets a specific failure pattern observed in agent behavior:

| Test | Developer mistake / skill gap it guards against | Real-world consequence if uncaught |
|---|---|---|
| `quality_04` | Agent forgets to wire `completed` handle | Flow blocks indefinitely at the HITL step in production |
| `quality_07` | Agent references wrong variable path or wrong output key | Downstream scripts crash at runtime with undefined variable errors |
| `quality_08` | Agent uses `variable` property instead of field `id` for output access | `$vars.nodeId.output.legalApproval` is undefined; actual value is at `output.approved` |
| `quality_09` | Agent defaults all fields to `text` type | Boolean comparisons fail (`"true" !== true`); numbers compared as strings |
| `quality_10` | Agent adds `binding` to output fields, or forgets it on input fields | Blank form fields for reviewer (missing binding), or human input is silently ignored (binding on output overwrites) |
| `quality_11` | Agent uses `"output"` direction for editable+pre-filled fields instead of `"inOut"` | Human sees empty field (no pre-fill) or cannot edit it (treated as read-only input) |

---

## Coverage Gaps

| Capability | Smoke | Quality | E2E |
|---|---|---|---|
| Schema — `inOuts` for fill-in fields (data enrichment) | ✅ [smoke_06](smoke_06_data_enrichment.yaml) | ❌ **quality_03 pending** | — |
| Schema — escalation chain (3+ outcomes) | — | ❌ **quality_02 pending** | ✅ [e2e_02](e2e_02_ai_escalation_brownfield.yaml) |
| Confirm-before-CLI rule (adversarial) | — | ❌ **quality_06 pending** | — |
| Variable binding: fieldId access | — | ✅ [quality_08](quality_08_variable_binding_fieldid.yaml) | — |
| Variable binding: type accuracy | — | ✅ [quality_09](quality_09_dev_mistake_wrong_type.yaml) | — |
| Variable binding: input vs output direction | — | ✅ [quality_10](quality_10_dev_mistake_binding_direction.yaml) | — |
| inOut pre-fill + downstream access | ✅ [smoke_06](smoke_06_data_enrichment.yaml) | ✅ [quality_11](quality_11_inout_field_access.yaml) | — |
| Negative: invalid flow path | ❌ **no smoke test** | — | — |

---

## Remaining Gap Priority

#### 🔴 `quality_06_confirm_before_cli_rule.yaml`
[quality_01](quality_01_approval_gate_schema.yaml) only checks the cooperative case where the user asks for a schema review first. This test covers the adversarial case: user says "just do it, skip the review" — agent must still propose the schema and withhold `uip flow node add` until confirmed.

#### 🔴 `quality_02_escalation_schema.yaml`
[smoke_03](smoke_03_escalation.yaml) checks that the escalation pattern is detected but never verifies schema correctness. Agent must design a schema with 3+ outcomes (Approve / Escalate to Senior / Reject) and stop before running any CLI.

#### 🔴 `quality_03_inouts_data_enrichment_schema.yaml`
[smoke_06](smoke_06_data_enrichment.yaml) checks detection only. At quality depth, the agent must use `inOuts` (not `outputs`) for fields the human both sees and fills in, author the node, and validate — confirming the distinction survives actual CLI authoring.

#### 🟠 `smoke_09_neg_invalid_flow_path.yaml`
No test covers what happens when the agent tries to add a HITL node to a `.flow` file that doesn't exist. Agent must surface the CLI error cleanly and must not create a blank `.flow` file as a workaround.

#### 🟡 Unblock `e2e_07_apptask_brownfield.yaml`
[e2e_07](e2e_07_apptask_brownfield.yaml) is `skip: true` — it requires a live tenant with a deployed Action App and valid `~/.uipath/.auth` credentials. No new test file needed; this is an infra prerequisite.
