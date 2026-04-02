# Healing Agent Data

When Healing Agent is enabled and a UI automation activity fails, the system captures detailed recovery data. This feature describes how HA interacts with UI Automation at runtime, the data structure it produces, and how to gather and interpret that data.

## How It Works

1. A UI automation activity fails with a selector exception
2. HA captures the current UI tree snapshot at the point of failure
3. HA analyzes the snapshot and generates alternative selectors
4. In **Self-Healing mode** — HA applies the best alternative and the activity retries automatically. If recovery succeeds, the job continues and recovery data is written as `RecoveryInfo`.
5. In **Recommendations mode** — HA records the suggestions for later review. The activity still fails, but recovery data is written as `InferredRecoveryInfo`.
6. Recovery data is written to the `healing-agent/` directory and accessible via Orchestrator API

HA only works with selector-based UI automation activities. Image-only targeting is not supported for recovery.

## Two-Tier Data Structure

```
healing-agent/
  recovery-data-summary.json     # Index file (~15KB) — ALWAYS read first
  uia/                           # Detailed recovery data
    638955556313961579.json      # 600KB-4MB per file
    638955558234567890.json
```

### Tier 1: Index File (recovery-data-summary.json)

Small (~15KB), safe to read fully. Contains:
- Job metadata (JobId, ProcessName, RobotName, timestamps)
- List of all recovery entries with metadata
- Activity names and workflow file references
- URIs to detailed files in the `uia/` directory

### Tier 2: Detailed Files (uia/*.json)

Large (600KB-4MB each). **Never read entire files.** Use targeted extraction.

Key paths:
- `.Content.RuntimeInfo` — activity details, failed selector, error message, `ActivityRefId`
- `.Content.AnalysisResult[0].AnalysisInformation` — strategies executed by Healing Agent (with Targets or Popups identified)
- `.Content.AnalysisResult[0].OriginalException` — why the activity failed (its exception)
- `.Content.AnalysisResult[0].Images` — base64 screenshots (~500KB, extract only when needed)

## External Interference (Popups)

HA can detect external interferences that blocked the automated application — windows overlapping the target app, HTML popups, or native browser popups (e.g., JavaScript `alert` dialogs).

- **External windows** — other application windows that appeared over the automated app. HA minimizes them to restore access.
- **HTML popups** — in-page overlays or dialogs within the browser. HA closes them.
- **Native browser popups** — JavaScript `alert`, `confirm`, `prompt` dialogs. HA dismisses them.

### Where to find popup data (agent-internal)

Popup recoveries are in `RecoveryInfo[].RecoveredExternally.Recoveries[]`. Each entry may contain:
- `ClickTarget` — the selector HA used to dismiss an HTML popup (browser popups only)
- `ClickTargetImage` — screenshot of the clicked dismiss element
- `Image` — screenshot of the popup itself

### Presenting popup findings to the user

Tell the user that a popup was detected and HA dismissed it. Do NOT expose field names or raw popup data. Example:
- Say "A popup appeared over the application and Healing Agent dismissed it to continue" — NOT "RecoveredExternally.Recoveries[0] contains a ClickTarget"

### Fix for popups

Do NOT attempt to edit the workflow to handle popups programmatically. Instead, suggest the user apply the fix from **Studio Desktop Recovery Panel**, which can integrate HA's popup handling into the workflow.

## Deterministic Fixes (healing-fixes.json)

When HA successfully identifies a fix, it's written to `healing-fixes.json` at the job cache root (next to `job-info.json`, `logs.txt`, `trace.json`).

Each entry contains:
- **activityRefId** — unique activity identifier, maps to XAML `IdRef`
- **activityName** — display name of the activity
- **workflowFile** — which .xaml file contains the activity
- **source** — `RecoveryInfo` (HA applied fix at runtime and it worked) or `InferredRecoveryInfo` (HA inferred fix from UI tree after failure)
- **fixes** — array of fix objects:
  - `update-target` — replace the activity's selector with HA-recommended one
  - `dismiss-popup` — add a Click activity to dismiss a popup before the failing activity

## Activity Matching: HA Data → XAML

The `ActivityRefId` from HA data maps directly to the `sap2010:WorkflowViewState.IdRef` attribute in XAML. This is a unique match within a workflow.

Matching methods (in preference order):
1. **ActivityRefId → IdRef** (preferred) — unique, unambiguous
2. **ActivityName + WorkflowFile** (fallback) — may be ambiguous if duplicate display names exist
3. **Line number / position** (last resort) — fragile, breaks if file is edited

