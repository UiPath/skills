# MST-16422 round 5: prediction (written before upload, 2026-10-09)

Round 4 showed that the Designer keeps a hand-written trigger `entryPointId`. Round 5
repeats the check on a plan the CLI wrote itself, with UiPath/cli#5037 (920fb5595,
stacked on #5004).

## Input

Built with that CLI, from a separate clone:
1. `uip solution init`, then `uip maestro case init CMGoldenExpense` inside it;
2. `uip maestro case sdd convert` of the cm_golden_expense SDD (the retest's
   `sdd.md` and `registry-resolved.json`), `--out` the seeded `caseplan.case`;
3. `uip maestro case bindings sync`.

The trigger carries `{"serviceType": "None", "entryPointId": "dced5eda-…"}`, equal to the
entry point's `uniqueId`. Plain validate is Valid. Strict reports connector findings
(context incomplete, output types, folder-key default) because convert leaves 9
`Unresolved` items for the agent, and none of them concern the trigger or the entry
point. No `STRICT_TRIGGER_ENTRY_POINT_ID`.

## Procedure

Upload, pull (control), Cliff opens the case with nothing selected, pull (round 1),
delete.

## Predictions

| # | Prediction | Falsified if |
|---|---|---|
| F1 | control: plan, entry points, bindings, descriptor byte-identical | any differs |
| F2 | round 1: `entry-points.json` byte-identical to the upload | any byte differs |
| F3 | round 1: trigger `entryPointId` unchanged | changed or removed |
| F4 | round 1: the Designer did save (`caseplan.case.bpmn` and `layout` added) | nothing added, so the open did not save and F2/F3 prove nothing |

Pass condition, as agreed with the CLI work stream: F2 and F3 hold, with F4 holding.
