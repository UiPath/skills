# SlackDigestBoundaryBpmn — Draft BPMN Project

## Process overview

```
Manual Start  →  Prepare Digest (ScriptTask)  →  Send Slack Digest (IS boundary)  →  End
```

| Node | BPMN element | Extension type | Status |
|---|---|---|---|
| Manual Start | `bpmn:StartEvent` | _(none — blank start)_ | ✅ Complete |
| Prepare Digest | `bpmn:ScriptTask` | `BPMN.ScriptTask` | ✅ Structurally complete (replace script body for production) |
| Send Slack Digest | `bpmn:SendTask` | `Intsvc.ActivityExecution` | ⚠️ DRAFT — CLI enrichment required (see below) |
| End | `bpmn:EndEvent` | _(none — blank end)_ | ✅ Complete |

---

## CLI-owned enrichment blockers

The following items **must** be resolved by CLI enrichment before this project
can be uploaded, published, packaged, or run. None of them can be hand-authored
without risking a non-functional or incorrectly-bound process.

### 1. Slack connector resource key (`connectorKey`)

The Integration Service connector key for Slack is not fabricated here because
it is tenant-registry-owned. Resolve it with:

```
uip maestro bpmn registry search slack --output json
```

Locate the row whose `ExtensionType` is `Intsvc.ActivityExecution` and whose
`Label` names the Slack connector. Copy the exact `connectorKey` value and
replace `PLACEHOLDER_CONNECTOR_KEY` in `Task_SendSlack`'s `uipath:context`.

### 2. Connection ID and connection binding

The `uipath:binding` block in the process `extensionElements` uses:

```
default="PLACEHOLDER_CONNECTION_ID"
```

This placeholder is deliberately non-functional. To resolve it:

```
uip is connections list --all-folders --output json
```

Find the Slack connection entry. Copy its `Id` field and replace
`PLACEHOLDER_CONNECTION_ID` in the `uipath:binding` block inside the BPMN
`extensionElements`.

> Always pass `--all-folders`; a folder-scoped listing silently misses
> connections in other folders.

### 3. Enriched operation metadata (activity, method, path, body schema, output schema)

Once you have a connection ID, run the full enrichment call:

```
uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <discovered-connection-id> \
    --object-name <operation-object-name> \
    --output json
```

The response's `ISEnrichment` block supplies the authoritative values for:

| Placeholder in BPMN | Resolved from ISEnrichment |
|---|---|
| `PLACEHOLDER_OPERATION` | `ISEnrichment.activity` / operation name |
| `PLACEHOLDER_METHOD` | `ISEnrichment.method` |
| `PLACEHOLDER_PATH` | `ISEnrichment.path` |
| Body CDATA in `uipath:input name="body"` | `ISEnrichment.inputSchema` / generated body template |
| Output `type` and `source` on `uipath:output` | `ISEnrichment.outputSchema` |
| `Var_SlackResult` variable `type` | Narrows from `object` to the schema-derived type |

Replace all `PLACEHOLDER_*` values and the body CDATA with the ISEnrichment
output. Do not hand-author these values from Slack API documentation — the
enrichment call generates the correct schema for the specific tenant connector
version.

### 4. Folder key (`folderKey`)

The `PLACEHOLDER_FOLDER_KEY` value in `Task_SendSlack`'s context must be
replaced with the real folder key from the connection discovery output (the
folder in which the connection is registered). This is visible in the output
of `uip is connections list --all-folders`.

### 5. `bindings_v2.json` resources array

The scaffolded `bindings_v2.json` has an **empty** `resources` array:

```json
{ "version": "2.0", "resources": [] }
```

The CLI packaging step (`uip maestro bpmn pack`) populates `resources` with the
live connection binding. Do not hand-author this array. The project **cannot be
packaged** until this array is populated.

### 6. Generated package metadata files

The following files were scaffolded from the BPMN source and represent a
structural starting point. They must be regenerated or enriched by the CLI
after all BPMN placeholder values are resolved:

| File | Blocker |
|---|---|
| `bindings_v2.json` | `resources` array empty (see item 5 above) |
| `entry-points.json` | Input/output schemas are draft; update after enrichment changes variable types |
| `operate.json` | Correct as-is; re-validate after any BPMN filename change |
| `package-descriptor.json` | Correct as-is; re-validate after adding assets |
| `project.uiproj` | Correct as-is |

Run the drift checker before every pack:

```
python3 scripts/check_metadata_drift.py \
    --bpmn SlackDigestBoundaryBpmn.bpmn \
    --project-dir .
```

---

## What is already complete (no CLI enrichment needed)

- BPMN document scaffold, namespaces, process, and entry-point declaration.
- All three process variables: `DigestText`, `SlackResult`, `DigestChannel`.
- `Prepare Digest` ScriptTask: assembles a digest string from `DigestChannel`
  and writes it to `DigestText`. Replace the script body CDATA with real
  aggregation logic before production use; the mapping and variable wiring are
  final.
- Sequence flows and left-to-right diagram geometry. All nodes have `BPMNShape`
  entries; all flows have `BPMNEdge` entries with waypoints.
- Structural `uipath:bindings` block and `Binding_SlackConn` entry (placeholder
  connection ID must be replaced — see item 2 above).
- Validator result: **VALID** (all PO.Frontend canvas rules pass on the
  structural draft).

---

## Files in this project

| File | Purpose |
|---|---|
| `SlackDigestBoundaryBpmn.bpmn` | BPMN process source — the authoritative file |
| `project.uiproj` | Package project descriptor (scaffolded) |
| `operate.json` | Runtime operate descriptor (scaffolded) |
| `entry-points.json` | Entry-point schema manifest (scaffolded; update after enrichment) |
| `bindings_v2.json` | Connection binding manifest — resources array empty (CLI-owned) |
| `package-descriptor.json` | Package content descriptor (scaffolded) |
| `README.md` | This file — enrichment blockers and project notes |

---

## Prohibited actions on this draft

Do **not** upload, publish, deploy, or run this project until all CLI-owned
enrichment blockers listed above are resolved. Uploading a project whose
`bindings_v2.json` has an empty `resources` array, or whose `Task_SendSlack`
context contains `PLACEHOLDER_*` values, will result in a non-functional or
incorrectly-bound process instance.
