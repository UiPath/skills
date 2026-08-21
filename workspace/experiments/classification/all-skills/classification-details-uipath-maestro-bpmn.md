# Classification Details — uipath-maestro-bpmn

**Classification: Partial**

---

## What the Skill Teaches

Author, validate, package, operate, and diagnose UiPath Maestro `.bpmn` projects — with authoring split between registry-driven `uipath:*` payload assembly and judgment-based structural BPMN design.

| # | Area | Codifiable? | Notes |
|---|------|-------------|-------|
| **1** | **Registry discovery (pull / list / search)** | **Yes — EXTRACT** | `uip maestro bpmn registry pull/list/search --output json`; fixed command sequence to map intent to extension types |
| **2** | **`uipath:*` template fetching and placeholder fill** | **Yes — TRANSFORM-PIPELINE** | `registry get <type> --output json` returns `xmlTemplate`; fill placeholders only, no invention |
| 3 | Structural BPMN authoring (process scaffold, sequence flows, gateways, events, boundary events, subprocesses, multi-instance, diagram) | No | Judgment on process structure, node placement, gateway conditions, event design; the largest portion of the skill |
| **4** | **BPMN validation** | **Yes — VALIDATE/CHECK** | `uip maestro bpmn validate <file.bpmn> --output json`; exit 0 = valid, exit 1 = errors; fix only error-severity findings |
| **5** | **Package and operate lifecycle** | **Yes — TRANSFORM-PIPELINE** | Pack → upload → publish → run pipeline via CLI; references/operate/CAPABILITY.md |
| **6** | **Diagnosis (fetch incidents, variables, element executions)** | **Yes — EXTRACT** | `uip maestro bpmn instance` commands; DETECT for failure mode matching |
| 7 | IS connector enrichment (connection binding, dynamic schemas) | No | Requires live connector metadata; CLI-owned; agent must defer enrichment to CLI |
| 8 | User confirmation gates (AskUserQuestion before authoring, before cloud changes) | No | Judgment on what to confirm and how to present options |

---

## Codifiable Procedures (not yet scripted)

### 1. Registry Discovery Sequence — EXTRACT

**Source:** `skills/uipath-maestro-bpmn/SKILL.md` §Workflow (step 1)

**What it does:** Before authoring any `uipath:*` node, discover available extension types via a fixed three-command sequence: `registry pull` (once per session to populate cache), `registry list` or `registry search <keyword>` to map intent to type names, and `registry get <type>` to retrieve the `xmlTemplate`. For IS connector nodes, `uip is connections list --all-folders` is also required. Line 99: "Discover. `uip maestro bpmn registry pull` once (cached for the session — do not re-pull), then `list` / `search` to map intent to extension types; `uip is connections list --all-folders` for live connections (always `--all-folders` — a folder-scoped list silently misses connections)."

**Why it's mechanical:** The command sequence (pull → list/search → get) is fixed and order-dependent; the output shape (`xmlTemplate`) is always the same regardless of node type.

**Turn savings:** Currently the agent runs 3–5 commands across 2–3 turns to discover and fetch templates; a discovery script accepting intent keywords and returning templates collapses to one call.

---

### 2. BPMN Validation — VALIDATE/CHECK

**Source:** `skills/uipath-maestro-bpmn/SKILL.md` §Workflow (step 4)

**What it does:** After assembling a `.bpmn` file, run the CLI validator which executes the full PO.Frontend canvas rule set offline. Exit 0 means valid; exit 1 means validation failed with per-issue rule codes in the envelope. Fix only error-severity findings; warnings do not block. Line 158: "Validate. Run the CLI validator — it runs the full PO.Frontend canvas rule set (structural rules plus variable, method-call, input-type, and event-object checks) offline, plus deploy-readiness checks: `uip maestro bpmn validate <file.bpmn> --output json`."

**Why it's mechanical:** The command is fixed; pass/fail is deterministic from exit code; error vs warning severity is explicit in the response envelope.

**Turn savings:** Without a script the agent runs the command, parses JSON, and decides what to fix across 1–2 turns; a validation wrapper returning structured findings collapses to one call.

---

### 3. Package and Operate Lifecycle — TRANSFORM-PIPELINE

**Source:** `skills/uipath-maestro-bpmn/SKILL.md` §Operate and diagnose

**What it does:** After authoring and validating, the skill routes to a fixed lifecycle pipeline: pack the project, upload to Studio Web, publish or deploy, run or debug instances, and manage jobs and lifecycle actions — all via `uip maestro bpmn` and `uip solution` CLI commands. Line 179: "Package and operate (package a project, upload to Studio Web, publish or deploy, run or debug instances, and manage jobs, instances, incidents, and lifecycle actions): see references/operate/CAPABILITY.md."

**Why it's mechanical:** The pipeline steps are ordered and CLI-driven; each step has a fixed command and verification check; user consent gates are the only non-mechanical element.

**Turn savings:** Without a script the agent runs 4–6 CLI commands sequentially across multiple turns; a lifecycle orchestrator collapses the standard pack→upload→publish sequence to one call.

---

## Justification for Classification

**Partial** — not Strong, not None.

**Why not Strong:** Structural BPMN authoring — the primary purpose of the skill — is judgment-driven: the agent designs the process structure (which nodes, which gateways, how sequence flows connect, what boundary events attach to), selects from the full BPMN event matrix, and makes all architectural decisions about the process shape. This is the largest single area of the skill, and it cannot be scripted. The codifiable procedures (registry discovery, validation, lifecycle packaging) are essential support infrastructure but secondary to the design work.

**Why not None:** The registry discovery sequence (EXTRACT), validation (VALIDATE/CHECK), and operate lifecycle (TRANSFORM-PIPELINE) are all deterministic, CLI-driven procedures with fixed command sequences and explicit success criteria.

**Evidence locations:**
- Registry discovery sequence: `skills/uipath-maestro-bpmn/SKILL.md` §Workflow step 1 (line 99)
- Validation procedure: `skills/uipath-maestro-bpmn/SKILL.md` §Workflow step 4 (line 158)
- Judgment-based structural authoring: `skills/uipath-maestro-bpmn/SKILL.md` §The model (lines 46–58), §Structural coverage table (lines 192–210)
- Operate/diagnose routing: `skills/uipath-maestro-bpmn/SKILL.md` §Operate and diagnose (lines 176–188)
