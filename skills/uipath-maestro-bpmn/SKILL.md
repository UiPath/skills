---
name: uipath-maestro-bpmn
description: "Author valid UiPath-compatible Maestro BPMN XML (.bpmn) from a natural-language description, driven end-to-end by the `uip maestro bpmn registry` CLI. Every UiPath extension element (`uipath:activity`, `uipath:event`, `uipath:mapping`, `uipath:Bindings`) is emitted STRICTLY from registry `xmlTemplate`s — never hand-authored. Discovers real connectors, connections, and Orchestrator processes (RPA, agents, API workflows, agentic/case processes, queues) via `uip maestro bpmn registry pull/list/search/get` and `uip is connections list`; confirms every choice with the user; never fabricates a connection ID, releaseKey, or connectorKey. Covers structural BPMN (events, tasks, gateways, sequence flows), variable declaration, connector enrichment against live Integration Service shapes, and `=js:` gateway expressions with a default branch. Triggers on: 'generate/create/build a Maestro BPMN', '.bpmn file', 'Maestro process XML'. For .flow Maestro flows->uipath-maestro-flow. For case management->uipath-maestro-case."
when_to_use: "User wants to create or author a UiPath Maestro BPMN process as `.bpmn` XML from a description — e.g. 'generate a Maestro BPMN that runs an RPA job then sends a Slack message', 'build a BPMN with an exclusive gateway', 'author Maestro process XML calling connector X'. Also when editing/extending an existing `.bpmn` by adding registry-backed nodes. NOT for `.flow` Maestro flows (->uipath-maestro-flow), case-management apps (->uipath-maestro-case), API workflow JSON (->uipath-api-workflow), or `.xaml`/coded RPA (->uipath-rpa)."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# UiPath Maestro BPMN Authoring

Generate **valid, UiPath-importable Maestro BPMN XML** from a natural-language description. The single source of truth for every UiPath extension is the **Maestro BPMN registry**, queried through the `uip maestro bpmn registry` CLI. You assemble the BPMN graph (events, tasks, gateways, sequence flows); the registry supplies every `uipath:*` payload as a fill-in-the-blanks `xmlTemplate`.

## When to Use This Skill

- User wants to **create a new** Maestro `.bpmn` file from a description.
- User wants to **add nodes** (RPA job, agent, connector activity, HTTP request, message event, gateway) to an existing `.bpmn`.
- User asks how a particular Maestro step type is represented in BPMN XML.
- User asks to wire a Maestro process to a **real** connector, connection, queue, or Orchestrator process.

Do NOT use for: `.flow` Maestro flows (-> `uipath-maestro-flow`), case-management apps (-> `uipath-maestro-case`), API workflow JSON (-> `uipath-api-workflow`), `.xaml` / coded RPA (-> `uipath-rpa`).

## Non-Negotiable Principles

1. **Author UiPath extensions ONLY from registry templates.** Never hand-write a `uipath:activity`, `uipath:event`, `uipath:mapping`, or `uipath:Bindings` element from memory. Always fetch the type's `xmlTemplate` with `uip maestro bpmn registry get <extensionType>` and fill its `{placeholders}`. If a type isn't in the registry, stop and tell the user — do not invent it.
2. **Never fabricate an ID.** Connection IDs, `releaseKey`s, `connectorKey`s, `folderKey`s, queue keys, app IDs — every one comes from discovery (`registry` / `is connections`) or is supplied by the user. A guessed GUID produces a BPMN that imports but fails at runtime.
3. **Confirm before you commit.** This skill is interactive. Confirm the connector/connection/process selection, the overall structure, and the variable set with the user (AskUserQuestion or a plain question) before writing XML. When discovery returns several candidates, present them and let the user pick.
4. **Build in phases, validate at the end.** Discover -> Skeleton -> Enrich + author -> Validate + output. Don't author a connector node before you've enriched it against its real object shape.

## The Four-Phase Flow

