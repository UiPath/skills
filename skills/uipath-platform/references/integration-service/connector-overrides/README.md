# Connector Overrides

Per-connector override files. Each `<connector-key>.md` aggregates all overrides that apply to one connector, organized as H2 sections by override type. Currently one override type is defined (Connection Selection); more may be added.

---

## Connection Selection Override

Connector-specific carve-outs from the auto-select rule in [../connections.md — Selecting a Connection](../connections.md#selecting-a-connection). 99% of connectors follow the default rule (silent auto-select when the default enabled connection lives in the user's personal workspace). Entries here are operations where the default rule fails because the bound connection cannot satisfy operation-specific requirements (e.g., bot scope, BYOA).

### How the override fires

1. Extract the connector key from the node type — `uipath.connector.<key>.<op>`, `uipath.connector.trigger.<key>.<op>`.
2. Look up the key in the Connector-Specific Overrides table in [../connections.md](../connections.md#connector-specific-overrides).
3. If the entry's scope (node-type pattern or operation list) matches, read the linked file and follow its rules. Override supersedes the auto-select rule.
4. No match → proceed to the auto-select rule.

### File schema (Connection Selection section of a connector file)

The `## Connection Selection Override` section of a connector file follows this shape:

- **`## Connection Selection Override`** — H2 heading for this override type.
- **`### When this override applies`** — node-type pattern or operation list. Multiple scopes on one connector → H4 sub-sections.
- **`### Override behavior`** — auto-select disabled (default for all overrides), list filter (optional), post-selection verification (optional), recovery on empty.
- **`### Why`** — one-paragraph rationale.
- **`### User-facing presentation`** — exact prefix wording the agent uses when presenting the list.

The connector file's H1 is `# <Connector Display Name> — Connector Overrides` with `**Connector key:** <kebab-case-key>` directly below.

---

## How to add a new override

1. Add `<connector-key>.md` in this directory using the schema above.
2. Add a row to the Connector-Specific Overrides table in [../connections.md](../connections.md#connector-specific-overrides).
3. Specify the node-type pattern precisely — overrides are operation-scoped, not blanket connector-wide.

## File naming

`<connector-key>.md` — kebab-case connector key as it appears in `uip is connectors list`. Multiple override scopes for one connector live in the same file as H4 sub-sections under the relevant H3.

## Existing overrides

- [uipath-microsoft-teams.md](uipath-microsoft-teams.md) — `send-bot-*` activities require bot scope.
- [uipath-salesforce-slack.md](uipath-salesforce-slack.md) — Trigger node types require BYOA.
