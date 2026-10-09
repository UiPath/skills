# MST-16422 round 3: prediction (written before upload, 2026-10-09)

Question: does the Case Designer keep the entry-point `uniqueId` of a project
that is already `caseplan.case` when it is first opened? In MST-15831 and the
MST-16423 retest the id was re-minted once, on the first open, together with the
`caseplan.json` → `caseplan.case` rename and the `filePath` rewrite.

## Input

The MST-16423 retest's pre-upload solution (cm_golden_expense, CLI-emitted),
changed only as `uip maestro case init` on UiPath/cli#5004 (head cd9532a)
scaffolds a project: plan named `caseplan.case`, entry point
`/content/caseplan.case.bpmn#trigger_1` with a fresh `uniqueId`, package
descriptor naming `caseplan.case` and `caseplan.case.bpmn`. Fresh SolutionId and
project Id. Two solutions, uploaded separately:

| Variant | Plan `version` | Why |
|---|---|---|
| A | 32.0.3 (the floor the CLI writes) | the shape a #5004 project actually has |
| B | 32.0.4 (what the Designer writes) | removes the version migration, so a re-mint in A but not B points at it |

Both are strict-Valid on the #5004 build with the two standing
`STRICT_INPUT_UNBOUND` warnings, and no sidecar finding.

## Procedure

Upload A and B. Pull each (control). Cliff opens each case in the Designer, no
edit. Pull each (round 1). Delete both.

## Predictions

| # | Prediction | Falsified if |
|---|---|---|
| Q1 | control pulls: plan, entry points, bindings and descriptor byte-identical to the upload | any of them differs |
| Q2 | A: entry-point `uniqueId` survives the open | it changes |
| Q3 | B: entry-point `uniqueId` survives the open | it changes |
| Q4 | A and B: no rename; `caseplan.case` stays, `caseplan.case.bpmn` is added, `filePath` unchanged | a file is renamed or `filePath` changes |
| Q5 | A: `version` 32.0.3 → 32.0.4. B: stays 32.0.4 | A stays, or B changes |
| Q6 | A and B: `layout` added; connector tasks get `activityConfigurationVersion: v2`, re-minted ids, catalog upgrade, as in retest P2/P6/P7 | any of these absent |
| Q7 | A and B: the 13 non-connector tasks unchanged; the 6 app/process `bindings_v2` entries byte-identical | any change |

Credence: Q2 and Q3 are the hypothesis under test, not a confident call. The
competing explanation is that the Designer re-mints whenever it first generates
the `.bpmn` sidecar, which both variants lack before the open.

## Reading the result

| A uniqueId | B uniqueId | Means |
|---|---|---|
| survives | survives | the rename caused the re-mint; #5004's `caseplan.case` scaffold fixes MST-16422 |
| changes | survives | the version migration causes it; writing the 32.0.3 floor keeps it happening |
| changes | changes | the first Designer save re-mints regardless of name or version; the CLI cannot prevent it |
| survives | changes | unexplained; record and do not conclude |