### Phase 1 — Discover

Sync the registry, then find the real building blocks. Confirm each choice with the user; never proceed on a fabricated ID.

```bash
# 1. Sync (and authenticate for connectors/processes; OOTB types work without login)
uip login                      # needed to discover connectors & Orchestrator processes
uip maestro bpmn registry pull # caches static extension types + discovered resources

# 2. Browse / search extension types, connectors, processes
uip maestro bpmn registry list                 # first 30; --limit -1 for all
uip maestro bpmn registry search <keyword>     # e.g. slack | queue | agent | connector

# 3. Discover live Integration Service connections (ID + state)
uip is connections list
```

Map the user's intent to extension types using `search` / `list`:
- "Run an RPA workflow / process" -> `Orchestrator.StartJob`
- "Run an agent" -> `Orchestrator.StartAgentJob`; "API workflow" -> `Orchestrator.ExecuteApiWorkflowAsync`
- "Agentic process / case management" -> `Orchestrator.StartAgenticProcess[Async]` / `Orchestrator.StartCaseMgmtProcess[Async]`
- "Queue item" -> `Orchestrator.CreateQueueItem` / `Orchestrator.CreateAndWaitForQueueItem`
- "Call a connector (Slack/Gmail/...)" -> `Intsvc.ActivityExecution`; wait for a connector event -> `Intsvc.WaitForEvent`
- "HTTP request" -> `Intsvc.UnifiedHttpRequest`; "internal message" -> `Maestro.SendMessageEvent` / `Maestro.ReceiveMessageEvent`
- "Human task / action app" -> `Actions.HITL`; "script" -> `BPMN.ScriptTask`; variables -> `BPMN.Variables`

For Orchestrator-resource types (`Orchestrator.*`), the real `releaseKey` / queue key comes from the user or from registry-discovered resources (`registry list` -> `Processes[].ProcessKey`). For `Intsvc.*` types, the `connection` (a connection ID) and `connectorKey` come from `uip is connections list`. **Present what discovery returns and confirm the exact selection before continuing.**

### Phase 2 — Skeleton

Emit the structural BPMN graph first, with no UiPath payloads yet.

- One `bpmn:process` (give it a stable `id`), wrapped in a `bpmn:definitions` that declares the namespaces, including `xmlns:uipath`.
- A `bpmn:startEvent`, the user-confirmed task / event / gateway nodes, a `bpmn:endEvent`.
- `bpmn:sequenceFlow` edges connecting them; each flow's `id` is what fills the `{incomingEdge}` / `{outgoingEdge}` placeholders in node templates.
- Structural BPMN element types come from the registry's `bpmnElements` section (`registry get` or the spec): gateways (`bpmn:ExclusiveGateway`, `bpmn:ParallelGateway`, ...), events, and the correct task element for each extension type (a type's `bpmnElement` field — e.g. `Orchestrator.StartJob` -> `bpmn:ServiceTask`, `Intsvc.ActivityExecution` -> `bpmn:SendTask`, `Orchestrator.StartAgenticProcess` -> `bpmn:CallActivity`).

**Declare variables** the process needs (inputs, outputs of each node, gateway-decision values) using the `BPMN.Variables` extension type's template. Each node template exposes a `{varId}` for its output variable.

Confirm the structure (node list, order, branches, variables) with the user before enriching.

### Phase 3 — Enrich + author (per node, in topological order)

Walk the graph from start to end. For each node, fetch its template and fill it.

```bash
# Non-connector node (Orchestrator.*, Maestro.*, BPMN.*, Actions.HITL, A2A.*):
uip maestro bpmn registry get <extensionType>

# Connector node (Intsvc.*): enrich against the LIVE object shape
uip maestro bpmn registry get <extensionType> \
  --connection-id <connectionId> --object-name <objectName>
```

