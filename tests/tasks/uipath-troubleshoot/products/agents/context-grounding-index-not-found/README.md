# Agent Context Grounding - Index Not Found

Faithful-replay scenario for the `uipath-troubleshoot` skill. It covers an
Agents runtime failure where a context grounding tool span reports
`ContextGroundingIndex not found`.

## What this exercises

The trace contains a `contextGroundingTool` span for `SupportKnowledge` with a
missing `support-kb-prod` index. The local agent project has a matching
`SupportAgent/resources/SupportKnowledge/resource.json` that points to
`indexName: support-kb-prod` in `folderPath: Shared/Agents`. The mocked
`uip context-grounding list --folder-path Shared/Agents` response returns no
matching index.

The agent should diagnose a deleted or never-created Context Grounding index,
then recommend the current lifecycle:

- inspect the trace with `uip traces spans get`
- inspect the agent-side context `resource.json`
- recreate or relink the index with `uip context-grounding`
- after a resource edit, run `uip agent refresh` and `uip agent validate`
- after successful validation, ask whether the user wants to upload or
  publish/deploy the corrected solution

It must not recommend deprecated agent context-management, standalone publish,
or run-status commands.

## Mock surface

| Command | Fixture |
|---|---|
| `traces spans get <trace-id>` | `trace-context-index-missing.json` |
| `context-grounding list --folder-path Shared/Agents` | `context-grounding-list-empty.json` |
| `context-grounding retrieve` | `context-grounding-retrieve.json` (not found) |
| `agent validate` | `agent-validate.json` |
| repair/upload/publish/deploy commands attempted without approval | `repair-command-denied.json` |
