# Logging — Implementation

Unified issue log for the implementation phase. Initialized by `implementation.md`, written to by any plugin, **flushed to disk at every section boundary**, and summarized after build.

> **No `planning.md`** — logging is an implementation-only utility (not a planned node type), so it has no planning doc. Intentional, not a gap.

> **Pseudocode only.** The snippets below are data-shape specifications, not runnable code. The agent accumulates issues in its own reasoning *within a section* and emits `tasks/build-issues.md` with the Write/Edit tools at each flush. Do NOT create a `.py` script or shell out to Python — per [`case-editing-operations.md § Tool usage`](../../case-editing-operations.md#tool-usage--mandatory), Read/Write/Edit are the only I/O primitives.

**Flush grain: the section boundary.** Not per issue (one Edit per finding, fights the [per-section batch write contract](../../case-editing-operations.md#per-section-batch-write-contract--canonical)); not per build (a whole-build buffer is lost to context pressure before it is written, and no Step 12 check reads the log). A section boundary already carries a validate, so the flush rides an existing seam and bounds loss to one section.

## Setup — Step 6 entry

Accumulate issues in reasoning *within the current section only*:

```text
issues = []   # pseudocode — per-section buffer, NOT a whole-build accumulator
```

## Entry Format

```text
issues.append({                 # pseudocode — not executed
    "severity": "ERROR",        # "ERROR" | "WARNING" | "SKIPPED"
    "step": "9",                # implementation step number
    "plugin": "io-binding",     # plugin name — used for grouping in the summary
    "message": "human-readable description"
})
```

| Severity | Meaning | Build effect |
|---|---|---|
| `ERROR` | Required element missing — operation skipped | Binding/wiring incomplete |
| `WARNING` | Possible problem — operation proceeded | May cause runtime issues |
| `SKIPPED` | Intentionally deferred — placeholder/unresolved | User must complete manually |

## Flush — at every section boundary (MANDATORY)

Flush alongside the section's validate, then clear the buffer. Sections are the ones named in [`implementation.md` § Per-section batched writes](../../implementation.md): Phase 2 §4.2.1 vars, §4.3 triggers, §4.4 stages, §4.6 task shapes, §4.8 SLA, §4.7 conditions; Phase 3 §9.7 connector schema, §9.8 I/O binding, §10.5 connector-rule upgrades.

**Flush even when the section produced zero issues** — the file's existence after the first section is what proves the log survived.

### First flush — create the file (Write)

```markdown
# Build Issues — <CaseName>

**Case file:** caseplan.json | **Build started:** <ISO>

<!--build-issues:summary:start-->
_Summary written at Step 12.1._
<!--build-issues:summary:end-->

## Journal

Appended at each section boundary as the build proceeds. Chronological, not grouped — grouping happens in the summary above at Step 12.1.

| Sev | Step | Plugin | Message |
|---|---|---|---|
| SKIPPED | 9 | connector-activity | Task "Confirm Payment Settlement" — connector unresolved, placeholder emitted |
```

### Later flushes — append rows (Edit)

One `Edit` per section, appending the section's rows to the end of the Journal table. Never rewrite earlier rows — the journal is append-only, so a later context loss cannot erase what an earlier section recorded.

A section with no issues appends nothing; the file already exists, which is the signal that matters.

## Summary — Step 12.1

Read the journal back, group by `plugin`, and replace **only** the block between `<!--build-issues:summary:start-->` and `<!--build-issues:summary:end-->`:

```markdown
| Category | Errors | Warnings | Skipped |
|---|---|---|---|
| [io-binding](#io-binding) | 3 | 1 | 2 |
| [global-vars](#global-vars) | 1 | 0 | 0 |
| **Total** | **4** | **1** | **2** |
```

- Group counts come from the journal on disk, **not** from reasoning — that is the point of the journal.
- Omit severity subsections with zero entries; plugins with zero issues need no heading.
- Leave the Journal section intact. It is the audit trail; the summary is a view over it.
- The completion report (Step 13) reads this file directly.

## Recovery — journal missing at Step 12.1

If `tasks/build-issues.md` does not exist when Step 12.1 runs, the incremental flush was skipped. Reconstruct what the artifacts prove — `<UNRESOLVED>` markers in `tasks.md`, placeholder tasks (`data: {}`) in `caseplan.json`, `selected: null` entries in `tasks/registry-resolved.json`, and any surviving connector stub — and stamp the file:

```
NOTE: reconstructed at Step 12.1 from on-disk artifacts — the incremental journal was not written. Severity and step attribution are approximate.
```

A reconstructed log records what the artifacts prove, not what the build observed. It is a fallback, not the contract.

<!-- END: impl-json.md -->
