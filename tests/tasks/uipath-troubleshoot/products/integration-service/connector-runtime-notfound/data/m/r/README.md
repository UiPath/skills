# Connector Activity — RuntimeException DAP-RT-1101 (operation NotFound)

Faithful-replay scenario for the `uipath-troubleshoot` skill. Covers the
`RuntimeException` case of TROUB-139 (`ConnectorActivity`).

## What this exercises

A `ConnectorActivity` ("Google Drive: Get File or Folder") resolves its connection
fine, sends the request, and Google responds **HTTP 404 (File not found)**. The IS
runtime surfaces this as `RuntimeException` with error code **DAP-RT-1101** /
`Status code: NotFound`, carrying a `ProviderMessage` block with the provider's own
404 / `reason=notFound` / `location=fileId`. The agent must distinguish this
**operation-level** failure (missing file / wrong ID) from a connection-resolution
failure (`DAP-GE-*`), and recommend correcting the referenced file identifier.

> **Live-anchored:** built from a **real Orchestrator faulted job** on alpha — a
> Google Drive `Get File or Folder` ConnectorActivity run by a robot against a live
> connection with a non-existent file ID. The error text (signature, `ProviderMessage`,
> stack frames) and the job envelope are verbatim from that job (identities scrubbed).

## Mock surface

| Command | Fixture |
|---|---|
| `or folders list` | `or-folders-list.json` |
| `or jobs list --folder-key <Shared> [--state Faulted]` | `or-jobs-list-faulted.json` |
| `or jobs get <key>` | `or-jobs-get.json` (Faulted, Info = real DAP-RT-1101 NotFound + ProviderMessage) |
| `or jobs logs <key> --level Error` | `or-jobs-logs.json` |
| `docsai ask` | passthrough |

No project source is staged — the conclusion is reachable from the job evidence
(the failing file ID is in `InputArguments` and the `ProviderMessage`).

## Success criteria

`skill_triggered` + `llm_judge` (graded against `RESOLUTION.md`, final response only).