## XAML Selector Encoding

When editing selectors in XAML, apply XML encoding in this order:
1. `&` → `&amp;` (FIRST — otherwise it corrupts other encodings)
2. `<` → `&lt;`
3. `>` → `&gt;`
4. `'` → `&apos;`
5. `"` → `&quot;`

## How to Check if HA is Enabled

Read the `AutopilotForRobots` field from job info. All three conditions must be true:

1. `AutopilotForRobots` field exists and is not null
2. `AutopilotForRobots.Enabled` is `true`
3. `AutopilotForRobots.HealingEnabled` is `true`

**Do NOT rely on the legacy `EnableAutopilotHealing` field** — it's a computed boolean that can be `false` even when HA is properly enabled. Always use `AutopilotForRobots` as the authoritative source.

If HA is disabled, all UI failure diagnostics are severely limited — no UI tree snapshots, no alternative selectors, no recovery detections. Enabling HA is the single highest-impact configuration change for improving UI failure diagnostics.

## How to Gather HA Data

1. **Check if healing-fixes.json exists** — this is the highest-value file. If it exists and has entries, the fix is already known with high confidence. Check this before reading anything else.

2. **Read recovery-data-summary.json** — always read this first (~15KB, safe to read fully). It gives you the map to everything in the `uia/` directory.

3. **Choose image handling** — steps 3a and 3b are mutually exclusive. Decide before processing:

   - **3a. Strip images** (default) — if screenshots are NOT needed for this investigation, run the post-processing script to remove base64 image data. This reduces file sizes from ~4MB to ~50KB and makes them safe to read:

     ```powershell
     # Windows (PowerShell)
     pwsh scripts/strip-ha-images.ps1 -Path uia/
     ```

     ```bash
     # Linux/macOS
     bash scripts/strip-ha-images.sh uia/
     ```

   - **3b. Preserve images** — if visual confirmation IS needed (e.g., to show the user the UI state at failure), do NOT run the strip script. Instead, extract screenshots selectively — images are base64 encoded, ~500KB each. Only read the last image (most recent UI state).

   Once images are stripped, they cannot be recovered. If unsure, preserve them.

