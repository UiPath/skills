# O365 Upload File — Per-File Size Limit Exceeded (maxFileSizeExceeded) — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session (scrubbed).

## What the original session uncovered

The user asked why their last job in folder `Shared` failed. The most recent
job, `ERN_O365_UploadQuotaSize` (key `7fd5e890-f162-4591-a895-e649b09aea02`),
faulted at the legacy **Upload File** activity ("Upload File (point at
oversize file or near-full drive for quota/size errors)" in
`O365_UploadQuotaSize.xaml`) inside the Microsoft 365 Scope. Microsoft Graph
rejected the chunked upload at upload-session creation with a raw
`Microsoft.Graph.ServiceException`: `Code: invalidRequest`, `Message: The
payload of the request was too large`, `Inner error: Code:
maxFileSizeExceeded` — the documented over-size rejection: the file's
declared size exceeds the OneDrive/SharePoint per-file upload limit,
refused before any bytes transferred. Stack:
`LargeFileUploadTask.UploadAsync` / `UploadSliceRequest.PutAsync` /
`SimpleHttpProvider.SendAsync` into `UploadFile.ExecuteAsync`; the raw
`ServiceException` (no `Office365Exception` wrapper) marks the legacy code
path. Ruled out by message form: NOT a storage-quota problem
(`quotaLimitReached` absent), NOT a transient upload-session break, NOT
throttling. Deterministic on every run with the same file. Fix: compress or
split the file, or store it elsewhere and share a link; restart only after
the file is reduced. Playbook:
`references/activity-packages/o365-activities/playbooks/upload-file-quota-or-size.md`.

### Evidence gap: traces unavailable

In the real session job execution traces could NOT be retrieved — `uip
traces spans get --job-key 7fd5e890-...` returned `{"Result": "Failure",
"Message": "Error retrieving trace ID for job"}` with exit code 1. The
replay reproduces that failure faithfully: every trace-retrieval form
(`or jobs traces <key>`, `traces spans get --job-key <key>`, and the
TraceId-positional `traces spans get <32-hex>`) returns the recorded
failure payload with exit code 1. There is no span evidence for this job;
the diagnosis must come from `jobs get` + the Error-level job log alone —
both carry the full ServiceException with the cause-discriminating
`maxFileSizeExceeded` inner code.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session's investigation `raw/` outputs |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

No `process/` snapshot — the original investigation determined the root cause
from platform evidence alone (job Info and the Error-level log carry the full
Graph ServiceException and .NET stack).

### Fixture derivations and scrubs

- `or-jobs-logs-...-level-error.json` is the recorded Error-level log query
  (the only logs raw captured); the generic logs rule maps to the same
  fixture — the exception row is the only diagnostic content.
- `or-jobs-history-...-output-json.json` is the recorded verbatim history:
  Pending → Running → Faulted in ~8 seconds, a clean single execution.
- No `--state Faulted` jobs-list raw was recorded, so there is no
  Faulted-only fixture; the folder-key rule substring-matches
  `--state Faulted` variants and returns the full recorded list.
- `traces-retrieval-error-...json` is the verbatim recorded trace-retrieval
  failure (see Evidence gap above); all trace forms map to it with
  exit code 1. The TraceId-positional form was not attempted in the real
  session, but no span raw exists — serving the same recorded failure
  preserves the evidence gap instead of fabricating an empty span set.
- The uploaded file's actual path and byte size were not in the platform
  evidence (project source unavailable); Graph's rejection of the declared
  size is the authoritative evidence.
- Standard scrubs applied: hostname → `MOCK-HOST`, workspace owner email →
  `original_email@test.com`, Windows account → `UIPATH\REPLACEMENT_USER`.
  Error text, stacks, keys, and timestamps are verbatim.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent's final response reaches the same root cause and fix as `RESOLUTION.md`

## Re-running the extraction

This scenario was hand-built from the investigation's `raw/` verbatim CLI
outputs. If the source investigation changes, update the fixture JSONs
directly and re-run the scrub checks, or regenerate with:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path> --transcript <path> --resolution <path> \
    --scenario-name o365-upload-maxfilesize --apply
```
