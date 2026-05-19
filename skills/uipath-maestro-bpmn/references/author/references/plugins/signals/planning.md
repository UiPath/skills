# Signal Planning

Signals are preserve-only for current Maestro BPMN authoring. Use this
reference only when inspecting or preserving imported signal throw/catch
behavior.

## When to use

- An imported or brownfield BPMN file already contains signal definitions or
  signal event definitions.
- The user asks why signal-based behavior is not regenerated.
- You need to preserve imported signal XML while editing unrelated supported
  process structure.

## Planning steps

1. Identify the existing signal definitions and event references.
2. Preserve them unchanged unless the user explicitly asks to remove or replace
   them.
3. Route new behavior through supported message, timer, receive-task,
   Integration Service, or gateway patterns instead of adding new signals.
4. Report that signal regeneration is unsupported until current product and CLI
   validation confirm it.

## Executable boundary

Do not generate new `bpmn:signal` definitions or
`bpmn:signalEventDefinition` elements in new source.

- Preserve-only: imported `bpmn:signal` definitions, signal event references,
  local throw/catch topology, labels, variables, mappings, and diagram
  geometry.
- Unsupported for regeneration: runtime subscription registration,
  cross-process correlation, payload schema versioning, tenant/folder/resource
  identifiers, and any non-BPMN binding needed for deployed execution.

## Model may draft

- No new signal BPMN.
- Only preservation of imported signal XML while applying unrelated supported
  edits.

## Stop conditions

Stop before Operate when imported signal behavior is expected to execute and no
current runtime validation evidence is available.
