# rpa-is-personal-workspace-connection-cns

Reproduces the classic cross-workspace Connection Service failure: a process
was published bound to a connection living in the **author's personal
workspace**, so the unattended robot cannot resolve it — Connection Service
returns **HTTP 404, error code `CNS1049`** ("connection is on a personal
folder"), surfaced as `DAP-GE-3000` at the connector activity. The trap this
scenario tests: a 404 here does NOT mean the connection was deleted, and
neither re-authentication nor recreating-in-place fixes it — the connection
must live in a shared folder the robot can reach.

Fixtures are hand-authored from the production error signature (Connection
Service traces `StatusCode: NotFound, ErrorCode: "CNS1049"` with the
personal-folder message); shapes mirror the sibling `rpa-is-*-dap` scenarios.

## How this test reproduces it

| Layer | Simulation |
|---|---|
| Faulted job | `or jobs list/get/logs`: `NewHireDocs` unattended run faulted at "Upload Offer Letter" with the `CNS1049` personal-folder message |
| Job folder | `is connections list --folder-key <Onboarding>` returns **no connections** — nothing for the robot to resolve |
| The real location | `is connections list --connection-id <id>` shows the OneDrive connection alive and Enabled in "Personal Workspace - priya.sharma" |
| Disambiguation | `ping` fails 404 with the personal-folder message — deleted vs cross-workspace must be decided from the connection's folder, not the 404 alone |

## Success criteria

- `skill_triggered` — the uipath-troubleshoot skill actually ran
- `llm_judge` vs [RESOLUTION.md](./RESOLUTION.md) — root cause is the personal-workspace-bound connection; fix is creating/moving the connection into the shared folder and rebinding — **not** re-authentication and **not** "the connection was deleted"
