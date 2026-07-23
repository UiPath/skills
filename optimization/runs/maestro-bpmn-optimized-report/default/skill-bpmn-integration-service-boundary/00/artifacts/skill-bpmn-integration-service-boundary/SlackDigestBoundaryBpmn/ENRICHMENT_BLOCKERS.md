# SlackDigestBoundaryBpmn — CLI-Owned Enrichment Blockers

This project is a **local draft** and is **not ready to upload, publish, or run**.
The `Task_SendSlack` node (Intsvc.ActivityExecution) is a structural BPMN shell
whose Integration Service context fields, body schema, connection binding, generated
outputs, and package metadata are entirely CLI-owned. No identifier has been invented.

---

## What "draft executable boundary" means

The BPMN file is structurally valid: it parses, passes the canvas schema rules,
and its diagram renders all four nodes. The `Task_SendSlack` `bpmn:SendTask`
carries the correct `uipath:activity` wrapper and `<uipath:type
value="Intsvc.ActivityExecution" version="v1" />` child element.

**The node is NOT runnable** because the following six context-field placeholders
are deliberately blank, and the following four file-level artifacts do not yet exist.

---

## Blocker 1 — Slack connector resource key (`connectorKey`) and operation name (`activity`)

The `connectorKey` context field must hold the canonical resource key for the
Slack Integration Service connector, as served by the live registry.

The `activity` field in the BPMN currently holds the literal string
`DRAFT_REPLACE_VIA_CLI_ENRICHMENT`. This is a structural placeholder that
satisfies the canvas required-field validation rule while making the draft
status unambiguous. It must be replaced with the real operation name resolved
by the CLI steps in Blocker 3.

**CLI step required (for connectorKey):**

```
uip maestro bpmn registry search slack --output json
```

Inspect `Data[*].ExtensionType` entries whose label or key references Slack.
Copy the exact `connectorKey` value into `Task_SendSlack`'s context:

```xml
<uipath:input name="connectorKey" value="<value-from-registry-search>" />
```

Do **not** guess or derive this value from the brand name.

---

## Blocker 2 — Live connection ID and folder key (`connection`, `folderKey`)

A tenant connection to Slack must exist in Integration Service before the node
can execute. The connection ID and the folder key are discovered — never invented.

**CLI step required:**

```
uip is connections list --all-folders --output json
```

From the response, locate the Slack connection entry and record:

- `Id`          → the connection UUID (used in Blocker 3 below and in `bindings_v2.json`)
- `FolderKey`   → the Orchestrator folder the connection belongs to

Fill the context fields:

```xml
<uipath:input name="folderKey" value="<FolderKey-from-connections-list>" />
```

The `connection` field is **not** filled with a literal ID; it is filled with a
binding reference (see Blocker 4).

---

## Blocker 3 — Connector operation metadata (`activity`, `method`, `path`)

The connector operation name (e.g. `PostMessage`), HTTP method, and route path
are emitted by the ISEnrichment block that the CLI returns when you supply a live
connection ID and object name. These fields cannot be authored by hand.

**CLI step required (after Blocker 2 is resolved):**

```
uip maestro bpmn registry get Intsvc.ActivityExecution \
    --connection-id <Id-from-Blocker-2> \
    --object-name <Slack-object-name> \
    --output json
```

From `Data.ExtensionType.ISEnrichment`, copy the resolved values into the context:

```xml
<uipath:input name="activity" value="<resolved-activity-name>" />
<uipath:input name="method"   value="<resolved-method>"        />
<uipath:input name="path"     value="<resolved-path>"          />
```

---

## Blocker 4 — Connection binding and `bindings_v2.json`

The `connection` context field must reference a process-level binding via
`=bindings.<bindingId>`, and a corresponding `<uipath:binding>` entry must exist
in the process-level `<uipath:bindings version="v1">` block. Additionally,
`bindings_v2.json` (a package metadata file) must list the live connection ID
under `resources`.

