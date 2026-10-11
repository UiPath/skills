# MST-16422 round 4 result, 2026-10-09

Prediction: `PREDICTION.md` beside this file, committed (2e3821a67) before the upload.
Uploaded 08:44 MDT (`Action: Imported`), control pull 08:45, Cliff opened the case
with nothing selected (round 1 pull 08:54), then selected List Emails and Wait for HTTP
Webhook with no edit (round 2 pull 08:55), deleted 08:56.

| # | Result |
|---|---|
| R1 control byte-identical | **holds** |
| R2 round 1 keeps `uniqueId` and `entryPointId` | **holds**: 5437d809… before and after. The open did save (sidecar, `layout`, 32.0.4 added), so this is a real save that kept the id |
| R3 round 1 connector tasks byte-identical | **holds**, both |
| R4 round 2 selected connector tasks upgrade | **holds**: both get `activityConfigurationVersion: v2`. Output ids re-minted: webhook `response`, `error3`; List Emails `error` (its `response` keeps its id) |
| R5 round 2 keeps `uniqueId` and `entryPointId` | **holds**; `entry-points.json` byte-identical to round 1 |
| R6 non-connector tasks unchanged | **holds**, 13 of 13 in both rounds |

## What it settles

- **MST-16422.** The Designer keeps a pre-written `entryPointId` and leaves the
  `uniqueId` alone. The shape it writes, and keeps, is a plain GUID string at
  `nodes[<trigger>].data.inputs.entryPointId`, beside `serviceType`
  (`{"serviceType": "None", "entryPointId": "<uniqueId>"}`), equal to the entry's
  `uniqueId` in `entry-points.json`. The CLI fix is to write that field on every
  trigger it writes.
- **Connector v2.** An unedited open is a no-op on connector tasks. The v2 upgrade
  (flag, catalog re-fetch, id re-mints) runs when a connector task is selected on the
  canvas. That explains MST-15831 round 1 and the MST-16423 retest, where tasks were
  clicked. The name-based error id allocation is not stable across sessions:
  `error2` in the earlier rounds, `error3` here.
