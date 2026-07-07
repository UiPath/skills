# O365 Email Trigger — Integration Service 503 Outage — Faithful Replay

This scenario replays a real UiPath troubleshooting investigation where the
agent reached a verified resolution. The fixtures are the verbatim
`uip` CLI responses captured from that session (scrubbed).

## What the original session uncovered

The user asked why their last job in folder `Shared` failed. The most recent
job, `ERN_O365_TriggerConnFailure` (key `1db8bac1-ecc2-4670-843e-ff5f9a26c532`),
faulted after ~2.4 s when its **New Email Received** trigger activity
(`NewEmailReceived`, "New Email Received via dead connection (expect
ConnectionHttpException)" in `O365_TriggerConnFailure.xaml`) could not reach
the Integration Service connection layer. The HTTP request received 503; the
connection client exhausted its internal retries
(`HttpConnectionServiceClient.RequestWithRetryAsync`) and threw
`UiPath.ConnectionClient.Contracts.ConnectionHttpException: Service
Unavailable`, surfaced as `Office365Exception: Service Unavailable`. No
Microsoft Graph call was reached — the failure is in the UiPath Integration
Service layer, not Outlook. Fix: retry once the connection service recovers
(verify via an IS connections probe) and escalate as a service incident if
the 503 persists.

### Live-probe evidence pattern

This scenario's distinguishing evidence is a **live probe of the platform**,
not just job artifacts: the original investigation ran `uip is connections
list --folder-key <Shared>` three times (~35 min after the job) and received
HTTP 503 "no healthy upstream" on every attempt — confirming a real,
ongoing Integration Service outage. The 5xx status class rules out the
sibling causes from the playbook's branch table: connection deleted/not
shared (404-class) and authorization expired/revoked (401/403-class). The
mock replays the recorded 503 Failure payload (exit code 1) for every
`is connections list` variant so the eval agent can reproduce the probe.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `fixtures/mocks/responses/*.json` | real stdout extracted verbatim from the session's investigation `raw/` outputs |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its recorded fixture |

No `process/` snapshot — the original investigation determined the root cause
from platform evidence alone (job Info/logs/traces carry the full
ConnectionHttpException stack; the live IS probe carries the outage proof).

### Trace spans

Three spans were recorded for this job and both trace retrieval forms
(`or jobs traces <key>` and `traces spans get --job-key <key>`) replay them:
the RobotJob span (full exception stack in Attributes), the
`NewEmailReceived` activity span (connector `uipath-microsoft-outlook365`,
`UseConnectionService=True`), and the "operation failed" error span.

### IS 503 fixture choice

The three recorded probe attempts (`triage-is-connections.json`,
`triage-is-connections-retry.json`, `H1-is-connections-attempt3.json`)
were byte-identical, so one representative fixture
(`is-connections-list-folder-key-1965a46b-db4e-469e-aaaa-7e0b379cb34d-503.json`)
answers all probe retries.

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
    --scenario-name o365-trigger-connection-503 --apply
```
