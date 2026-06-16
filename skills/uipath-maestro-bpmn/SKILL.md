---
name: uipath-maestro-bpmn
description: "UiPath Maestro BPMN — author valid, importable Maestro `.bpmn` XML from a description via the `uip maestro bpmn registry` CLI. uipath:* extensions come from registry templates; IDs from discovery. Triggers on 'create a Maestro BPMN', '.bpmn file'."
when_to_use: "User wants to create or author a UiPath Maestro BPMN process as `.bpmn` XML from a description — e.g. 'generate a Maestro BPMN that runs an RPA job then sends a Slack message', 'build a BPMN with an exclusive gateway', 'author Maestro process XML calling connector X'. Also when editing/extending an existing `.bpmn` by adding registry-backed nodes. NOT for `.flow` Maestro flows (->uipath-maestro-flow), case-management apps (->uipath-maestro-case), API workflow JSON (->uipath-api-workflow), or `.xaml`/coded RPA (->uipath-rpa)."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Maestro BPMN Authoring

Generate **valid, UiPath-importable Maestro BPMN XML** from a natural-language description. The single source of truth for every UiPath extension is the **Maestro BPMN registry**, queried through the `uip maestro bpmn registry` CLI. You assemble the BPMN graph (events, tasks, gateways, sequence flows, diagram); the registry supplies every `uipath:*` payload as a fill-in-the-blanks `xmlTemplate`.

> **Scope:** this skill covers the *authoring* lifecycle — generate, validate, and package a local `.bpmn` project. It does **not** cover operating (upload/publish/run) or diagnosing deployed instances. Those are out of scope for this skill.

## When to Use This Skill

- User wants to **create a new** Maestro `.bpmn` file from a description.
- User wants to **add nodes** (RPA job, agent, connector activity, HTTP request, message event, gateway, script) to an existing `.bpmn`.
- User asks how a particular Maestro step type is represented in BPMN XML.
- User asks to wire a Maestro process to a **real** connector, connection, queue, or Orchestrator process.

Do NOT use for: `.flow` Maestro flows (-> `uipath-maestro-flow`), case-management apps (-> `uipath-maestro-case`), API workflow JSON (-> `uipath-api-workflow`), `.xaml` / coded RPA (-> `uipath-rpa`).

## Non-Negotiable Principles

1. **Author UiPath extensions ONLY from registry templates.** Never hand-write a `uipath:activity`, `uipath:event`, `uipath:mapping`, or `uipath:Bindings` element from memory. Always fetch the type's `xmlTemplate` with `uip maestro bpmn registry get <extensionType> --output json` and fill its `{placeholders}`. If a type isn't in the registry, stop and tell the user — do not invent it.
2. **Never fabricate an ID.** Connection IDs, `releaseKey`s, `connectorKey`s, `folderKey`s, queue keys, app IDs — every one comes from discovery (`registry` / `is connections`) or is supplied by the user. A guessed GUID produces a BPMN that imports but fails at runtime.
3. **Confirm before you commit.** This skill is interactive. Use `AskUserQuestion` (or a plain question) to confirm the connector/connection/process selection, the overall structure, and the variable set before writing XML. When discovery returns several candidates, present them and let the user pick.
4. **Build in phases, validate at the end.** Discover -> Skeleton (with diagram) -> Enrich + author -> Validate + package. Don't author a connector node before you've enriched it against its real object shape.
5. **A BPMN without a diagram does not import.** Every authored process MUST carry a `bpmndi:BPMNDiagram` + `bpmndi:BPMNPlane`, with a `bpmndi:BPMNShape` for every visible node and a `bpmndi:BPMNEdge` for every sequence flow. See [shared/bpmn-xml-contract.md](references/shared/bpmn-xml-contract.md).

## The Four-Phase Flow

### Phase 1 — Discover

Sync the registry, then find the real building blocks. Confirm each choice with the user; never proceed on a fabricated ID. Pass `--output json` on any command whose output you parse.

```bash
# 1. Sync (and authenticate for connectors/processes; OOTB types work without login)
uip login                                  # needed to discover connectors & Orchestrator processes
uip maestro bpmn registry pull             # caches static extension types + discovered resources

# 2. Browse / search extension types, connectors, processes
uip maestro bpmn registry list --output json                 # first 30; --limit -1 for all
uip maestro bpmn registry search <keyword> --output json     # e.g. slack | queue | agent | connector

# 3. Discover live Integration Service connections (ID + state)
uip is connections list --output json
```

