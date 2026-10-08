# MST-16423 / 16424 / 16421 retest: prediction (written before upload, 2026-10-08)

CLI: branch `fix/case-schema-32-0-4` at a9edd5863 (tree identical to the pin
`~/src/cli-roundtrip-pin-c5fe33417`). Golden: `cm_golden_expense`, re-emitted
with that build. Same procedure as MST-15831: upload, pull (control), open in
the Case Designer with no edit, pull (round 1).

## What the CLI now writes (the input)

- version `32.0.3` (the floor), not 32.0.4
- connector tasks: context in the Designer's order; each output `value` = `var`;
  `data.bindings: []` where absent. **No** `activityConfigurationVersion`
- bindings_v2.json: app/process entries with `id`, flagged/labelled slots and
  `SolutionsSupport`/`BindingsVersion`/`DisplayLabel`/`ActivityName` metadata;
  connection entries with flagged/labelled `ConnectionId` and `folderKey` kept

## Predictions for round 1 (each falsifiable by the pull)

| # | Prediction | Falsified if |
|---|---|---|
| P1 | version still goes 32.0.3 → 32.0.4 on open | stays 32.0.3 |
| P2 | the Designer still adds `activityConfigurationVersion: "v2"` to both connector tasks and still re-fetches from the catalog (output schema descriptions, List Emails' response body becomes an array, input body defaults) — i.e. not stamping the flag did not stop the upgrade | flag absent after open, or the catalog upgrade does not happen |
| P3 | connector `context` order is unchanged by the open apart from the appended flag | any entry moves |
| P4 | every output keeps a `value` equal to its `var` (now present before the open) | a `value` removed or differing from `var` |
| P5 | `data.bindings: []` survives on both connector tasks | removed or changed |
| P6 | input ids are still re-minted (random, `v` + 8) | input ids survive |
| P7 | output ids are still re-minted to name-based ids (`response`, `error`, …) — the CLI does not emit them | output ids survive |
| P8 | bindings_v2.json: the 6 app/process entries come back byte-identical | any app/process entry changes |
| P9 | bindings_v2.json: both connections lose `value.folderKey`; the webhook's loses `metadata.ActivityName`; nothing else changes | any other connection field changes, or folderKey survives |
| P10 | `uip maestro case validate round1/caseplan.case --strict` on the pin: no `CASE_MGMT_VERSION_NEWER_THAN_SCHEMA`, no `STRICT_BINDINGS_SIDECAR_STALE` | either appears |
| P11 | the 13 non-connector tasks: unchanged, as in MST-15831 | any change |

## Net expectation

Fewer connector-task changes on open than MST-15831 (order, `value`,
`bindings` no longer change) but **not** a no-op: P2, P6, P7 still change the
file. bindings_v2 changes only in the two accepted connection fields.

If P2 is falsified (no v2 upgrade happens because something else we now write
signals "already v2"), that is the important finding: the CLI would then be
leaving connector tasks un-upgraded, and 16423's shape needs revisiting.
