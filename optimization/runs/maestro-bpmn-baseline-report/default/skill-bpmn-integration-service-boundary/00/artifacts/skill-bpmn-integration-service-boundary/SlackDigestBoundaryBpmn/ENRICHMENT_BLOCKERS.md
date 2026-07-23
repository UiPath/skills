# CLI-Owned Enrichment Blockers

**Project:** SlackDigestBoundaryBpmn  
**Affected node:** `Task_SendSlack` (`bpmn:SendTask`, type `Intsvc.ActivityExecution`)  
**Status:** DRAFT — the BPMN file is structurally valid and passes the offline
validator, but the process **cannot be uploaded, packaged, or run** until every
blocker below is resolved by the CLI.

---

## What "draft executable boundary" means

`Task_SendSlack` uses the exact `Intsvc.ActivityExecution` wrapper served by the
registry (`uip maestro bpmn registry get Intsvc.ActivityExecution --output json`).
The structural BPMN shape, sequence flows, variable declarations, output variable
binding, and diagram geometry are all present and valid.  
**What is absent** is everything the CLI must supply from live tenant data:
connector operation metadata, connection binding, dynamic input/output schemas,
generated output, `bindings_v2.json`, and package metadata.  
Those items are **never hand-authored** — this file intentionally leaves their
slots empty rather than inventing values.

---

## Blocker 1 — Slack connector resource key (`connectorKey`)

**What is missing:** The `connectorKey` context field on `Task_SendSlack` is
empty (`value=""`).

**Why it cannot be invented:** The connector resource key is an opaque string
assigned by the Integration Service catalog. Guessing it (e.g. `"slack"` or
`"uipath-slack"`) will produce a node the canvas cannot bind to any real
connector.

**How to resolve:**

```
uip maestro bpmn registry search slack --output json
```

Locate the matching entry in `Data.Connectors[]`. Copy its `ExtensionType`
(e.g. `Intsvc.ActivityExecution`) and its connector identifier into:

```xml
<uipath:input name="connectorKey" value="<value-from-registry>" />
```

---

## Blocker 2 — Live Slack connection ID and connection binding (`connection` / `Binding_SlackConnection`)

**What is missing:** The `<uipath:binding>` for `Binding_SlackConnection` has
`default=""`. The context field `connection` references
`=bindings.Binding_SlackConnection`, which resolves to nothing at runtime.

**Why it cannot be invented:** Connection IDs are GUIDs assigned per tenant and
per folder. There is no canonical value that works across tenants.

**How to resolve:**

```
uip is connections list --all-folders --output json
```

Find the Slack connection entry. Copy its `Id` (a GUID) into the binding:

```xml
<uipath:binding
    id="Binding_SlackConnection"
    resource="Connection"
    propertyAttribute="ConnectionId"
    default="<connection-guid-from-list>" />
```

---

## Blocker 3 — Connector operation metadata (`activity`, `method`, `path`)

**What is missing:** The `activity`, `method`, and `path` context fields are all
empty. These describe which Slack API operation to invoke (e.g. "Post Message",
`POST`, `/chat.postMessage`).

**Why they cannot be invented:** Operation names, HTTP methods, and API paths are
served by the IS catalog and vary by connector version. Hand-authoring them
produces a node the runtime cannot dispatch.

**How to resolve:** Run the enriched registry get after resolving Blocker 2:

```
uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <connection-guid> \
    --object-name <object-name-from-catalog> \
    --output json
```

The response `Data.ExtensionType.ISEnrichment` block contains the resolved
`activity`, `method`, and `path` values. Copy them into the corresponding
`<uipath:input>` elements on `Task_SendSlack`.

---

## Blocker 4 — Dynamic input schema and `body` CDATA

**What is missing:** The `body` CDATA on `Task_SendSlack` contains only:

```json
{"text":"=vars.Var_DigestContent"}
```