Map the user's intent to extension types using `search` / `list`:
- "Run an RPA workflow / process" -> `Orchestrator.StartJob`
- "Run an agent" -> `Orchestrator.StartAgentJob`; "API workflow" -> `Orchestrator.ExecuteApiWorkflowAsync`
- "Agentic process / case management" -> `Orchestrator.StartAgenticProcess[Async]` / `Orchestrator.StartCaseMgmtProcess[Async]`
- "Queue item" -> `Orchestrator.CreateQueueItem` / `Orchestrator.CreateAndWaitForQueueItem`
- "Call a connector (Slack/Gmail/...)" -> `Intsvc.ActivityExecution`; wait for a connector event -> `Intsvc.WaitForEvent`
- "HTTP request" -> `Intsvc.UnifiedHttpRequest`; "internal message" -> `Maestro.SendMessageEvent` / `Maestro.ReceiveMessageEvent`
- "Human task / action app" -> `Actions.HITL`; "script" -> `BPMN.ScriptTask`; variables -> `BPMN.Variables`

For Orchestrator-resource types (`Orchestrator.*`), the real `releaseKey` / queue key comes from the user or from registry-discovered resources (`registry list --output json` -> `Processes[].ProcessKey`). For `Intsvc.*` types, the `connection` (a connection ID) and `connectorKey` come from `uip is connections list --output json`. **Present what discovery returns and confirm the exact selection before continuing.**

### Phase 2 — Skeleton (including the diagram)

Emit the structural BPMN graph first, with no UiPath payloads yet — but **with diagram geometry**, because Studio Web rejects a diagram-less file.

- One `bpmn:process` (give it a stable `id`), wrapped in a `bpmn:definitions` that declares the namespaces, including `xmlns:uipath="http://uipath.org/schema/bpmn"` and the BPMNDI/DI/DC namespaces. Do **not** use `http://schemas.uipath.com/workflow/activities` for the `uipath` prefix.
- A `bpmn:startEvent`, the user-confirmed task / event / gateway nodes, a `bpmn:endEvent`.
- `bpmn:sequenceFlow` edges connecting them; each flow's `id` is what fills the `{incomingEdge}` / `{outgoingEdge}` placeholders in node templates.
- A **`bpmndi:BPMNDiagram` containing a `bpmndi:BPMNPlane`** that references the root process `id`, with one `bpmndi:BPMNShape` (with `dc:Bounds`) per visible node and one `bpmndi:BPMNEdge` (with `di:waypoint`s) per sequence flow. A file without this fails import.
- Structural BPMN element types come from the registry's `bpmnElements` section (`registry get` or the spec): gateways (`bpmn:exclusiveGateway`, `bpmn:parallelGateway`, ...), events, and the correct task element for each extension type (a type's `bpmnElement` field — e.g. `Orchestrator.StartJob` -> `bpmn:serviceTask`, `Intsvc.ActivityExecution` -> `bpmn:sendTask`, `Orchestrator.StartAgenticProcess` -> `bpmn:callActivity`).

**Declare variables** the process needs (inputs, outputs of each node, gateway-decision values) under `bpmn:process` / `bpmn:extensionElements` as a root `uipath:variables version="v1"` block, using `uipath:input` / `uipath:inputOutput` / `uipath:output` children with a stable `id`, a `name`, and a `type`. Each node template references its variable through `=vars.<variableId>`.

Confirm the structure (node list, order, branches, variables) with the user before enriching.

### Phase 3 — Enrich + author (per node, in topological order)

Walk the graph from start to end. For each node, fetch its template and fill it.

```bash
# Non-connector node (Orchestrator.*, Maestro.*, BPMN.*, Actions.HITL, A2A.*):
uip maestro bpmn registry get <extensionType> --output json

# Connector node (Intsvc.*): enrich against the LIVE object shape
uip maestro bpmn registry get <extensionType> \
  --connection-id <connectionId> --object-name <objectName> --output json
```

