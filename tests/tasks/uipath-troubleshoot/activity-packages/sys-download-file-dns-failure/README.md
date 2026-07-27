# Download File Failure — DNS / Transport Failure

This scenario replays a real faulted Orchestrator job where the
`Download File from URL` activity fails at the transport layer. The job
throws `System.Net.Http.HttpRequestException` wrapping a
`System.Net.Sockets.SocketException` ("The requested name is valid, but
no data of the requested type was found") — a DNS / name-resolution
failure for the target host.

## What this scenario uncovers

**Root Cause:** The download host
`files.acme-vendorportal.example.com` does not resolve from the robot.
The failure is at the network/transport layer (DNS), not a missing file,
HTTP 404, or authentication error.

This maps to:
`references/activity-packages/system-activities/playbooks/download-file-failed.md`
(the "Transport failure — HttpRequestException" branch).

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` (manifest-driven Python dispatcher) |
| `process/` | snapshot of the failing UiPath project (`Main.xaml` + `project.json`) |
| `fixtures/mocks/responses/*.json` | canned `uip` responses replaying the captured job/logs |
| `fixtures/mocks/responses/manifest.json` | dispatch table mapping each command pattern to its fixture |

## Success criteria

The test scores the **conclusion**, not the trajectory:

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched the correct playbook AND reached the same root cause as `RESOLUTION.md`
- Specifically, the agent must name a DNS / name-resolution / transport failure for the host, not a file-not-found or auth failure
