# MST-16422 round 4: prediction (written before upload, 2026-10-09)

Round 3 showed that the Designer sets `entry-points.json` `uniqueId` from the trigger
node's `data.inputs.entryPointId`, and mints one when the field is missing. Round 4
asks two questions:
1. Does the Designer keep a pre-written `entryPointId`?
2. Is the connector v2 upgrade triggered by selecting the task, rather than by the
   open (round 3 saw no upgrade on a bare open)?

## Input

Round 3's variant A (`caseplan.case`, version 32.0.3), with fresh SolutionId, project
Id and entry-point `uniqueId`, plus one change: `nodes[trigger_1].data.inputs.entryPointId`
is set to that `uniqueId`, written by hand where round 3's open put it. Strict-Valid on
the #5004 build, with the two standing `STRICT_INPUT_UNBOUND` warnings.

## Procedure

Upload. Pull (control). Cliff opens the case, no selection, no edit. Pull (round 1).
Cliff selects List Emails and then Wait for HTTP Webhook, no edit. Pull (round 2).
Delete.

## Predictions

| # | Prediction | Falsified if |
|---|---|---|
| R1 | control: plan, entry points, bindings, descriptor byte-identical | any differs |
| R2 | round 1: `uniqueId` and `entryPointId` both unchanged | either changes |
| R3 | round 1: both connector tasks byte-identical (as round 3) | either changes |
| R4 | round 2: the selected connector tasks get `activityConfigurationVersion: v2` and re-minted output ids | neither changes |
| R5 | round 2: `uniqueId` and `entryPointId` still unchanged | either changes |
| R6 | rounds 1 and 2: the 13 non-connector tasks unchanged | any change |

Credence: R2 is the fix under test. R4 is a guess from one observation (the
MST-16423 retest, where List Emails was selected).

## Reading the result

- R2 holds: the CLI fix is to write `entryPointId` = `uniqueId` on every trigger.
- R2 falsified: the Designer re-mints regardless, and the CLI cannot keep the id.
- R4 holds: an unedited open is a no-op on connector tasks, and the v2 upgrade
  happens on selection.
- R4 falsified: the v2 trigger is still unknown.