`registry get` returns the type's full spec: `xmlTemplate`, `contextFields`, `inputPattern`, `bindingPattern`, and (for `Intsvc.*` with `--connection-id` / `--object-name`) an `ISEnrichment` block with the real field shapes for that connection's object. Authoring rules:

- **Fill placeholders, keep structure.** Replace `{id}`, `{name}`, `{incomingEdge}`, `{outgoingEdge}`, `{varId}`, and each `{contextField}` (e.g. `{releaseKey}`, `{activity}`, `{connectorKey}`) with discovered / confirmed values. Do not add, rename, or drop `uipath:*` elements the template doesn't have.
- **IDs from discovery only.** `releaseKey`, `connection` ID, `connectorKey`, `folderKey`, queue key, `appId` — Phase-1 values or user-supplied. Never a placeholder GUID.
- **Connector inputs from the enriched shape.** Write the node's input expressions (the `body` / separate `<uipath:input>` values, output `var` references) against the real fields in `ISEnrichment`, respecting the type's `inputPattern` (`separateInputs` vs `mergedBody`). For the wrapper element, use the registry type's **`extensionTag` field verbatim** (it also tells you whether the type yields a `uipath:activity` or `uipath:event`, and where `uipath:mapping` attaches).
- **Non-connector nodes use the template alone** — no enrichment call needed.

**Write `uipath:Bindings` from the template's `bindingInfo`.** Types whose `bindingPattern` is `process` / `queue` carry a `bindingInfo` (`resource`, `resourceKeyPattern`, `propertyAttribute`, `contextField`). Emit one `uipath:Bindings` / binding entry per such resource using `resource` = the declared resource (`process`, `queue`, ...) plus its `resourceSubType` and the resource GUID confirmed in Phase 1; the bound context field (e.g. `releaseKey`) references that binding. For `bindingPattern: connection` (`Intsvc.*`), the connection is bound inline via the template's `value="=bindings.{bindingId}"` — wire `{bindingId}` to the `uipath:Bindings` entry holding the discovered connection ID. Do not author binding shapes the registry didn't describe.

**Gateways.** For a `bpmn:exclusiveGateway`, write each outgoing `bpmn:sequenceFlow`'s `bpmn:conditionExpression` as a runtime expression over declared variables (Maestro expects a leading `=`, and the documented form is the `=js:` prefix — e.g. `=js: vars.amount > 1000`). It is **recommended** to mark exactly one outgoing flow as the gateway's `default` so the graph cannot dead-end; if the spec for a particular gateway type says otherwise, follow the spec.

**Script tasks.** Use `bpmn:scriptTask scriptFormat="JavaScript"` with a `uipath:scriptVersion value="v3"` (preserve imported `v2`), a `uipath:mapping` whose `uipath:input name="args"` carries the mapped fields as `=vars.<variableId>` JSON, a script body that reads those fields as **top-level identifiers** (`amount`, not `args.amount`), and a `uipath:output ... var="<declared id>" source="=result.response"`. Scripts run under **Jint** — no `require`/`import`, `fetch`/`XMLHttpRequest`, `fs`/`process`, `window`/`document`, timers, packages, or long-running async. See [script/impl.md](references/author/references/plugins/script/impl.md) for the exact shell.

### Phase 4 — Validate + package

1. **Validate** the assembled BPMN before handing it over. Run the local CLI validator against the source file:
   ```bash
   uip maestro bpmn validate ProjectName/ProjectName.bpmn --output json
   ```
   If the installed CLI does not expose a validate command, run an explicit XML parse as a fallback (this must actually execute — reading or eyeballing the file is not validation):
   ```bash
   python3 -c "import xml.etree.ElementTree as ET; ET.parse('ProjectName/ProjectName.bpmn')"
   ```
   At minimum confirm: well-formed XML; a `bpmndi:BPMNDiagram`/`BPMNPlane` with a shape per node and an edge per flow; every `uipath:*` block matches a registry `xmlTemplate`; every referenced sequence-flow `id` exists; every `var` / binding reference resolves; and no ID was fabricated.
