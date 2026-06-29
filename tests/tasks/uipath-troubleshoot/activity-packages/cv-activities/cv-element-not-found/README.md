# CV Click — ElementNotFound (descriptor no longer matches the screen) — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim `uip` CLI
responses captured from that session (scrubbed).

## What the original session uncovered

The user asked why their last job in folder `Shared` failed. The most recent
job, process **CV** (key `37e7a8bb-d207-4db4-8ebf-f0ccc7aa85e9`), faulted with
`UiPath.CV.ElementNotFoundException: Element not found` thrown from the
Computer Vision **CV Click** activity (`CvClickWithDescriptor`, "CV Click -
'Button'") inside the **CV Screen Scope** (`CVScope`, "CV Screen Scope
'msedge.exe  Google'") in `CV_ElementNotFound.xaml`. The find could not match
its locked descriptor geometry against the live `msedge.exe / Google` screen
and the retry loop exhausted its timeout — timeout expiry surfaces AS
`ElementNotFoundException` (there is no separate `TimeoutException`).

### Verdict

**Branch A — genuine descriptor mismatch — is the operative cause:** the
captured descriptor (target Button + two anchor Buttons) no longer matches the
current page, so CV returns no matching region within `TimeoutMS`. **Branch B**
(scope root lost / screenshot-refresh failure) cannot be fully excluded from
job-level evidence alone — confirming it requires the host-side
`*_ComputerVision` runtime dump on the run machine (unavailable from this
session). The fix is to re-indicate the CV Click target in Studio to regenerate
the descriptor — **not** to merely raise `TimeoutMS` (geometry/match problem,
not time) — after confirming Branch A vs B via the dump.

Ruled out: invalid descriptor, scroll-search exhaustion, cell-targeting, CV
server / auth / throttling / network, scope-setup failure, action-failed-after-find.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session's investigation `raw/` outputs |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |
| `process/` | snapshot of the failing `CV` project — `project.json` + `CV_ElementNotFound.xaml` only |

### Trace spans

One `RobotJob` span was recorded for this job; both trace-retrieval forms
(`or jobs traces <key>` and `traces spans get --job-key <key>`) replay it. Its
`Attributes` carry the full `UiPath.CV.ElementNotFoundException` .NET stack with
the `CvClickWithDescriptor.EndExecute` faulting frame propagating through
`CVScope.OnFault` — confirming the fault is the CV Click find, not scope setup
or a downstream action. No per-activity child spans were emitted, so the trace
adds the verbatim stack but no attribute-level disambiguation beyond `jobs get`.

### Fixture derivations and scrubs

- `or-jobs-logs-...-level-error.json` is the recorded Error-level log query (the
  only logs raw captured); the generic logs rule maps to the same fixture — the
  exception row is the only diagnostic content.
- No `--state Faulted` jobs-list raw was recorded, so the folder-key rule
  substring-matches `--state Faulted` variants and returns the full recorded
  list. The failing CV job is the most recent row.
- Standard scrubs applied: run-machine hostname → `MOCK-HOST`; workspace /
  Orchestrator-identity email → `original_email@test.com`; local Windows account
  → `UIPATH\REPLACEMENT_USER`; the CV Screen Scope `ApiKey` literal in the
  snapshotted `CV_ElementNotFound.xaml` → `MOCK_CV_API_KEY`. Job and folder keys
  and the `Element not found` / `ElementNotFoundException` error text are kept
  verbatim.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent's final response reaches the same root cause and fix as `RESOLUTION.md`
