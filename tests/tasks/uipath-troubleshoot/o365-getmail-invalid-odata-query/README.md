# O365 Get Mail Invalid OData Query — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session (scrubbed).

## What the original session uncovered

The user asked why their last job in folder `Shared` failed. The most recent
job, `ERN_O365_InvalidODataQuery` (key `4b4a58f8-6a7c-4af2-8700-1b6479b51028`),
faulted with a raw `Microsoft.Graph.ServiceException` `Code: BadRequest` —
`Invalid filter clause: ')' or operator expected at position 56 in
'(receivedDateTime ge 1900-01-01T00:00:00Z) and (subject equals 'invoice' and
unread is true)'` — thrown by the legacy O365 `GetMail` activity. The
activity prepends the date-range clause itself; the malformed segment is the
user-configured `Query`, which uses natural-language operators (`equals` is
not an OData operator, `unread` is not a Graph message property). Graph
rejected the request at parse time — deterministic, independent of mailbox
content, not auth/throttling/transient. Fix: correct the `Query` to valid
OData (`subject eq 'invoice'`) and/or use the activity's built-in Only Unread
Messages option.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session's investigation `raw/` outputs |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

No `process/` snapshot — the original investigation determined the root cause
from platform evidence alone (job Info/logs carry the full fault stack and
the composed `$filter` echoed verbatim).

### Trace spans

No trace spans were recorded for this job in the original session. Both trace
retrieval forms (`or jobs traces <key>` and `traces spans get --job-key
<key>`) are mocked with a well-formed empty `JobTraces` response so the agent
sees "no spans" rather than an unmocked default. The root cause is fully
visible in `jobs get` / `jobs logs`.

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent's final response reaches the same root cause and fix as `RESOLUTION.md`

## Re-running the extraction

This scenario was hand-built from the investigation's `raw/` verbatim CLI
outputs (the generator's transcript pass is unreliable for this session). If
the source investigation changes, update the fixture JSONs directly and re-run
the scrub checks, or regenerate with:

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
    --investigation <path> --transcript <path> --resolution <path> \
    --scenario-name o365-getmail-invalid-odata-query --apply
```