2. **Package** the project locally when the user wants an artifact. The project directory holds `ProjectName.bpmn` plus `project.uiproj` and the generated metadata (`operate.json`, `entry-points.json`, `bindings_v2.json`, `package-descriptor.json`). Pack to a **local output directory** outside the project source:
   ```bash
   uip maestro bpmn pack ProjectName/ ./pack-output --output json
   ```
   Do not upload, publish, deploy, debug, or run — those are out of this skill's scope.
3. **State the import target:** the file imports into a UiPath Maestro process (Studio Web BPMN modeler / Maestro project) — tell the user exactly where to import it and which connections / processes it expects to exist in that tenant.

## Quick Reference — CLI surface

| Command | Purpose |
| --- | --- |
| `uip maestro bpmn init <Name>` | Scaffold a local Maestro BPMN project (`Name/Name.bpmn` + `project.uiproj`) |
| `uip maestro bpmn registry pull [-f]` | Sync & cache the registry (login first for connectors / processes; `-f` forces refresh) |
| `uip maestro bpmn registry list --output json [--limit <n\|-1>]` | List cached extension types + discovered connectors / processes |
| `uip maestro bpmn registry search <keyword> --output json` | Find types / connectors / processes by keyword |
| `uip maestro bpmn registry get <extensionType> --output json` | Full spec: `xmlTemplate`, `contextFields`, `bindingInfo`, patterns |
| `uip maestro bpmn registry get <type> --connection-id <id> --object-name <obj> --output json` | As above, plus live IS field shapes (`ISEnrichment`) for `Intsvc.*` types |
| `uip is connections list --output json` | List live Integration Service connections (ID + state) |
| `uip maestro bpmn validate <Name>/<Name>.bpmn --output json` | Local BPMN validation against the source file |
| `uip maestro bpmn pack <Name>/ <OutputDir> --output json` | Package the project locally (consumes `package-descriptor.json`) |

Always pass `--output json` on any command whose output you parse programmatically. If a command does not yet support JSON, do not silently scrape its text — report it and keep the next step manual.

## Anti-patterns

- **Do not hand-author `uipath:*` elements** (`uipath:activity`, `uipath:event`, `uipath:mapping`, `uipath:Bindings`) from memory — always fill a registry `xmlTemplate`.
- **Do not skip the BPMN diagram.** A file without `bpmndi:BPMNDiagram`/`BPMNPlane` (and a shape/edge per visible element) fails Studio Web import.
- **Never fabricate an ID** — connection IDs, `releaseKey`, `connectorKey`, `folderKey`, queue keys, app IDs come from discovery or the user, never a guessed GUID.
- **Do not put real tenant data in the BPMN** — no real connection IDs, folder keys, tenant URLs, user names, or exported customer XML. Examples must be synthetic/placeholder-safe.
- **Do not write a script that leaves the Jint boundary** — no Node/browser/filesystem/network APIs, timers, packages, or long-running async.
- **Do not parse human CLI text** when `--output json` is available.

## Reference Navigation

Read the smallest relevant reference for the step at hand; do not bulk-read the tree.

| I need to... | Read |
| --- | --- |
| Understand the model-owned vs CLI-owned XML boundary, namespace, and diagram rules | [shared/bpmn-xml-contract.md](references/shared/bpmn-xml-contract.md) |
| Understand source vs generated package files and packaging inputs | [shared/project-layout.md](references/shared/project-layout.md) |
| Author variables, bindings, mappings, and expressions | [shared/variables-bindings-expressions.md](references/shared/variables-bindings-expressions.md) |
| Author lint-compatible runtime expressions | [shared/expression-authoring.md](references/shared/expression-authoring.md) |
| Author Maestro retry / boundary error / error mapping | [shared/error-handling.md](references/shared/error-handling.md) |
| Follow CLI conventions and the side-effect boundary | [shared/cli-conventions.md](references/shared/cli-conventions.md) |
| Run the local validation checklist before packaging | [author/validation.md](references/author/references/validation.md) |
| Copy a minimal XML shell per supported wrapper | [shared/wrapper-shells.md](references/shared/wrapper-shells.md) |
| Author a Jint-compatible script task | [script/impl.md](references/author/references/plugins/script/impl.md) |
| Keep examples and commits public-safe | [shared/public-safety.md](references/shared/public-safety.md) |
| See the full authoring capability index and plugin references | [author/CAPABILITY.md](references/author/CAPABILITY.md) |
