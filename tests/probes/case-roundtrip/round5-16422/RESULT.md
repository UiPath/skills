# MST-16422 round 5 result, 2026-10-09

Prediction: `PREDICTION.md` beside this file, committed (88c5d807a) before the upload.
Built with UiPath/cli#5037 (920fb5595). Uploaded 09:17 MDT (`Action: Imported`), control
pull 09:17, Cliff opened the case with nothing selected, round 1 pull 09:18, deleted 09:19.

| # | Result |
|---|---|
| F1 control byte-identical | **holds** |
| F2 `entry-points.json` byte-identical | **falsified on one byte only**: the CLI ends the file with a newline and the Designer's save does not. Parsed, the file is identical: same `uniqueId` (dced5eda…), `filePath`, input and output. Round 4's input was written without a trailing newline, which is why it came back byte-identical |
| F3 trigger `entryPointId` unchanged | **holds**: `{"serviceType": "None", "entryPointId": "dced5eda…"}` before and after |
| F4 the open saved | **holds**: `caseplan.case.bpmn` and `layout` added, version 32.0.4 |

**Verdict:** a plan written by #5037's `case init` and `sdd convert` keeps its entry-point
`uniqueId` through the first Designer save. MST-16422's re-mint is fixed by #5037. The
trailing newline is formatting, not identity. The CLI could drop it to make the file
byte-stable, but nothing keys on it.