This is the single field the BPMN layer can safely author from the declared
process variable. The full field list (e.g. `channel`, `blocks`, `attachments`,
`username`, `icon_emoji`) is part of the connector's dynamic schema and is
absent.

**Why it cannot be invented:** Dynamic schemas are generated from the live
connector definition. Inventing field names risks silent data loss or a runtime
schema-validation failure.

**How to resolve:** After running the enriched `registry get` (Blocker 3), the
`ISEnrichment.inputSchema` in the response defines the complete body structure.
Replace the `body` CDATA with the enriched schema, keeping
`"text":"=vars.Var_DigestContent"` wired to the process variable.

---

## Blocker 5 — Folder key (`folderKey`)

**What is missing:** The `folderKey` context field is empty (`value=""`).

**Why it cannot be invented:** Folder keys are tenant-specific GUIDs or path
strings assigned in Orchestrator. A wrong key causes a runtime authorization
failure.

**How to resolve:**

```
uip or folders list --output json
```

Identify the target folder and copy its `Key` (or `FullyQualifiedName` as
appropriate) into:

```xml
<uipath:input name="folderKey" value="<folder-key>" />
```

---

## Blocker 6 — Generated output variable schema (`Var_SlackResult`)

**What is missing:** `Var_SlackResult` is declared as type `object` with no
sub-schema. The output mapping `source="."` captures the full connector
response, but downstream variable references (e.g.
`=vars.Var_SlackResult.ts`, `=vars.Var_SlackResult.channel`) cannot be
validated without the actual response schema.

**Why it cannot be invented:** The response schema is served by the IS catalog
and enrichment call. Its fields vary by connector version and operation.

**How to resolve:** After the enriched `registry get` (Blocker 3), inspect
`ISEnrichment.outputSchema`. If downstream tasks need specific fields, narrow
the output mapping `source` to those fields (e.g. `source="=result.ts"`) and
declare typed variables accordingly.

---

## Blocker 7 — `bindings_v2.json` and package metadata

**What is missing:** The following files do not exist in this project directory:

- `bindings_v2.json` — resource bindings generated from BPMN + IS enrichment
- `entry-points.json` — runnable start-event entry points and I/O schemas
- `operate.json` — runtime/package metadata
- `package-descriptor.json` — package manifest

**Why they cannot be hand-authored:** These files are generated outputs of CLI
packaging. Hand-authoring them risks schema drift, incorrect entry-point IDs,
and upload rejection.

**How to resolve (after Blockers 1–6 are closed):**

```
uip maestro bpmn pack SlackDigestBoundaryBpmn/ <OutputDir> --output json
```

The pack command generates all four files. Do not edit them by hand; re-run
the pack command after any BPMN source change.

---

## Authoring boundary summary

| Item | Owner | Status |
|---|---|---|
| BPMN structure, sequence flows, diagram geometry | Authored (BPMN layer) | Complete |
| Process variables (`Var_DigestContent`, `Var_DigestSubject`, `Var_SlackResult`) | Authored (BPMN layer) | Complete |
| `Task_PrepareDigest` script logic | Authored (BPMN layer) | Complete |
| `Intsvc.ActivityExecution` wrapper shape | Authored from registry template | Complete (draft) |
| `connectorKey` | CLI — `registry search` | **Blocker 1** |
| Connection GUID + binding `default` | CLI — `is connections list --all-folders` | **Blocker 2** |
| `activity`, `method`, `path` | CLI — enriched `registry get` | **Blocker 3** |
| Full `body` input schema | CLI — IS enrichment `inputSchema` | **Blocker 4** |
| `folderKey` | CLI — `or folders list` | **Blocker 5** |
| `Var_SlackResult` output schema | CLI — IS enrichment `outputSchema` | **Blocker 6** |
| `bindings_v2.json`, `entry-points.json`, `operate.json`, `package-descriptor.json` | CLI — `bpmn pack` | **Blocker 7** |

Resolve blockers 1–6 in the BPMN source, then run `bpmn pack` to close Blocker 7
before attempting upload or run.
