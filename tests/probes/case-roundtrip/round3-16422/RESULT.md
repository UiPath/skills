# MST-16422 round 3 result, 2026-10-09

Prediction: `PREDICTION.md` beside this file, committed (72d00b773) before the upload.
Uploaded 08:38 MDT (A and B, `Action: Imported`), control pulls 08:39, Cliff opened
each case with no edit, round 1 pulls 08:40, both solutions deleted 08:41.

| # | Result |
|---|---|
| Q1 control byte-identical | **holds**, both |
| Q2 A keeps `uniqueId` | **falsified**: 9a527e34… → cf036e2d… |
| Q3 B keeps `uniqueId` | **falsified**: 422bd401… → 8f0f32ed… |
| Q4 no rename, `filePath` unchanged, `.bpmn` added | **holds**, both |
| Q5 A 32.0.3 → 32.0.4, B stays | **holds** |
| Q6 layout + connector v2 upgrade | **half**: `layout` added; both connector tasks **byte-identical**, no v2, no id re-mints |
| Q7 non-connector tasks, app/process bindings | **holds**: 13 of 13, 6 of 6; connections lose `folderKey.defaultValue` (and the webhook `metadata.ActivityName`) as before |

## Why the `uniqueId` changes

Neither the name nor the version: the falsifying row of the reading table applies
(both change). The leaf diff names the mechanism. The open adds
`nodes[0].data.inputs.entryPointId` to the trigger node, and its value **is** the
new `uniqueId`, in both variants. MST-15831 round 1 (200233d5…) and the MST-16423
retest (aef0905a…) show the same equality, and every CLI-written plan lacks the
field. The Designer derives `entry-points.json` from the plan: a start event's
`entryPointId` is its entry point's `uniqueId`. A trigger without one gets a fresh
GUID on the first save, which overwrites the CLI's `uniqueId`. Round 2 of MST-15831
kept the id because the field was in the plan by then.

So MST-16422's fix is for the CLI to write `entryPointId` equal to the entry point's
`uniqueId` on every trigger node it writes. Untested until a round trip shows
the Designer keeps a pre-written value.

## Not predicted

- The connector v2 upgrade did not happen on a bare open. In the MST-16423 retest
  Cliff selected List Emails; here no task was selected. Candidate: the upgrade runs
  when a connector task's panel loads, not on open.
- Other open-time additions: root `isPendingParent`, `isInvalidDropTarget`;
  `metadata.caseExecutionTaskErrorHandling`, `caseBpmnConsolidatedCycle`,
  `maestroEngineVersion` added, `caseDirectlyPassTaskOutputs` removed; `name` set to
  the project name.

The pulls stay outside the repo.
