# Inline Agent in a Flow — Moved

**Inline agents are owned by the `uipath-maestro-flow` skill.** Tell the user to use that skill (its inline-agent plugin) — do not author inline agents from here.

The architecture changed: the full agent definition now lives **in the `.flow` file** — the `uipath.agent.autonomous` node embeds prompts, model, settings, and typed outputs directly in its `inputs`, and each attached resource (tool, context, escalation) is a flow node carrying its full config. The UUID-named subdirectory this file used to document is a **derived artifact**: the flow canvas regenerates it from the `.flow` on every save. Hand-authored sidecar edits are shadowed on open and overwritten on save.

Consequences for this skill:

1. **Never scaffold with `uip agent init --inline-in-flow`** — legacy; not part of any recipe. There is no agent project to create.
2. **Never edit `<GUID>/agent.json`, `resources/`, or `features/` inside a flow project** — derived files; the `.flow` wins.
3. **`uip agent refresh` / `uip agent validate` do not apply** to inline agents — validation is `uip maestro flow validate`.
4. This skill remains authoritative for **standalone** low-code agent projects only.

If asked to build or edit an inline agent, hand off to `uipath-maestro-flow`. If you find a legacy flow whose agent node only carries `inputs.source` (a shell, definition still in the subdirectory), the flow skill's inline-agent plugin documents the migration.
