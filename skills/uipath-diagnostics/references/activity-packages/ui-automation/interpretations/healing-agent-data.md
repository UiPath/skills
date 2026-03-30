# Healing Agent Data

When Healing Agent is enabled and a UI automation activity fails, the system captures detailed recovery data. This feature describes how HA interacts with UI Automation at runtime, the data structure it produces, and how to gather and interpret that data.

## How It Works

1. A UI automation activity fails with a selector exception
2. HA captures the current UI tree snapshot at the point of failure
3. HA analyzes the snapshot and generates alternative selectors with confidence scores
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
- `.Content.AnalysisResult[0].Recommendations` — suggested replacement selectors with confidence
- `.Content.AnalysisResult[0].TargetAnalysis.FailureReason` — why the selector failed
- `.Content.AnalysisResult[0].Images` — base64 screenshots (~500KB, extract only when needed)
- `.Content.AnalysisResult[0].UiTreeSnapshot` — UI tree metadata

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

If HA is disabled, all UI failure diagnostics are severely limited — no UI tree snapshots, no alternative selectors, no recovery confidence scores. Enabling HA is the single highest-impact configuration change for improving UI failure diagnostics.

## How to Gather HA Data

1. **Check if healing-fixes.json exists** — this is the highest-value file. If it exists and has entries, the fix is already known with high confidence. Check this before reading anything else.

2. **Read recovery-data-summary.json** — always read this first (~15KB, safe to read fully). It gives you the map to everything in the `uia/` directory.

3. **Extract targeted fields from uia/*.json** — never read the full file. Use targeted extraction:

```bash
# Get the ActivityRefId (critical for XAML matching)
jq -r '.Content.RuntimeInfo.ActivityRefId' uia/638955556313961579.json

# Get recommendations without screenshots
jq '.Content.AnalysisResult[0] | del(.Images)' uia/638955556313961579.json

# Get just the failure reason
jq -r '.Content.AnalysisResult[0].TargetAnalysis.FailureReason' uia/638955556313961579.json

# Get recommendation confidence scores
jq '.Content.AnalysisResult[0].Recommendations[] | {Confidence, StrategyName}' uia/638955556313961579.json
```

Alternative with grep when jq isn't available:
```bash
grep -A 3 '"ActivityRefId"' uia/638955556313961579.json
grep -A 3 '"Confidence"' uia/638955556313961579.json
```

4. **Extract screenshots only when needed** — images are base64 encoded, ~500KB each. Only read the last image (most recent UI state) and only when visual confirmation is needed.

## How to Interpret HA Data

### Confidence Scores

Recommendations include confidence scores (0.0-1.0):
- **> 0.8** — high confidence, HA is fairly certain this selector will work
- **0.5-0.8** — moderate confidence, likely correct but may need verification
- **< 0.5** — low confidence, HA couldn't find a close match. The UI may have changed significantly.

### Strategy Names

The `strategyName` field tells you how HA found the alternative:
- **FindAlternativeTextAttributeTargetStrategy** — matched by text content (aaname, innertext)
- **FindAlternativeIdTargetStrategy** — matched by automation ID
- **FuzzySearch** — fuzzy matching on multiple attributes
- **ComputerVision** — image-based element detection

### Source Types

- **RecoveryInfo** — HA applied this fix at runtime and the activity succeeded. Highest confidence — the fix is proven.
- **InferredRecoveryInfo** — HA inferred this fix from UI tree snapshots after the failure. The activity did NOT recover, but HA identified a viable alternative based on UI tree state. Still high confidence (0.95) because it's based on instrumentation, not heuristics.

### Failure Reasons

The `TargetAnalysis.FailureReason` field explains why the original selector failed:
- Element attribute changed (name, id, class)
- Element moved to a different position in the UI tree
- Element no longer exists (removed from application)
- Multiple elements match the selector (ambiguous)

## Prerequisites

- Healing Agent must be enabled on the process (`AutopilotForRobots.Enabled: true`, `AutopilotForRobots.HealingEnabled: true`)
- Robot must have connectivity to Semantic Proxy and LLM Gateway
- Activity must use selector-based targeting (HA doesn't support image-only activities for recovery)