4. **Extract targeted fields from uia/*.json** — for targeted extraction:

```bash
# Get the ActivityRefId (critical for XAML matching)
jq -r '.Content.RuntimeInfo.ActivityRefId' uia/638955556313961579.json

# Get just the failure reason
jq -r '.Content.AnalysisResult[0].OriginalException' uia/638955556313961579.json

# Get detections
jq -r '.Content.AnalysisResult[0].AnalysisInformation[0]' uia/638955556313961579.json
```

Alternative with grep when jq isn't available:
```bash
grep -A 3 '"ActivityRefId"' uia/638955556313961579.json
grep -A 3 '"OriginalException"' uia/638955556313961579.json
```

## Cross-Job Comparison

Do NOT assume that other job runs of the same process are relevant if the package version differs. A different version means the workflow may have changed — selectors, activities, and recovery behavior could all be different. Treat each package version as a separate process for diagnostic purposes.

Only compare across job runs when:
- The package version is **identical** between the jobs being compared
- OR the user **explicitly asks** to check similar jobs across versions

If the user asks to verify similar jobs of the same process, note the version difference in findings and flag that conclusions may not transfer across versions.

## How to Interpret HA Data

### Strategy Classification (agent-internal — NEVER show to user)

Strategies in `AnalysisInformation` are classified by their name prefix:
- **Alternative target strategies** — name starts with `FindAlternative` or is `ReuseTargetFaultAnalyzer`. These attempt to find a replacement UI element for the failed selector.
- **Other strategies** — everything else (e.g., popup detection).

### Source Types and Recovery Status

- **RecoveryInfo** with `RecoverySuccessful: true` — HA applied this fix at runtime and the activity succeeded. This is a **proven fix**.
- **RecoveryInfo** with `RecoverySuccessful: false` — HA attempted to apply a fix at runtime but the activity still failed. The suggested alternative did not work. Do NOT offer this as a fix.
- **InferredRecoveryInfo** — HA was in **recommendation-only mode** (self-healing disabled). `RecoverySuccessful` will always be `false` because HA did not retry the activity — it only analyzed the UI tree and inferred a possible alternative.

### Detections Without Recovery Entries

HA may find alternative targets or popups in `AnalysisResult` that do NOT appear in `RecoveryInfo` or `InferredRecoveryInfo`. This happens when:

- **Self-healing was enabled (RecoveryInfo path):** HA uses a voting mechanism across strategies — it selects the alternative target that intersects the most with the other strategies' results. If no consensus exists (strategies found different, conflicting alternatives), HA does not recommend anything to avoid false positives. The detections still exist in `AnalysisResult` but no recovery entry is written.
- **Recommendation-only (InferredRecoveryInfo path):** Same voting logic applies. HA analyzed the UI tree but strategies disagreed, so no recommendation was produced.

Only fall back to `AnalysisResult` in the detailed `uia/*.json` files if `RecoveryInfo` and `InferredRecoveryInfo` are empty or don't contain useful information. When reading `AnalysisResult`, be aware that strategies may have entries with empty detections (no targets or popups found) — skip those and only consider strategies that actually found something.

If `AnalysisResult[].AnalysisInformation[]` contains non-empty detections but `RecoveryInfo`/`InferredRecoveryInfo` are empty, tell the user that Healing Agent detected possible alternatives but its internal voting mechanism could not reach consensus, so no fix was recommended. Do NOT offer to apply anything from `AnalysisResult` — these are unreliable.

### Applying Fixes — MUST Ask the User

When a fix is available, you MUST use `AskUserQuestion` to ask the user whether they want you to apply it. Do NOT skip this step. Do NOT just describe the fix — explicitly ask.

When presenting the fix, first print the selectors as plain text output (NOT inside `AskUserQuestion` options or previews — XML selectors don't render correctly there). Then ask the question separately.

**Step 1 — Print selectors as text:**

```
Failed selector:
<selector content from FailedResolvedTarget.PartialSelector or FuzzyPartialSelector>

Recovered Partial selector:
<selector content from the chosen detection's PartialSelector>

Recovered Fuzzy selector:
<selector content from the chosen detection's FuzzyPartialSelector>
```

**Step 2 — Ask the user** (via `AskUserQuestion`, with no previews):

**If RecoveryInfo with RecoverySuccessful: true:**
- Tell the user the fix was proven at runtime
- Ask which recovered selector they want to apply (Partial or Fuzzy)

**If InferredRecoveryInfo with fix suggestions:**
- Warn the user that HA was in recommendation-only mode (self-healing was not enabled), so this fix was never actually tested at runtime and there's no guarantee it will work
- Ask which recovered selector they want to apply (Partial or Fuzzy)

**If no fix is available** (RecoverySuccessful: false with RecoveryInfo, no suggestions in InferredRecoveryInfo, or detections without recovery entries):
- Do NOT offer to apply anything. Proceed with manual investigation.

### Failure Reasons

The `TargetAnalysis.FailureReason` field explains why the original selector failed:
- Element attribute changed (name, id, class)
- Element moved to a different position in the UI tree
- Element no longer exists (removed from application)
- Multiple elements match the selector (ambiguous)

## Presentation — No Internal Fields

**NEVER present internal field names, JSON paths, strategy names, debug file structure, or raw data keys to the user.** This includes tables, lists, or any format that exposes internals. The user does not need to know about `ActivityRefId`, `AnalysisResult`, `RuntimeInfo`, `AnalysisInformation`, `OriginalException`, `RecoverySuccessful`, strategy names like `FindAlternativeTextAttributeTargetStrategy`, or any other internal key.

Do NOT show tables of detections, strategy names, or raw analysis results. Translate everything.

Do NOT tell the user which strategy or method HA used to recover the target. It is enough to say that HA found a fix.

Examples:
- Say "The activity **Click 'Submit'** in **Main.xaml** failed because the selector no longer matches" — NOT "ActivityRefId 12345 in RuntimeInfo shows SelectorNotFoundException"
- Say "Healing Agent found an alternative for this element" — NOT "FindAlternativeTextAttributeTargetStrategy with Confidence 0.95" or "matched by text content"
- Say "The button was renamed from 'Submit' to 'Send'" — NOT "The aaname attribute changed in the enhanced target"
- Say "Healing Agent analyzed 3 failed activities and found fixes for 2 of them" — NOT a table of AnalysisInformation entries

Internal field names exist in this document so the agent knows where to look in the JSON. They are never for the user.

## Prerequisites

- Healing Agent must be enabled on the process (`AutopilotForRobots.Enabled: true`, `AutopilotForRobots.HealingEnabled: true`)
- Robot must have connectivity to Semantic Proxy and LLM Gateway
- Activity must use selector-based targeting (HA doesn't support image-only activities for recovery)
