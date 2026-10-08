# Round-trip probe result (MST-15831), 2026-10-08

Golden `cm_golden_expense` (claude-opus-5-5, nightly 2026-10-05), uploaded to Studio Web
on alpha (codereval / DefaultTenant) at 08:36 MDT as a new solution (`Data.Action:
Imported`, SolutionId 7a698b3d-e42c-4655-9d00-08df25493a03). CLI: pin 59cceb569. The
prediction (`PREDICTION.json`) was committed at 1688ac398, before the upload.

Three pulls, each by `uip solution download --extract`:

| Pull | When | What happened before it |
|---|---|---|
| control | 08:37 | nothing: uploaded, never opened |
| round 1 | 08:39 | Cliff opened the case in the Case Designer and made no edit. Studio Web autosaves; there is no Save button, so "save without editing" is "open" |
| round 2 | 08:43 | Cliff renamed one task, "Wait for timer - S7" → "Wait for timer - S7 renamed" |

## The control: upload alone changes nothing in the plan

`caseplan.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json` and
`operate.json` came back byte-identical. The only plan-project change was two null
fields added to `project.uiproj` (`Description`, `MainFile`). So every divergence below
was written by the designer, on open.

## Round 1: opening the case, no edit

The designer's own converter round-trips the pre-open plan with zero divergences
(`simulate.cjs`), so none of this comes from `@uipath/case-schema`; it is the front end.

| # | Divergence | Predicted | Disposition |
|---|---|---|---|
| 1 | `caseplan.json` renamed to `caseplan.case` | not named | **deliberate**: Studio Web renames the plan to its newest name on every save and reads all four names (the CLI's `case-plan-file.ts` documents it and resolves `caseplan.case` first) |
| 2 | `caseplan.case.bpmn` added | C2 side-car, uncertain | **deliberate**: the compiled side-car. `entry-points.json`'s `filePath` was rewritten to `/content/caseplan.case.bpmn#trigger_1`, which names it, so the pair is **consistent** |
| 3 | top-level `layout` added (`layout.nodes`) | C1, change | **predicted, deliberate**: the canvas layout. No per-node geometry was written |
| 4 | `version` 32.0.3 → **32.0.4** | S8, survive | **violated. To file.** The CLI's vendored schema accepts only 32.0.3, so `validate` fails with `CASE_MGMT_VERSION_NEWER_THAN_SCHEMA`: the returned plan is not CLI-editable on this build |
| 5 | `entry-points.json` `uniqueId` b6842084… → 200233d5… | S3, survive | **violated. To file.** Orchestrator keys bindings on `uniqueId`. Re-minted once: round 2's save left it unchanged |
| 6 | connector tasks (Wait for HTTP Webhook, List Emails): input ids re-minted; output ids re-minted to name-based ids (`response`, `error`, `error2`) with a `value` companion added; `activityConfigurationVersion: v2` added to `context`; `data.bindings: []` added | S6, survive | **violated.** Every configured `context` value survives (connectorKey, connection, resourceKey, folderKey, objectName, operation, method, path), so nothing needs a re-configure at file level, and the canvas showed no warning on either task. What changes is the I/O shape: the designer normalises connector tasks to configuration v2 on load. **To file**, as a parity gap: the CLI/skill emits a shape the designer rewrites |
| 7 | `bindings_v2.json` connection resources: `value.folderKey` dropped, `metadata.ActivityName` dropped, `isExpression` and `displayName` added | S5, survive | **violated. To file.** The CLI now reports `STRICT_BINDINGS_SIDECAR_STALE` on the returned project: the designer's projection and the CLI's disagree, and one of them is wrong |
| 8 | `evals/<id>/…` scaffold added (evaluation set, trajectory evaluator, `initialized.json`) | not named | Studio Web's, outside the plan. Explained as a designer scaffold; not filed |
| 9 | the 13 non-connector tasks, every node and task id, every `elementId`, root `bindings`, out-arg companions of non-connector tasks | S1, S2, S4, S7 | **survived**, as predicted |

The scorer reported this round as `misses: [C1-layout]` and violations of S3, S5 and S9.
That run compared `caseplan.json` against a file the designer had deleted. The table
above compares `caseplan.json` with `caseplan.case`, which is the comparison that
means something; the harness now loads any JSON file regardless of extension.

**CLI-editable: no, on this build.**
- `validate --strict --sdd` fails on the version (item 4).
- With the version set back to 32.0.3 (a diagnostic copy, never uploaded), it is strict
  **Valid**, with the three warnings the pre-open plan had plus `STRICT_BINDINGS_SIDECAR_STALE`.
  So the version is the only blocker.
- The CLI's converter run on the returned plan drops the new `layout`. A CLI rewrite
  of a designer-saved plan would silently erase its canvas layout.

## Round 2: one canvas edit

Exactly as predicted: the plan changed in one leaf, that task's `displayName`, and the
compiled BPMN changed with it. `entry-points.json` was byte-identical to round 1, so
the `uniqueId` re-mint happens on the first designer save, not on every save. No id,
`elementId` or reference changed.

## What this golden cannot show (stated before the run; still true)

- **Out-arg companion collapse.** Every output had `id == var`, so a collapse of
  `id != var` cannot appear. The only companion change is item 6's, on connector outputs.
- **References to re-minted connector outputs.** No task or condition in this golden
  references a connector output by id (each old id appeared only as its own `id`/`var`).
  Whether the designer updates such a reference when it re-mints the output id is
  untested, and it is the case that would break.

## Scored against the matrix's hedges

- "Some connector fields need a UI re-configure" (MST-16034): **not observed**. All
  configured values survive the open, and the canvas showed no re-configure state. The
  designer does rewrite the task's I/O to v2, which the hedge may have been describing.
- "Out-arg companions may collapse": **not observable here** (above).
- The prior that more survives than predicted held for the plan's content (every
  non-connector task byte-identical), and failed for the envelope: version,
  `uniqueId` and `bindings_v2` all changed, against "survive" predictions.
