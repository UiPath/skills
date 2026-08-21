# SlackDigestBoundaryBpmn — Draft Notes and CLI Enrichment Blockers

**Status:** LOCAL DRAFT — do NOT upload, publish, package, deploy, or run.

This project is structurally valid BPMN that expresses the intended process
shape. The Slack Integration Service step (`Task_SendSlack`) is a **draft
executable boundary**: its BPMN host element, `uipath:activity` wrapper, and
variable mappings are present, but all connector-specific values are stubs.
The node will not execute until every blocker below is resolved by CLI tooling.

---

## Process overview

```
Manual Start  →  Prepare Digest (ScriptTask)  →  Send Slack Digest (IS boundary)  →  Done
```

| Node ID             | Type                          | Status       |
|---------------------|-------------------------------|--------------|
| `Start_Manual`      | `bpmn:StartEvent` (none)      | Authored     |
| `Task_PrepareDigest`| `bpmn:ScriptTask` (Jint)      | Authored     |
| `Task_SendSlack`    | `bpmn:SendTask` IS boundary   | **DRAFT**    |
| `End_Done`          | `bpmn:EndEvent` (none)        | Authored     |

---

## CLI-owned enrichment blockers

The following items **cannot** be authored by hand and must be resolved through
UiPath CLI tooling before this project can be packaged or run. None of these
values have been invented or guessed in the BPMN source.

### 1. Slack connector resource key (`connectorKey`)

- **What is needed:** the exact connector key string from the Integration
  Service catalog that represents the Slack connector.
- **How to resolve:**
  ```
  uip login
  uip maestro bpmn registry get Intsvc.ActivityExecution --output json
  ```
  Then search the IS catalog for the Slack connector by name. Never infer
  the key from the brand name; use the value returned by the registry.
- **Placeholder in BPMN:** `PLACEHOLDER_CONNECTOR_KEY` on
  `Task_SendSlack > uipath:context > connectorKey`.

### 2. Live connection ID and connection binding

- **What is needed:** a provisioned Slack connection in the target tenant,
  and its connection ID from `uip is connections list`.
- **How to resolve:**
  ```
  uip is connections list --all-folders --output json
  ```
  Identify the Slack connection row; copy its `id` value.
- **Placeholder in BPMN:**
  - `PLACEHOLDER_CONNECTION_ID` in `uipath:bindings > uipath:binding > default`.
  - `PLACEHOLDER_BINDING_ID` in both the `uipath:binding id=` attribute and
    the `connection` context field (`=bindings.PLACEHOLDER_BINDING_ID`).
- **Note:** the binding ID must be a stable identifier chosen at enrichment
  time and must match between the `bindings` block and the `context` field.

### 3. Folder key (`folderKey`)

- **What is needed:** the Orchestrator folder key for the folder that owns
  the Slack connection.
- **How to resolve:** read from the `uip is connections list` response
  (the folder context of the returned connection).
- **Placeholder in BPMN:** `PLACEHOLDER_FOLDER_KEY` on
  `Task_SendSlack > uipath:context > folderKey`.

### 4. Connector operation metadata (`activity`, `method`, `path`)

- **What is needed:** the exact IS catalog operation name, HTTP method, and
  API path for the Slack "send message" (or equivalent) operation.
- **How to resolve:**
  ```
  uip maestro bpmn registry get Intsvc.ActivityExecution \
      --connection-id <resolved-connection-id> \
      --object-name <slack-object-name> \
      --output json
  ```
  The `ISEnrichment` block in the response contains `activity`, `method`,
  and `path` for every available operation on that object.
- **Placeholders in BPMN:** `PLACEHOLDER_SLACK_OPERATION`,
  `PLACEHOLDER_HTTP_METHOD`, `PLACEHOLDER_API_PATH` on `Task_SendSlack`.

### 5. Request body schema (dynamic, IS-catalog-owned)

- **What is needed:** the real field map for the Slack send-message body
  (field names, types, required vs optional). The stub `body` CDATA in the
  BPMN (`{"channel":"...","text":"..."}`) is indicative only; the actual
  field names (e.g. `channel`, `text`, `blocks`) must come from the IS
  enrichment response, not from documentation guesses.
