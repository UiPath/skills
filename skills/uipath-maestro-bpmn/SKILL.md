---
name: uipath-maestro-bpmn
description: "UiPath Maestro BPMN — author valid, importable Maestro `.bpmn` XML from a description via the `uip maestro bpmn registry` CLI. Every uipath:* extension comes from a registry template; every ID from discovery. Triggers on 'create a Maestro BPMN', '.bpmn file'."
when_to_use: "User wants to create or author a UiPath Maestro BPMN process as `.bpmn` XML from a description — e.g. 'generate a Maestro BPMN that runs an RPA job then sends a Slack message', 'build a BPMN with an exclusive gateway', 'author Maestro process XML calling connector X'. Also when adding registry-backed nodes to an existing `.bpmn`. NOT for `.flow` Maestro flows (->uipath-maestro-flow), case-management apps (->uipath-maestro-case), API workflow JSON (->uipath-api-workflow), or `.xaml`/coded RPA (->uipath-rpa)."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Maestro BPMN Authoring

Generate **valid, UiPath-importable Maestro BPMN XML** from a natural-language description. The single source of truth for every UiPath extension is the **Maestro BPMN registry**, queried through the `uip maestro bpmn registry` CLI. You assemble the BPMN graph (events, tasks, gateways, sequence flows, diagram); the registry supplies every `uipath:*` payload as a fill-in-the-blanks `xmlTemplate`.

> **Scope:** authoring only — discover, skeleton, enrich, validate, and (optionally) package a local `.bpmn` project. This skill does **not** upload, publish, deploy, debug, run, or diagnose deployed instances. Those are out of scope.

## When to Use This Skill

- User wants to **create a new** Maestro `.bpmn` file from a description.
- User wants to **add nodes** (RPA job, agent, connector activity, HTTP request, message event, gateway, script, variables) to an existing `.bpmn`.
- User asks how a particular Maestro step type is represented in BPMN XML.
- User asks to wire a Maestro process to a **real** connector, connection, queue, or Orchestrator process.

Do NOT use for: `.flow` Maestro flows (-> `uipath-maestro-flow`), case-management apps (-> `uipath-maestro-case`), API workflow JSON (-> `uipath-api-workflow`), `.xaml` / coded RPA (-> `uipath-rpa`).

## Non-Negotiable Principles

