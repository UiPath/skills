# rpa-is-folder-permission-cns

Reproduces the highest-volume *distinct-fix* Connection Service failure seen in
production telemetry: an unattended job faults at a connector activity because
the **robot account lacks the `Connections.View` folder permission** on the
folder holding the Integration Service connection — surfaced as `CNS1045`
inside the activity's `DAP-GE-3000` wrapper. The classic signature is
"debug works, unattended fails", which routinely gets misdiagnosed as a
connection-authentication problem.

Fixtures are hand-authored from the production error signature (Connection
Service `FailureUserMessageKey: FolderAuth.403.CNS1045`) rather than extracted
from a live session; shapes mirror the sibling `rpa-is-*-dap` scenarios.

## How this test reproduces it

| Layer | Simulation |
|---|---|
| Faulted job | `or jobs list/get/logs` fixtures: `InvoiceSync` unattended run faulted at "Send Invoice Email" with the `CNS1045` message naming the permission and folder key |
| Connection state | `is connections ping` returns **Success** (the connection itself is healthy — the decisive evidence that re-authentication is the wrong fix) |
| Connection location | `is connections list --folder-key <Finance>` shows the Enabled Outlook connection; the job folder itself has none |
| Red herring | The "works in Studio" report tempts an auth/token diagnosis; the log's explicit permission message must win |

## Success criteria

- `skill_triggered` — the uipath-troubleshoot skill actually ran
- `llm_judge` vs [RESOLUTION.md](./RESOLUTION.md) — root cause is the robot's missing folder permission; fix is granting `Connections.View` (or moving the connection), explicitly **not** re-authentication