- **How to resolve:** the `ISEnrichment.inputSchema` returned by the enriched
  `registry get` call above contains the authoritative field definitions.
- **Location in BPMN:** `Task_SendSlack > uipath:input[name="body"]` CDATA.

### 6. Dynamic output schema (`Var_SlackResult`)

- **What is needed:** the real response schema for the Slack connector
  operation (field names, types). The declared output variable `Var_SlackResult`
  is typed `object` as a placeholder; the actual schema and any field-level
  output mappings come from the IS enrichment response.
- **How to resolve:** `ISEnrichment.outputSchema` from the enriched
  `registry get` call.
- **Location in BPMN:** `Task_SendSlack > uipath:output`.

### 7. `bindings_v2.json` (CLI-generated, not hand-authored)

- **What is needed:** a valid `bindings_v2.json` with a populated `resources`
  array that references the resolved connection binding.
- **How to resolve:**
  1. Run `scripts/scaffold_metadata.py` to generate the stub file.
  2. Then run the CLI pack enrichment to populate the `resources` array.
- **Do not** hand-author `bindings_v2.json`; an empty or hand-written
  `resources` array will cause packaging or runtime binding failures.

### 8. Package metadata files (CLI-generated)

The following files do not exist yet and must be generated by
`scripts/scaffold_metadata.py` (from the BPMN skill's `scripts/` directory)
**after** all BPMN-source enrichment is complete:

| File                     | Generator                   |
|--------------------------|-----------------------------|
| `project.uiproj`         | `scaffold_metadata.py`      |
| `operate.json`           | `scaffold_metadata.py`      |
| `entry-points.json`      | `scaffold_metadata.py`      |
| `bindings_v2.json`       | `scaffold_metadata.py` then CLI pack enrichment |
| `package-descriptor.json`| `scaffold_metadata.py`      |

Run the scaffold script as:
```
python3 <skill-dir>/scripts/scaffold_metadata.py \
    --bpmn SlackDigestBoundaryBpmn/SlackDigestBoundaryBpmn.bpmn \
    --out-dir SlackDigestBoundaryBpmn/
```

Do not run `uip maestro bpmn pack` until `bindings_v2.json` resources are
populated by the CLI enrichment step.

---

## What is already authored (not blocked)

- BPMN document scaffold, namespaces, and process element.
- Three process variables: `DigestContent` (string), `SlackChannel` (string),
  `SlackResult` (object placeholder).
- `Start_Manual`: none-type start event with `uipath:entryPointId` and a
  `BPMN.Variables` mapping to accept `SlackChannel` at trigger time.
- `Task_PrepareDigest`: fully executable `bpmn:ScriptTask` (Jint v3) that
  assembles a digest string from `SlackChannel` and writes it to
  `DigestContent`. Replace the stub script body with real aggregation logic.
- All sequence flows and diagram geometry (left-to-right, non-overlapping).
- `End_Done`: none-type end event.
- `Task_SendSlack`: correct `bpmn:SendTask` host element with
  `Intsvc.ActivityExecution` wrapper, `uipath:type` child, variable wiring,
  and connections block — all structural requirements met. Only the runtime
  values are placeholders.

---

## Validation

Run the bundled validator (Node.js, no upload required):

```
cd <skill-dir>/validator && npm install --silent
node validate-bpmn.mjs <path-to>/SlackDigestBoundaryBpmn.bpmn
```

The validator will flag `Task_SendSlack` as an IS connector node with
unresolved context fields. This is expected for a draft boundary node.
Fix all ERROR-severity findings before proceeding; warnings do not block import.

---

## Prohibited actions until blockers are resolved

- Do NOT upload to Studio Web or Orchestrator.
- Do NOT publish or deploy.
- Do NOT run or debug any instance.
- Do NOT hand-fill connector keys, connection IDs, folder keys, operation
  names, or schemas — these must come from CLI discovery and enrichment.
