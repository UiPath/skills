# uipath-human-in-the-loop — Coding Agent Test Plan

| Field | Value |
|---|---|
| **Surface** | `uipath-human-in-the-loop` skill |
| **Repo** | `UiPath/skills` |
| **Status** | Draft — Apr 2026 |

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

## Test Structure

| Tier | Purpose | Cadence |
|---|---|---|
| **Smoke** | Skill-trigger routing, negative guards — offline, tempdir sandbox | Every PR |
| **Quality** | Schema design accuracy, handle wiring, options, confirm-before-CLI rule | Every PR |
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

### Quality — 4 of 7 present, **3 gaps confirmed** ❌

| Status | File | Task ID | What it tests | Type |
|---|---|---|---|---|
| ✅ Present | [quality_01_approval_gate_schema.yaml](quality_01_approval_gate_schema.yaml) | `skill-hitl-quality-approval-gate-schema` | Invoice approval schema design (inputs/outputs/outcomes); agent must produce schema and stop — no CLI commands before user approves | 🟤 Brown |
| ❌ **Missing** | `quality_02_escalation_schema.yaml` | — | **Not created** — see proposed spec below | — |
| ❌ **Missing** | `quality_03_inouts_data_enrichment_schema.yaml` | — | **Not created** — see proposed spec below | — |
| ✅ Present | [quality_04_all_handles.yaml](quality_04_all_handles.yaml) | `skill-hitl-quality-completed-handle-and-result` | Wire `completed` handle → downstream script node; agent references `$vars.<id>.result`; validate | 🟢 Green |
| ✅ Present | [quality_05_priority_and_timeout.yaml](quality_05_priority_and_timeout.yaml) | `skill-hitl-quality-priority-timeout` | HIGH priority + `PT48H` timeout (ISO 8601); validate `FinanceCompliance` flow | 🟤 Brown |
| ❌ **Missing** | `quality_06_confirm_before_cli_rule.yaml` | — | **Not created** — see proposed spec below | — |
| ✅ Present | [quality_07_runtime_vars.yaml](quality_07_runtime_vars.yaml) | `skill-hitl-quality-runtime-vars` | Both `$vars.<id>.result` AND `$vars.<id>.status` referenced in downstream script; validate `ReviewAndRoute` | 🟢 Green |

### E2E — 7 of 7 present (1 skipped) ✅⏭

| Status | File | Task ID | What it tests | Type |
|---|---|---|---|---|
| ✅ Present | [e2e_01_invoice_approval_greenfield.yaml](e2e_01_invoice_approval_greenfield.yaml) | `skill-hitl-e2e-invoice-approval-greenfield` | SharePoint → HITL → SAP; full Discover→Plan→Build→Verify; wires `completed`, captures `$vars.result` | 🟤 Brown |
| ✅ Present | [e2e_02_ai_escalation_brownfield.yaml](e2e_02_ai_escalation_brownfield.yaml) | `skill-hitl-e2e-ai-escalation-brownfield` | Inserts HITL escalation node into existing `ComplaintTriage` flow on low-confidence path; wires `completed` | 🟤 Brown |
| ✅ Present | [e2e_03_gdpr_compliance_greenfield.yaml](e2e_03_gdpr_compliance_greenfield.yaml) | `skill-hitl-e2e-gdpr-compliance-greenfield` | GDPR deletion flow from scratch; 7-day timeout (ISO 8601); wires both `completed` and `timeout` handles | 🟢 Green |
| ✅ Present | [e2e_04_multi_hitl_brownfield.yaml](e2e_04_multi_hitl_brownfield.yaml) | `skill-hitl-e2e-multi-hitl-brownfield` | Inserts **two** HITL nodes into `HROnboarding` flow (doc review + IT access); both completed handles wired | 🟤 Brown |
| ✅ Present | [e2e_05_expense_approval_brownfield.yaml](e2e_05_expense_approval_brownfield.yaml) | `skill-hitl-e2e-expense-approval-brownfield` | Inserts single HITL node between two existing nodes in minimal `ExpenseApproval` flow; wires `completed` | 🟤 Brown |
| ✅ Present | [e2e_06_invoice_approval_greenfield_simple.yaml](e2e_06_invoice_approval_greenfield_simple.yaml) | `skill-hitl-e2e-invoice-approval-greenfield-simple` | Creates `InvoiceApproval` project from scratch (`uip solution new` + `flow init`); wires `completed`; validates | 🟢 Green |
| ⏭ **Skipped** | [e2e_07_apptask_brownfield.yaml](e2e_07_apptask_brownfield.yaml) | `skill-hitl-e2e-apptask-brownfield` | AppTask surface (`inputs.type = "custom"`): inserts HITL backed by deployed Action App; `skip: true` — blocked on live tenant + `~/.uipath/.auth` | 🟤 Brown |

---

## Coverage Gaps

| Capability | Smoke | Quality | E2E |
|---|---|---|---|
| Schema — `inOuts` for fill-in fields (data enrichment) | ✅ [smoke_06](smoke_06_data_enrichment.yaml) | ❌ **quality_03 missing** | — |
| Schema — escalation chain (3+ outcomes) | — | ❌ **quality_02 missing** | ✅ [e2e_02](e2e_02_ai_escalation_brownfield.yaml) |
| Confirm-before-CLI rule (adversarial — user says "skip") | — | ❌ **quality_06 missing** | — |
| Wire `timeout` handle | — | ❌ **no quality test** | ✅ [e2e_03](e2e_03_gdpr_compliance_greenfield.yaml) |
| Negative: broken / empty schema passed to CLI | — | ❌ **quality_03 missing** | — |
| Negative: invalid flow path | ❌ **no smoke test** | — | — |

---

## Gap Priority

#### 🔴 `quality_06_confirm_before_cli_rule.yaml`
[quality_01](quality_01_approval_gate_schema.yaml) only checks the cooperative case where the user asks for a schema review first. This test covers the adversarial case: user says "just do it, skip the review" — agent must still propose the schema and withhold `uip flow node add` until confirmed.

#### 🔴 `quality_02_escalation_schema.yaml`
[smoke_03](smoke_03_escalation.yaml) checks that the escalation pattern is detected but never verifies schema correctness. Agent must design a schema with 3+ outcomes (Approve / Escalate to Senior / Reject) and stop before running any CLI.

#### 🔴 `quality_03_inouts_data_enrichment_schema.yaml`
[smoke_06](smoke_06_data_enrichment.yaml) checks detection only. At quality depth, the agent must use `inOuts` (not `outputs`) for fields the human both sees and fills in, author the node, and validate — confirming the distinction survives actual CLI authoring.

#### 🟠 `quality_08_timeout_handle.yaml`
`timeout` handle wiring is only tested in [e2e_03](e2e_03_gdpr_compliance_greenfield.yaml) as part of a full business scenario. A focused quality test should verify the agent wires the `timeout` handle to a downstream node and sets a valid ISO 8601 duration in isolation.

#### 🟠 `smoke_09_neg_invalid_flow_path.yaml`
No test covers what happens when the agent tries to add a HITL node to a `.flow` file that doesn't exist. Agent must surface the CLI error cleanly and must not create a blank `.flow` file as a workaround.

#### 🟡 Unblock `e2e_07_apptask_brownfield.yaml`
[e2e_07](e2e_07_apptask_brownfield.yaml) is `skip: true` — it requires a live tenant with a deployed Action App and valid `~/.uipath/.auth` credentials. No new test file needed; this is an infra prerequisite.
