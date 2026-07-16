# Logging — Implementation

Unified issue log for the implementation phase. Initialized by `implementation.md`, written to by any plugin, dumped to markdown after build.

> **No `planning.md`** — logging is an implementation-only utility (not a planned node type), so it has no planning doc. Intentional, not a gap.

> **Pseudocode only.** The snippets below are data-shape specifications, not runnable code. The agent holds the issue list in its own reasoning during a run and emits `tasks/build-issues.md` with the Write tool at dump time. Do NOT create a `.py` script or shell out to Python — per [`case-editing-operations.md § Tool usage`](../../case-editing-operations.md#tool-usage--mandatory), Read/Write/Edit are the only I/O primitives.

## Setup

Initialize the in-reasoning issue list before Step 6:

```text
issues = []   # pseudocode — kept in the agent's reasoning, not on disk
```

## Entry Format

```text
issues.append({                 # pseudocode — not executed
    "severity": "ERROR",        # "ERROR" | "WARNING" | "SKIPPED"
    "step": "9",                # implementation step number
    "plugin": "io-binding",     # plugin name — used for grouping in the output file
    "message": "human-readable description"
})
```

| Severity | Meaning | Build effect |
|---|---|---|
| `ERROR` | Required element missing — operation skipped | Binding/wiring incomplete |
| `WARNING` | Possible problem — operation proceeded | May cause runtime issues |
| `SKIPPED` | Intentionally deferred — placeholder/unresolved | User must complete manually |

## Dump

After Step 12 (validate), group issues by `plugin` and write to `tasks/build-issues.md`:

```markdown
# Build Issues — <CaseName>

**Case file:** caseplan.json | **Timestamp:** <ISO>

| Category | Errors | Warnings | Skipped |
|---|---|---|---|
| [io-binding](#io-binding) | 3 | 1 | 2 |
| [global-vars](#global-vars) | 1 | 0 | 0 |
| **Total** | **4** | **1** | **2** |

---

## io-binding

### Errors

| Step | Issue |
|---|---|
| 9 | Input `amount` not found on task "Validate Expense Data" |

### Skipped

| Step | Task | Reason |
|---|---|---|
| 9 | Run Compliance Check | No inputs — placeholder task |

## global-vars

### Errors

| Step | Issue |
|---|---|
| 6 | Variable `caseStatus` declared twice |
```

- Omit severity subsections with zero entries
- Plugins with zero issues: write `No issues.` under the heading
- Write the file even if zero total issues — confirms a clean build
- The completion report (Step 13) reads this file directly

### Interface deferrals and open items

Whenever Resource Interface Resolution ends `deferred` or `unavailable`, append one `SKIPPED` issue under plugin `resource-interface` and one deduplicated row under `## Open Items for User`. Key it by the exact sidecar owner object, not a composite display string:

```markdown
## Open Items for User

| Owner | Provider | Status | Reason | Placeholder / next action |
|-------|----------|--------|--------|---------------------------|
| task: Submission Review / Validate Submission | tasks-describe | deferred | missing output `riskBand` | task `data: {}`; select/adapt a compatible process |
| event-trigger: New urgent email | case-spec-trigger | unavailable | acquisition failed twice | serviceType-only trigger; restore connection/spec |
| condition-rule: stage-entry / Submission Review / Await update | case-spec-trigger | deferred | reversed `status` direction | validated rule stub; correct Case mapping |
```

Do not add another row when Phase 2/3 rereads an unchanged snapshot. Update the existing row when status/reason changes; remove it only after the owner becomes `compatible`, `adapted`, or `not-applicable` and the full consumer is materialized.
