---
confidence: high
---

# Selector Failure — Healing Agent Recovery Data Available

## Context

A UI automation activity failed because its selector didn't match any element in the live UI tree. Healing Agent was enabled and produced recovery data — either a deterministic fix in `healing-fixes.json` (self-healing path) or an `InferredRecoveryInfo` entry inside `uia/*.json` (recommendation-only path).

What this looks like:
- `SelectorNotFoundException`, `UiElementNotFoundException`, `ElementNotInteractableException`, or `NodeNotFoundException` during activity execution
- HA was enabled on the run (`AutopilotForRobots.Enabled=true`, `HealingEnabled=true`)
- One of the following recovery artifacts exists for the faulted activity:
  - `healing-fixes.json` with a matching entry (self-healing path — proven or attempted at runtime), OR
  - `uia/*.json` with a non-null `InferredRecoveryInfo` / `RecoveryInfo` containing a recovered target (recommendation-only path when `HealingAgentContext.OrchestratorEnableHeal=false`)

What can cause it:
- Target application UI changed (redesign, update, dynamic content)
- Element attribute became dynamic (index shifted, name changed per session)
- Authoring-time selector mistake against a stable element (typo, wrong attribute value, copy-paste error) — the live element is unchanged but the workflow's selector never matched
- Element temporarily obscured by a popup or overlapping window (HA may emit a `dismiss-popup` fix instead of `update-target`)

This playbook applies whenever HA recovery data is present for the failing activity, regardless of which specific cause above produced the failure. The cause label affects the user-facing narrative; the **remediation procedure (present HA's recommendation, ask whether to apply it) is the same for all of them** and is the authoritative resolution path even when the cause is later refined (e.g., depth-verifier identifies an authoring typo rather than UI drift).

## Investigation

1. Identify the recovery channel:
   - **Self-healing path** — `healing-fixes.json` exists at the job cache root. Match an entry by `ActivityRefId` (preferred) or `activityName` + `workflowFile`.
   - **Recommendation-only path** — `healing-fixes.json` is absent but `uia/*.json` contains `InferredRecoveryInfo` or `RecoveryInfo` with `RecoveredTarget`/`RecoveredSecondaryTarget`. `HealingAgentContext.OrchestratorEnableHeal=false` is the signature of this mode.
2. **Extract concrete selector strings** from the recovery data so they can be shown to the user. Do NOT summarize them away — the actual XML strings are required by the resolution procedure:
   - **Failed selector** — `Content.FailedResolvedTarget.PartialSelector` (and `FuzzyPartialSelector` if present) from the matching `uia/*.json`.
   - **Recovered selector** — for self-healing: `enhancedTarget` / `clickTarget` from the `healing-fixes.json` entry. For recommendation-only: locate the detection in `Content.AnalysisResult[0].AnalysisInformation[*].Detections[*]` whose `Id` matches `InferredRecoveryInfo.RecoveredTarget.DetectionId` (or, when no DetectionId is set, take the detection from the strategy with the highest-confidence consensus per `interpretations/healing-agent-data.md` § "Detections Without Recovery Entries"). Read its `EnhancedTargetDto.PartialSelector` and `EnhancedTargetDto.FuzzyPartialSelector` (fall back to `InferredTargetDto.*` if `EnhancedTargetDto` is empty).
3. Compare failed vs recommended selector and note which attributes changed (text, index, role, ancestry, etc.).
4. Record the recovery channel, the detection's `InferMethod` / confidence score, and whether self-healing actually applied the fix at runtime (`RecoverySuccessful`). These determine the warning attached to the apply-fix prompt.

Persist the exact failed and recovered selector strings to the evidence file for this hypothesis (e.g., as `failed_selector_xml`, `recovered_partial_selector_xml`, `recovered_fuzzy_partial_selector_xml`). The orchestrator's Resolution phase will read them back to drive the `AskUserQuestion` apply-fix flow — they MUST be present verbatim, not paraphrased.

## Resolution

Follow the fix-application procedures in [interpretations/healing-agent-data.md](../interpretations/healing-agent-data.md) (section "Applying HA Fixes" and "Applying Fixes — MUST Ask the User"):
- For `update-target` (self-healing) or `InferredRecoveryInfo.RecoveredTarget` (recommendation-only): use `uia-improve-selector` skill if available, otherwise direct XAML edit. When the data is `InferredRecoveryInfo` or `RecoverySuccessful: false`, attach the runtime-not-validated warning to the apply-fix prompt.
- For `dismiss-popup` / `RecoveredExternally`: create a Click activity before the failing activity, validate the workflow compiles.

This resolution path is **interactive** — it requires `AskUserQuestion` to be called by the orchestrator at the end of the diagnostic to (a) print the Failed / Recovered Partial / Recovered Fuzzy selectors as plain text, (b) ask the user whether to apply the fix and which selector variant. The presenter must emit a `## Post-presentation actions` block declaring this interactive step; the orchestrator must execute it before closing the investigation. Do not collapse this into a generic "fix the selector" recommendation — the recovered selector text and the apply-fix prompt are part of the documented resolution.