1. **Author every `uipath:*` element from a registry template — never from memory or a prose doc.** For each node, fetch its `xmlTemplate` with `uip maestro bpmn registry get <extensionType> --output json` and fill the `{placeholders}`. This applies to *every* type that has a template, including `BPMN.ScriptTask` and `BPMN.Variables` — do not hand-write a `uipath:activity`, `uipath:event`, `uipath:mapping`, or `uipath:Bindings` block. If a type isn't in the registry, stop and tell the user; do not invent it.
2. **Never fabricate an ID.** Connection IDs, `releaseKey`s, `connectorKey`s, `folderKey`s, queue keys, app IDs — every one comes from discovery (`registry` / `is connections`) or is supplied by the user. A guessed GUID produces a BPMN that imports but fails at runtime.
3. **Confirm before you commit.** This skill is interactive. Use `AskUserQuestion` (or a plain question) to confirm the connector/connection/process selection, the overall structure, and the variable set before writing XML. When discovery returns several candidates, present them and let the user pick.
4. **Build in phases, validate at the end.** Discover -> Skeleton (with diagram) -> Enrich + author -> Validate. Don't author a connector node before you've enriched it against its real object shape.
5. **A BPMN without a diagram does not import.** Every authored process MUST carry a `bpmndi:BPMNDiagram` + `bpmndi:BPMNPlane`, with a `bpmndi:BPMNShape` for every visible node and a `bpmndi:BPMNEdge` for every sequence flow. The registry does **not** supply diagram geometry (see [Diagram: a known registry gap](#diagram-a-known-registry-gap)); you generate it.

## The Four-Phase Flow

### Phase 1 — Discover

Sync the registry, then find the real building blocks. Confirm each choice with the user; never proceed on a fabricated ID. Pass `--output json` on any command whose output you parse.

```bash
# 1. Sync (login first to discover connectors & Orchestrator processes; OOTB types work without login)
uip login
uip maestro bpmn registry pull                               # caches static types + discovered resources (-f forces refresh)

# 2. Browse / search extension types, connectors, processes
uip maestro bpmn registry list --output json                 # first 30; --limit -1 for all
uip maestro bpmn registry search <keyword> --output json     # e.g. slack | queue | agent | connector

# 3. Discover live Integration Service connections (ID + state)
uip is connections list --output json   # <!-- uip-check-skip -->
```

Map the user's intent to extension types using `search` / `list`:
- "Run an RPA workflow / process" -> `Orchestrator.StartJob`
- "Run an agent" -> `Orchestrator.StartAgentJob`; "API workflow" -> `Orchestrator.ExecuteApiWorkflowAsync`
- "Agentic process / case management" -> `Orchestrator.StartAgenticProcess[Async]` / `Orchestrator.StartCaseMgmtProcess[Async]`
- "Queue item" -> `Orchestrator.CreateQueueItem` / `Orchestrator.CreateAndWaitForQueueItem`
- "Business rule" -> `Orchestrator.BusinessRules`
- "Call a connector (Slack/Gmail/...)" -> `Intsvc.ActivityExecution`; wait for a connector event -> `Intsvc.WaitForEvent`; connector start trigger -> `Intsvc.EventTrigger`
- "HTTP request" -> `Intsvc.UnifiedHttpRequest`; "internal message" -> `Maestro.SendMessageEvent` / `Maestro.ReceiveMessageEvent`
- "Human task / action app" -> `Actions.HITL`; "script" -> `BPMN.ScriptTask`; declare variables -> `BPMN.Variables`

For Orchestrator-resource types (`Orchestrator.*`), the real `releaseKey` / queue key comes from the user or from registry-discovered resources (`registry list --output json` -> `Processes[].ProcessKey`). For `Intsvc.*` types, the `connection` ID and `connectorKey` come from `uip is connections list --output json`. **Present what discovery returns and confirm the exact selection before continuing.** <!-- uip-check-skip -->

### Phase 2 — Skeleton (including the diagram)

Emit the structural BPMN graph first, with no UiPath payloads yet — but **with diagram geometry**, because Studio Web rejects a diagram-less file.

- One `bpmn:process` (give it a stable `id`), wrapped in a `bpmn:definitions` that declares the namespaces, including `xmlns:uipath="http://uipath.org/schema/bpmn"` and the BPMNDI/DI/DC namespaces. Do **not** use `http://schemas.uipath.com/workflow/activities` for the `uipath` prefix. (`uip maestro bpmn init <Name>` scaffolds a correct, diagram-ready definitions shell you can build on.)
- A `bpmn:startEvent`, the user-confirmed task / event / gateway nodes, a `bpmn:endEvent`.
- `bpmn:sequenceFlow` edges connecting them; each flow's `id` is what fills the `{incomingEdge}` / `{outgoingEdge}` placeholders in node templates.
- The structural element type for each node is the registry type's **`bpmnElement` field** (from `registry get` / `registry list`): e.g. `Orchestrator.StartJob` -> `bpmn:serviceTask`, `Intsvc.ActivityExecution` -> `bpmn:sendTask`, `Intsvc.WaitForEvent` -> `bpmn:receiveTask`, `Orchestrator.StartAgenticProcess` -> `bpmn:callActivity`, `Actions.HITL` -> `bpmn:userTask`, `BPMN.ScriptTask` -> `bpmn:scriptTask`, `BPMN.Variables` -> `bpmn:task`. Gateways (`bpmn:exclusiveGateway`, `bpmn:parallelGateway`, ...) come from the spec's `bpmnElements` section.

**Declare process variables** with the **`BPMN.Variables` registry template** (`uip maestro bpmn registry get BPMN.Variables --output json`) — do not hand-author the variables block. Give each variable a stable `id`, a `name`, and a `type`. Node templates reference a variable through `=vars.<variableId>`.

Generate the **diagram** for every visible node and flow (see [Diagram: a known registry gap](#diagram-a-known-registry-gap)).

Confirm the structure (node list, order, branches, variables) with the user before enriching.

### Phase 3 — Enrich + author (per node, in topological order)

Walk the graph from start to end. For each node, fetch its template and fill it.

```bash
# Any node (Orchestrator.*, Maestro.*, BPMN.*, Actions.HITL, A2A.*):
uip maestro bpmn registry get <extensionType> --output json

# Connector node (Intsvc.*): enrich against the LIVE object shape
uip maestro bpmn registry get <extensionType> \
  --connection-id <connectionId> --object-name <objectName> --output json
```

`registry get` returns the type's full spec: `xmlTemplate`, `extensionTag`, `bpmnElement`, `inputPattern`, `bindingPattern`, `bindingInfo`, and (for `Intsvc.*` with `--connection-id` + `--object-name`) an `ISEnrichment` block with the real field shapes for that connection's object. Authoring rules:

- **Fill placeholders, keep structure.** Replace `{id}`, `{name}`, `{incomingEdge}`, `{outgoingEdge}`, `{varId}`, and each context placeholder (e.g. `{releaseKey}`, `{activity}`, `{connectorKey}`, `{bindingId}`) with discovered / confirmed values. Do not add, rename, or drop `uipath:*` elements the template doesn't have.
- **IDs from discovery only.** `releaseKey`, `connection` ID, `connectorKey`, `folderKey`, queue key, `appId` — Phase-1 values or user-supplied. Never a placeholder GUID.
- **Connector inputs from the enriched shape.** Write the node's input expressions (the `body` / `<uipath:input>` values, output `var` references) against the real fields in `ISEnrichment`, respecting the type's `inputPattern` (`separateInputs` vs `mergedBody` vs `scriptArgs`).
- **Bindings come from the template's `bindingInfo`** (Principle below) — not from a prose doc.

**Bindings (`uipath:Bindings`) from the template.** A type's `bindingPattern` and `bindingInfo` (from `registry get`) tell you how its resource is bound:
- `bindingPattern: process | queue | businessRule` carry a `bindingInfo` (`resource`, `resourceKeyPattern`, `propertyAttribute`, `contextField`). Emit one binding entry for that resource, using the resource GUID confirmed in Phase 1; the bound context field (e.g. `releaseKey`) references it.
- `bindingPattern: connection` (`Intsvc.*`) binds the connection inline via the template's `value="=bindings.{bindingId}"`; wire `{bindingId}` to a `uipath:Bindings` entry holding the discovered connection ID.
- `bindingPattern: none` needs no binding.

Author binding shapes **only** as the template's `bindingInfo` describes — never invent one.

**Gateways.** For a `bpmn:exclusiveGateway`, write each outgoing `bpmn:sequenceFlow`'s `bpmn:conditionExpression` as a runtime expression over declared variables (leading `=`; the documented JavaScript form is the `=js:` prefix — e.g. `=js:vars.amount > 1000`). Mark exactly one outgoing flow as the gateway's `default` so the graph cannot dead-end. See [shared/expression-authoring.md](references/shared/expression-authoring.md).

**Scripts.** Author the `BPMN.ScriptTask` node from its registry template (`uip maestro bpmn registry get BPMN.ScriptTask --output json`) and fill its `uipath:mapping` `args` input (`inputPattern: scriptArgs`). Script bodies run under **Jint** — no `require`/`import`, `fetch`/`XMLHttpRequest`, `fs`/`process`, `window`/`document`, timers, npm packages, or long-running async. Read mapped fields as top-level identifiers, not `args.<field>`. The exact element shape (including any `scriptVersion` / `scriptFormat` the product expects) is whatever the registry template returns — follow it verbatim; do not graft on attributes the template omits.

### Phase 4 — Validate

1. **Validate** the assembled BPMN before handing it over. There is **no `uip maestro bpmn validate` CLI command.** Use the bundled offline validator (semantic, ports the PO.Frontend canvas rules), which prints `VALID` / errors and exits 0 / non-zero: <!-- uip-check-skip -->
   ```bash
   node skills/uipath-maestro-bpmn/validator/validate-bpmn.mjs ProjectName/ProjectName.bpmn
   ```
   If the validator is not present in your checkout, run an explicit well-formed-XML parse as a fallback (this must actually execute — reading or eyeballing the file is not validation):
   ```bash
   python3 -c "import xml.etree.ElementTree as ET; ET.parse('ProjectName/ProjectName.bpmn')"
   ```
   At minimum confirm: well-formed XML; a `bpmndi:BPMNDiagram`/`BPMNPlane` with a shape per node and an edge per flow; every `uipath:*` block matches a registry `xmlTemplate`; every referenced sequence-flow `id` exists; every `var` / binding reference resolves; and no ID was fabricated.
2. **(Optional) package locally** when the user wants an artifact:
   ```bash
   uip maestro bpmn pack ProjectName/ ./pack-output --output json
   ```
   Do not upload, publish, deploy, debug, or run — those are out of this skill's scope.
3. **State the import target:** the file imports into a UiPath Maestro process (Studio Web BPMN modeler / Maestro project) — tell the user where to import it and which connections / processes it expects to exist in that tenant.

## Diagram: a known registry gap

The registry has **zero diagram content** — `registry get` returns no `bpmndi`/`BPMNPlane`. This is the one piece of an importable BPMN the registry does not own, so you must generate it yourself (or start from the `uip maestro bpmn init` shell). Minimal rules:

- One `bpmndi:BPMNDiagram` containing one `bpmndi:BPMNPlane bpmnElement="<process id>"`.
- One `bpmndi:BPMNShape bpmnElement="<node id>"` per visible node, each with a `dc:Bounds x/y/width/height`. Lay nodes left-to-right; a simple grid (e.g. x += 150 per step, fixed y) is enough — Studio Web re-layouts on import, it just needs valid geometry.
- One `bpmndi:BPMNEdge bpmnElement="<sequenceFlow id>"` per sequence flow, each with `di:waypoint` start/end points.

> **Tracked gap:** until the registry emits diagram geometry, this is generated by the skill. Do not route diagram authoring to any external/hand-made contract doc — keep it inline here.

## Quick Reference — CLI surface

| Command | Purpose |
| --- | --- |
| `uip maestro bpmn init <Name>` | Scaffold a local Maestro BPMN project (`Name/Name.bpmn` + `project.uiproj` + metadata; diagram-ready definitions shell) |
| `uip maestro bpmn registry pull [-f]` | Sync & cache the registry (login first for connectors / processes; `-f` forces refresh) |
| `uip maestro bpmn registry list --output json [--limit <n\|-1>]` | List cached extension types + discovered connectors / processes (default 30) |
| `uip maestro bpmn registry search <keyword> --output json` | Find types / connectors / processes by keyword |
| `uip maestro bpmn registry get <extensionType> --output json` | Full spec: `xmlTemplate`, `bpmnElement`, `extensionTag`, `bindingInfo`, patterns |
| `uip maestro bpmn registry get <type> --connection-id <id> --object-name <obj> --output json` | As above, plus live IS field shapes (`ISEnrichment`) for `Intsvc.*` types |
| `uip is connections list --output json` <!-- uip-check-skip --> | List live Integration Service connections (ID + state) |
| `node skills/uipath-maestro-bpmn/validator/validate-bpmn.mjs <Name>/<Name>.bpmn` | Bundled offline semantic validator (prints `VALID`, exits 0/non-zero) |
| `uip maestro bpmn pack <projectPath> <outputDir> [-v <version>]` | Package the project locally into a `.nupkg` |

There is **no** `uip maestro bpmn validate` command — do not present one. Always pass `--output json` on any command whose output you parse. If a command does not support JSON, do not silently scrape its text — report it and keep the next step manual. <!-- uip-check-skip -->

## Anti-patterns

- **Do not hand-author `uipath:*` elements** (`uipath:activity`, `uipath:event`, `uipath:mapping`, `uipath:Bindings`) from memory or a prose doc — always fill a registry `xmlTemplate`, including for scripts and variables.
- **Do not present `uip maestro bpmn validate`** — it does not exist. Use the bundled validator or an XML-parse fallback. <!-- uip-check-skip -->
- **Do not skip the BPMN diagram.** A file without `bpmndi:BPMNDiagram`/`BPMNPlane` (and a shape/edge per visible element) fails Studio Web import.
- **Never fabricate an ID** — connection IDs, `releaseKey`, `connectorKey`, `folderKey`, queue keys, app IDs come from discovery or the user, never a guessed GUID.
- **Do not put real tenant data in the BPMN** — no real connection IDs, folder keys, tenant URLs, user names, or exported customer XML. Examples must be synthetic/placeholder-safe.
- **Do not write a script that leaves the Jint boundary** — no Node/browser/filesystem/network APIs, timers, packages, or long-running async.
- **Do not parse human CLI text** when `--output json` is available.

## Reference Navigation

These references cover behavior the registry does **not** own. Read the smallest relevant one; everything structural (element shapes, bindings, script/variables payloads) comes from `registry get`, not a doc.

| I need to... | Read |
| --- | --- |
| Author lint-safe runtime expressions (`=vars.`, `=bindings.`, `=js:`/Jint, gateway conditions, iterators) | [shared/expression-authoring.md](references/shared/expression-authoring.md) |
| Follow CLI output-parsing / login / IS-enrichment conventions | [shared/cli-conventions.md](references/shared/cli-conventions.md) |
| Keep examples, fixtures, and commits public-safe | [shared/public-safety.md](references/shared/public-safety.md) |
