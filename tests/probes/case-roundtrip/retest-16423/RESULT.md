# MST-16423 retest result, 2026-10-08

Prediction: `PREDICTION.md` beside this file, written by the CLI work stream and
committed (e2c6c374a) before the upload.

## Input

The same golden as MST-15831 (cm_golden_expense, nightly 2026-10-05), re-fetched
unredacted from the nightly artifact. Its two connector tasks were re-emitted with
`uip maestro case splice` and its sidecar with `uip maestro case bindings sync`, both
from the CLI pin at c5fe33417 (tree identical to branch fix/case-schema-32-0-4 head
a9edd5863).

The re-splice kept every connector id and every context and input value, and changed
only what MST-16423 targets:
- the designer's context order;
- `value == var` on each output;
- `data.bindings: []`;
- no `activityConfigurationVersion`.

The other 13 tasks and the root bindings were untouched.

Pre-upload checks, all held:
- version 32.0.3;
- no `activityConfigurationVersion`;
- every connector output `value == var`;
- `SolutionsSupport` on every app and process entry of `bindings_v2.json`;
- strict `--sdd` Valid, with the two warnings the golden always carried.

## Run

| Step | When | |
|---|---|---|
| Upload | 09:44 MDT | fresh name CMGoldenExpenseRetest16423, fresh SolutionId; `Action: Imported` |
| Control pull | 09:45 | upload only: plan byte-identical, two nulls added to `project.uiproj` |
| Round 1 pull | 09:46 | Cliff opened the case and selected List Emails (no edit). The canvas showed it configured: activity "Get Email List", the Outlook connection, folder Inbox, no warning |
| Delete | 09:47 | solution deleted; a re-download fails |

## Scored against the prediction

| # | Prediction | Result |
|---|---|---|
| P1 | version 32.0.3 → 32.0.4 on open | **holds** |
| P2 | the designer still adds `activityConfigurationVersion: v2` and still upgrades from the catalog | **holds**. Both tasks get `v2`, and List Emails' response body goes `object` → `array`. On "input body defaults": the webhook's input is unchanged, while List Emails' `queryParameters.body` is rewritten and `pathParameters.body` dropped |
| P3 | context order unchanged apart from the appended flag | **holds** |
| P4 | every output keeps `value == var` | **holds** |
| P5 | `data.bindings: []` survives | **holds** |
| P6 | input ids re-minted (random, `v` + 8) | **holds** |
| P7 | output ids re-minted to name-based ids | **holds**: webhook `response`, `error2`; List Emails `error`; List Emails' `response` keeps its id. The same allocation as MST-15831 |
| P8 | the 6 app/process `bindings_v2` entries come back byte-identical | **holds**, 6 of 6 |
| P9 | the connections lose `value.folderKey`; the webhook's also loses `metadata.ActivityName`; nothing else | **holds** |
| P10 | strict validate on the pin: neither NEWER_THAN_SCHEMA nor SIDECAR_STALE | **holds**: Valid, with the two standing warnings only |
| P11 | the 13 non-connector tasks unchanged | **holds**, 13 of 13 |

**11 of 11 hold.** P2 holding is the result that matters. The shape the CLI now emits
does not suppress the designer's v2 upgrade, so MST-16423 does not need revisiting.
An unedited open is still not a no-op on connector tasks, as predicted: the v2 flag,
the catalog re-fetch and the id re-mints still change the file.

## Not predicted, recorded

- The entry-point `uniqueId` was re-minted again on first save (b6842084… → aef0905a…),
  and `filePath` moved to `caseplan.case.bpmn`. This is MST-16422. Its fix needs a plan
  already named `caseplan.case`, which this golden was not; the skill now writes that
  name once `case init` seeds it.
- `layout` was added, as in MST-15831.

The raw pulls are redacted (webhook path, mailbox item ids) and kept outside the repo.
