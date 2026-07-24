# Web Activities — ST-SEC-009 SecureString Misusage (design-time)

This scenario reproduces a **design-time Workflow Analyzer** failure (not a
runtime fault): the `TicketApiClient` project fails validation and won't
publish because rule **`ST-SEC-009` (SecureString Misusage)** fires at Error
severity on the sequence around an HTTP Request activity. The process has
**never run** — there are no Orchestrator jobs.

## What this scenario uncovers

**Root Cause:** `Main.xaml` retrieves a bearer token as a `SecureString`
(`GetRobotCredential`, output `apiToken`), then an Assign converts it to a
plain `String` — `"Bearer " + new System.Net.NetworkCredential(String.Empty,
apiToken).Password` — to populate the HTTP Request `Authorization` header. The
`SecureString` variable is also scoped to the whole sequence. Casting
`SecureString`→`String` and over-wide `SecureString` scope are exactly what
`ST-SEC-009` flags. This is a **secure-coding finding, not an activity bug**.

This maps to:
`references/activity-packages/web-activities/playbooks/securestring-misuse-analyzer.md`.

The correct agent behavior is to identify the `SecureString`→`String`
conversion feeding the header (plus the wide variable scope) from the project
source, give the real fix — Get Credential + minimal scope + Orchestrator
credential asset + convert only at the point of use, optionally excluding the
activity namespace from the rule — and **explicitly reject** the user's
floated "upgrade `UiPath.WebAPI.Activities` to 2.3.0 for native secure
handling" fix, which does NOT resolve ST-SEC-009 (the header dictionary is
still plain-string).

## How this test reproduces it

| Layer | Source |
|---|---|
| `m/uip` dispatcher | shared from `../../_shared/mock_template/` |
| `process/` | hand-authored Web Activities project whose `Main.xaml` converts a `SecureString` token to `String` (`NetworkCredential(...).Password`) into the HTTP `Authorization` header, with the `SecureString` variable scoped sequence-wide |
| `data/m/r/*.json` | folders list + **empty** job lists (the process never ran) |
| `data/m/r/manifest.json` | dispatch table (folders, empty jobs, `docsai ask` passthrough, permissive `[]` fallback) |

> **Note on fixtures.** Like the `uia-dependency-version-conflict` scenario,
> this has **no faulted job** by design — it is a design-time analyzer
> finding, so `or jobs list` returns empty and the agent must diagnose from
> `Main.xaml` + the rule id in the prompt. It tests whether the agent gives
> the real secure-coding fix and rejects the false package-upgrade fix.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `securestring-misuse-analyzer.md`
- Agent identified the `SecureString`→`String` conversion feeding the HTTP
  header (and the over-wide SecureString scope) as the ST-SEC-009 cause,
  reasoning from the project source; recommended the real fix (Get Credential
  + minimal scope + Orchestrator credential asset + convert at point of use,
  optionally exclude the activity namespace from the rule); and rejected the
  false "upgrade WebAPI to 2.3.0" fix — without fabricating actions
