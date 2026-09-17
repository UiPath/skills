# Connector Activity Nodes — Non-catalog (inline) activities

Use this walkthrough for a node whose type is `uipath.connector.custom.<connector-key>.<slug>`: an activity Integration Service does **not** carry, generated from the vendor's API docs by [/uipath:uipath-platform — activity-generation.md](../../../../../uipath-platform/references/integration-service/activity-generation.md). The node carries the whole activity — its metadata and its scripts — and the CLI builds the `definitions[]` entry from that metadata instead of fetching it from the registry.

Everything **not** listed here is identical to [impl.md](impl.md): follow its Configuration workflow and substitute only the steps below. The ownership rules do not change — `definitions[]` and `inputs.detail` are still CLI-written; you never hand-author either.

## When this applies

- Tier 2 of the [decision order](planning.md#decision-order): the connector exists, lacks the curated activity, and reports `v4Compatible: true`.
- The activity is **already generated** — you have `<Name>.json` (the compiled activity metadata) and one `<scriptRef>.js` per action and lookup. If you do not, stop here: identify the gap and hand the user off to the `uipath-platform` skill's activity generation ([SKILL.md rule #4](../../../../SKILL.md#critical-rules-universal) — never invoke it yourself), then resume with the artifacts.

## Inputs

| Artifact | Produced by | Used for |
|---|---|---|
| `$WORK/<Name>.json` | `uip is activities metadata generate` | `--metadata`; becomes the definition and `inputs.inlineActivityConfiguration.metadata` |
| `$WORK/<Name>.js`, `$WORK/<Lookup>.js` | `uip is activities script update` | `--scripts $WORK`; one `<scriptRef>.js` for the main action and for **every** `reference.scriptRef` in the metadata |

Keep `$WORK` until the node is added. The flow carries copies of the scripts; the files are what you re-add from if the metadata changes.

## Node type

`uipath.connector.custom.<connector-key>.<slug>`

- `<connector-key>` must equal the metadata's `elementKey` (`uipath-salesforce-slack`); `node add` refuses a mismatch.
- `<slug>` is the activity's display name in kebab case: `Add Users to Usergroup` → `add-users-to-usergroup`.
- A flow holds **one definition per type**. Two nodes with the same type share it, so the same slug must mean the same metadata; a different activity needs a different slug. `node add` refuses a second node whose metadata differs from the embedded definition.

The `custom` segment is what marks a non-catalog activity. Do not confuse it with a `custom-*` **connector key** (a Connector Builder connector, see [connectors.md — Connector Disambiguation](../../../../../uipath-platform/references/integration-service/connectors.md#connector-disambiguation)); the key here is the catalog connector's.

## Step 1 — Fetch and bind a connection

Unchanged: [impl.md — Step 1](impl.md#step-1--fetch-and-bind-a-connection).

## Step 2 — Read the metadata (replaces `registry get` and `describe`)

There is nothing to fetch. `$WORK/<Name>.json` **is** the metadata, and it has one verb slot:

| You need | Read |
|---|---|
| `method`, `endpoint` | `metadata.method.<VERB>.method`, `metadata.method.<VERB>.path` (the vendor path, e.g. `/usergroups.users.update`) |
| operation, main script | `metadata.method.<VERB>.operation`, `metadata.method.<VERB>.scriptRef` |
| `queryParameters`, `pathParameters` | `metadata.method.<VERB>.parameters[]` by `type` (`query` / `path`); `required` on each |
| `bodyParameters` | `fields.<name>` whose `method.<VERB>.request` is `true`; `required` on that entry |
| reference fields | `reference.scriptRef` on a parameter or a field (the lookup script's base name) |

The activity's `objectName` is the metadata's top-level `name` (`AddUsersToUsergroup`). You never pass it — the CLI reads it from the definition it built. As with any connector node: **write only parameter names the metadata lists, in the bucket it lists them under.**

## Step 3 — Add the node

```bash
uip maestro flow node add <file>.flow \
  uipath.connector.custom.<connector-key>.<slug> \
  --label "<Label>" \
  --metadata $WORK/<Name>.json --scripts $WORK --output json
```

Expect `Code: NodeAddSuccess`, `Data.DefinitionAdded: true` (`false` when a node of this type already exists and the metadata matches), and `Data.InlineActivity: { ScriptRef, Scripts[] }` listing every embedded script.

What it writes, and what you leave alone:

- `definitions[]` — the node manifest, built from the metadata at `version: "4.0.0"`. Its `connectorDetail.uiPathActivityTypeId` is a **placeholder random UUID**: Studio's TypeCache assigns the real one for catalog activities, and nothing assigns one for a non-catalog activity yet.
- `inputs.inlineActivityConfiguration` — `{ metadata, scriptRef, scripts }`: the metadata verbatim, the main action's `scriptRef`, and every script's source by ref.

Failures are all `Result: Failure`, exit `1`, and name the fix: a script missing from `--scripts` (the message lists every missing `<scriptRef>.js`), `--metadata` without `--scripts` or the reverse, a `custom` type added without them, a type whose connector key is not the metadata's `elementKey`, or a same-type node with different metadata.

## Step 4 — Resolve reference fields with the local lookup script

The lookup scripts are not published, so `--script-ref` cannot find them. Run the local file instead — a plain path ending in `.js`, no `@` prefix:

```bash
uip is resources run script --connection-id "<id>" \
  --inline-script $WORK/<lookupRef>.js --body '{}' --output json
```

Read the rows in `Data.Body` (an array), match `lookupNames`, take `lookupValue`. Every other rule of [impl.md — Step 4](impl.md#step-4--resolve-reference-fields) applies unchanged: connection-scoped IDs, resolve freshly before configure, zero-match and failed-call handling.

## Step 5 / 5b — Required fields and upstream wiring

Unchanged: [impl.md — Step 5](impl.md#step-5--validate-required-fields), [Step 5b](impl.md#step-5b--wire-upstream-outputs). Required fields come from the metadata entries in Step 2.

## Step 6 — Configure the node

Same `--detail` keys as any connector node. `method` and `endpoint` come from the verb slot. Do **not** pass `objectName`, `activityContext`, `scripts` or anything from the metadata — the CLI derives those.

```bash
uip maestro flow node configure <file>.flow <nodeId> --detail "$(cat /tmp/detail.json)" --output json
```

with, for example:

```json
{ "connectionId": "<id>", "folderKey": "<key>",
  "method": "POST", "endpoint": "/usergroups.users.update",
  "bodyParameters": { "usergroup": "<resolved id>", "users": "=js:$vars.pickUsers.output.ids" } }
```

What `node configure` does differently for an inline node:

- reads the metadata from `inputs.inlineActivityConfiguration` — no Integration Service request;
- writes `inputs.detail.activityContext` as `{ "version": "4.0.0", "source": "inline", "scriptRef": "<main scriptRef>" }` — `source: "inline"` is how the runtime knows to run the embedded activity, and `scriptRef` is the main action, not the `objectName`;
- builds `configuration` (`essentialConfiguration`) with `objectName` = the metadata's `name` and `path` = the vendor path;
- copies `uiPathActivityTypeId` from the definition, so re-running configure never changes it;
- keeps `inputs.inlineActivityConfiguration` across re-runs. Re-configure with the complete intended `--detail`, exactly as for any connector node.

## Validate

`uip maestro flow validate` runs the usual connector checks plus, for this node, offline:

- a `uipath.connector.custom.*` node must carry `inputs.inlineActivityConfiguration`, and a node carrying it must have that type;
- the main `scriptRef` and every lookup `reference.scriptRef` in the metadata must have a source under `scripts`;
- once configured, `activityContext.source` must be `"inline"` and `activityContext.scriptRef` must equal the embedded `scriptRef`.

Fix a script gap by `uip maestro flow node remove` and re-adding with a complete `--scripts` directory; fix an `activityContext` mismatch by re-running `node configure`. A missing `uiPathActivityTypeId` is a defect in the definition — re-add the node, never paste one.

## Limits

- The `uiPathActivityTypeId` is a placeholder until TypeCache, or a published formula, supplies real ids for non-catalog activities.
- Running the flow needs a runtime that understands `activityContext.source: "inline"`. `flow validate` cannot tell you whether the tenant has it.
- `node add` echoes the node, embedded scripts included. Use `--output-filter "Data.InlineActivity"` when the scripts are large.
