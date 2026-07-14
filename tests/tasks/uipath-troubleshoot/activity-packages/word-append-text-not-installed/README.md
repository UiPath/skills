# Append Text Failure - Word Not Installed on the Server (cross-ref)

This scenario reproduces an `Append Text` COM startup failure on a
locked-down server with no desktop Word: the `Word Application Scope` can't
create the `Word.Application` COM object and faults with `REGDB_E_CLASSNOTREG`
/ "make sure Word application is installed".

## What this scenario uncovers

**Root Cause:** App-Integration `Append Text` runs inside a Word Application
Scope (Interop), which needs a registered desktop Word. The server has none,
so the scope faults at startup. "Worked on dev, fails on the server" points
at a host-environment cause.

This is a **cross-activity validation** of the shared signature:
`references/activity-packages/word-activities/playbooks/word-scope-com-not-installed.md`

The correct agent behavior is to match the Word-not-installed signature and
recommend either installing desktop Word **or** switching to the standalone
**Word Document `Append Text`** (OpenXML, no Word install) — the
Append-Text-specific, server-friendly path — without fabricating host
actions.

## How this test reproduces it

| Layer | Source |
|---|---|
| `mocks/uip` + `mocks/uip.cmd` | shared from `../_shared/mock_template/` |
| `process/` | hand-authored UiPath project; `Word Application Scope` + `Append Text` on a server with no Word |
| `fixtures/mocks/responses/*.json` | **synthetic** canned `uip` responses authored from the playbook signature |
| `fixtures/mocks/responses/manifest.json` | dispatch table |

> **Note on fixtures.** The faulted job's `REGDB_E_CLASSNOTREG` on the
> `Word.Application` CLSID `{000209FF-...}` at scope startup is the same
> signature as the Word Application Scope not-installed case; this scenario
> confirms the agent routes an **Append Text** server failure to that shared
> playbook and gives the Word-Document-activities alternative.

## Success criteria

- Agent invoked the `uipath-troubleshoot` skill
- Agent matched `word-scope-com-not-installed.md` (the shared Word-not-installed signature)
- Agent identified desktop Word missing on the server as the cause and
  recommended installing Word **or** switching to the standalone Word
  Document Append Text (no Word install) — without fabricating host actions