`registry get` returns the type's full spec: `xmlTemplate`, `contextFields`, `inputPattern`, `bindingPattern`, and (for `Intsvc.*` with `--connection-id` / `--object-name`) an `ISEnrichment` block with the real field shapes for that connection's object. Authoring rules:

- **Fill placeholders, keep structure.** Replace `{id}`, `{name}`, `{incomingEdge}`, `{outgoingEdge}`, `{varId}`, and each `{contextField}` (e.g. `{releaseKey}`, `{activity}`, `{connectorKey}`) with discovered / confirmed values. Do not add, rename, or drop `uipath:*` elements the template doesn't have.
- **IDs from discovery only.** `releaseKey`, `connection` ID, `connectorKey`, `folderKey`, queue key, `appId` — Phase-1 values or user-supplied. Never a placeholder GUID.
- **Connector inputs from the enriched shape.** Write the node's input expressions (the `body` / separate `<uipath:input>` values, output `var` references) against the real fields in `ISEnrichment`, respecting the type's `inputPattern` (`separateInputs` vs `mergedBody`) and `extensionTag` (`uipath:event` for the `isEventsArray` types, else `uipath:activity`).
- **Non-connector nodes use the template alone** — no enrichment call needed.

**Write `uipath:Bindings` from the template's `bindingInfo`.** Types whose `bindingPattern` is `process` / `queue` carry a `bindingInfo` (`resource`, `resourceKeyPattern`, `propertyAttribute`, `contextField`). Emit one `uipath:Bindings` / binding entry per such resource using `resource` = the declared resource (`process`, `queue`, ...) plus its `resourceSubType` and the resource GUID confirmed in Phase 1; the bound context field (e.g. `releaseKey`) references that binding. For `bindingPattern: connection` (`Intsvc.*`), the connection is bound inline via the template's `value="=bindings.{bindingId}"` — wire `{bindingId}` to the `uipath:Bindings` entry holding the discovered connection ID. Do not author binding shapes the registry didn't describe.

**Gateways.** For a `bpmn:ExclusiveGateway`, write each outgoing `bpmn:sequenceFlow`'s `bpmn:conditionExpression` as a `=js:` expression over declared variables (e.g. `=js: vars.amount > 1000`), and mark exactly one flow as the gateway's `default` so the graph is total and never dead-ends.

### Phase 4 — Validate + output

1. **Validate** the assembled BPMN before handing it over. Run the repo's BPMN validation step if present (a sibling validator may be added by another PR — reference and invoke it when available); otherwise at minimum confirm: well-formed XML, every `uipath:*` block matches a registry `xmlTemplate`, every referenced sequence-flow `id` exists, every gateway has a `default`, every `var` / binding reference resolves, and no ID was fabricated.
2. **Write** the `.bpmn` file (default name from the process; confirm path with the user).
3. **State the import target:** the file imports into a UiPath Maestro process (Studio Web BPMN modeler / Maestro project) — tell the user exactly where to import it and which connections / processes it expects to exist in that tenant.

## Quick Reference — registry CLI surface

| Command | Purpose |
| --- | --- |
| `uip maestro bpmn registry pull [-f]` | Sync & cache the registry (login first for connectors / processes; `-f` forces refresh) |
| `uip maestro bpmn registry list [--limit <n\|-1>]` | List cached extension types + discovered connectors / processes |
| `uip maestro bpmn registry search <keyword>` | Find types / connectors / processes by keyword |
| `uip maestro bpmn registry get <extensionType>` | Full spec: `xmlTemplate`, `contextFields`, `bindingInfo`, patterns |
| `uip maestro bpmn registry get <type> --connection-id <id> --object-name <obj>` | As above, plus live IS field shapes (`ISEnrichment`) for `Intsvc.*` types |
| `uip is connections list` | List live Integration Service connections (ID + state) |

These are the only registry / connection flags this skill relies on; all are verified against the CLI command definitions. Use `--output-filter "Data.ExtensionType"` (a standard CLI option) to narrow large `get` output.