**Both the BPMN and the metadata file require CLI enrichment:**

1. Choose a stable binding ID (e.g. `Binding_Slack`).
2. Add to the BPMN process `<bpmn:extensionElements>`:

```xml
<uipath:bindings version="v1">
  <uipath:binding id="Binding_Slack"
                  resource="Connection"
                  propertyAttribute="ConnectionId"
                  default="<Id-from-Blocker-2>" />
</uipath:bindings>
```

3. Set the context field in `Task_SendSlack`:

```xml
<uipath:input name="connection" value="=bindings.Binding_Slack" />
```

4. In `bindings_v2.json`, populate the `resources` array with the live connection
   ID. The scaffold script writes an empty `resources` array; the CLI (or manual
   edit after the above steps) must fill it before packaging.

---

## Blocker 5 — Dynamic body schema and generated output schema

The `<uipath:input name="body">` CDATA is currently `{}` (empty placeholder).
The real request-body schema is generated from the `ISEnrichment` block returned
in Blocker 3. The output schema for `Var_SlackResult` is also generated from the
enrichment response. Neither schema may be hand-authored.

**Action:** After completing Blocker 3, replace the `body` CDATA with the
`inputSchema`-derived JSON structure from `ISEnrichment.inputFields`, and update
the output mapping's `type` from `custom` to the schema-resolved type.

---

## Blocker 6 — Package metadata files

The five package metadata files do not exist yet:

| File | Status |
|---|---|
| `project.uiproj` | Not generated |
| `operate.json` | Not generated |
| `entry-points.json` | Not generated |
| `bindings_v2.json` | Not generated (resources array must be populated — see Blocker 4) |
| `package-descriptor.json` | Not generated |

**CLI / script steps required (only after Blockers 1–5 are resolved):**

```
pip install defusedxml
python3 scripts/scaffold_metadata.py \
    --bpmn SlackDigestBoundaryBpmn/SlackDigestBoundaryBpmn.bpmn \
    --out-dir SlackDigestBoundaryBpmn/

# Then populate bindings_v2.json resources with the live connection ID.

python3 scripts/check_metadata_drift.py \
    --bpmn SlackDigestBoundaryBpmn/SlackDigestBoundaryBpmn.bpmn \
    --project-dir SlackDigestBoundaryBpmn/
```

Do not run `uip maestro bpmn pack` until `check_metadata_drift.py` exits 0.

---

## Upload / publish / run — explicit consent required

No upload, publish, deploy, or run has been performed. Any cloud-side action
requires explicit user consent and a passing local validation.

**Local validation command (run from the skill directory):**

```
cd /home/azureuser/projects/skills/tmp/skills/uipath-maestro-bpmn/validator
npm install --silent
node validate-bpmn.mjs \
  /work/output/artifacts/skill-bpmn-integration-service-boundary/SlackDigestBoundaryBpmn/SlackDigestBoundaryBpmn.bpmn
```

---

## Summary checklist

- [ ] Blocker 1 — Resolve `connectorKey` via `registry search slack`
- [ ] Blocker 2 — Resolve connection ID and folder key via `uip is connections list --all-folders`
- [ ] Blocker 3 — Resolve `activity`, `method`, `path` via `registry get Intsvc.ActivityExecution --connection-id <id> --object-name <obj>`
- [ ] Blocker 4 — Add `uipath:bindings` block to BPMN; populate `bindings_v2.json` resources
- [ ] Blocker 5 — Replace body CDATA and output schema from ISEnrichment `inputFields`
- [ ] Blocker 6 — Run `scaffold_metadata.py`, populate `bindings_v2.json`, run `check_metadata_drift.py`
- [ ] Validate BPMN with `validate-bpmn.mjs` (exit 0 required before upload)
- [ ] Obtain explicit user consent before any upload, publish, deploy, or run action
