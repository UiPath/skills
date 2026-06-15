# HTTP Request Node — Authoring from the StandardResource (SR) cache

When the prompt targets a known SaaS vendor action (e.g. "send a slack message to channel #order-ops", "create a jira ticket in project ENGCE"), use the SR cache to keep the vendor payload shape ready to plug into a connector-mode HTTP node. The first time you encounter a (connector, action) pair, you build the SR yourself from vendor docs and cache it. On subsequent runs you just read.

> **MANDATORY SEQUENCING — run this loop BEFORE `uip maestro flow node configure`.** Per [SKILL.md Critical Rule #3 — POC override](../../../../../SKILL.md) and [impl.md Step 2.5](impl.md), the SR cache MUST hold an entry for `(targetConnector, connectionId, object)` with **both request and response fields** before `node configure` runs on the corresponding HTTP node. The publish-time pipeline reads from this cache to build the eventual `custom-{org}-{vendor}` connector — skipping the loop yields a connector with input-only schemas and no documented response shape. The defect is non-recoverable at publish time without rebuilding the cache and re-publishing.

> **The cli does NOT fetch vendor docs or IS metadata for you.** `standardize` is a thin validator + storer. The agent reads vendor docs (via WebFetch + training data) and constructs the SR with the response-field budget heuristic applied.

## Step 0: vendor name → connector key

Map each vendor in the prompt to its IS connector key. If unknown, run `uip is connectors list --output json | jq '.Data[] | {key,vendorName}'` and grep. Common mappings:

| Prompt term | Connector key |
|---|---|
| slack | `uipath-salesforce-slack` |
| jira | `uipath-atlassian-jira` |
| outlook / o365 | `uipath-microsoft-outlook365` |
| gmail | `uipath-google-gmail` |
| salesforce | `uipath-salesforce-sfdc` |
| servicenow | `uipath-servicenow-servicenow` |
| sendgrid | `uipath-sendgrid-sendgrid` |

This table is intentionally connector-only. Method, path, and field shape for every action come from vendor docs at authoring time (Step 1 below). Do NOT assume a path from memory — read the docs each time. Vendor APIs version, deprecate, and rename.

The phrase "using http-request" in the prompt names the **node type** (`core.action.http.v2`), NOT the auth mode. When a catalog `uipath-{vendor}-{product}` connector exists, use **connector mode** (set its key as `targetConnector`) + SR cache. Manual mode is the fallback only when no catalog connector covers the vendor. **The node type stays `core.action.http.v2` either way** — that's what makes it extractable by the POC's background-publish loop. Don't promote to a native `uipath.connector.<key>.<activity>` node just because the catalog connector exists — see [SKILL.md Critical Rule #3 — POC override](../../../../../SKILL.md).

## Lazy cache loop

```bash
KEY="<CONNECTOR_KEY>"
OBJ="<OPERATION_OBJECT>"   # the slug you'll use everywhere; pick what reads naturally
CID="<CONNECTION_ID>"

uip is resources sr "$KEY" "$OBJ" --connection-id "$CID" --output json
# Cache hit → done. Cache miss → build the SR (see "Build an SR" below), then:
# uip is resources standardize "$KEY" "$OBJ" --connection-id "$CID" --from-sr <path>
# uip is resources sr "$KEY" "$OBJ" --connection-id "$CID" --output json
```

Cache path: `~/.uipath/cache/integrationservice/<tenantId>/<connector>/<connection>/<object>.standard.json`. TTL 24h.

## Build an SR on cache miss

The agent owns this step. The cli does nothing here — you read docs and produce a JSON file.

### 1. Read the vendor docs

For each (vendor, action) you need:

1. Identify the vendor's official API docs URL. Use `WebSearch` if needed. Do NOT skip this step — even for SaaS you've seen before, the vendor may have versioned, deprecated, or renamed the endpoint since training.
2. `WebFetch` the docs page for the specific operation. Pull:
   - HTTP method (POST / GET / …).
   - Vendor URL **relative to the connection's base URL**, i.e. with the host stripped. Verify the host you stripped matches `uip is connections base-url <connection-id> --output json` so the connector proxy resolves to the same place at runtime.
   - Request body fields — names, types, required vs optional, enums, descriptions.
   - Reference fields (lookups) — endpoint paths and the response-shape mapping (`lookupValue` + `lookupNames`).
   - Response shape — capture per the **response-field budget** below.

If a field is a reference, capture the lookup endpoint + value/name fields under `reference`. Read the docs for the lookup endpoint too — its path is also vendor-specific.

#### Response-field budget

Target ~10 fields total per SR. Cache reads and downstream prompts both pay per field, so prune.

| Request field count | What to emit |
|---|---|
| `>= 10` | All request fields. **Zero** response fields. |
| `< 10` | All request fields + up to `(10 - request_count)` response fields. |
| `0` (GET / DELETE) | Up to 10 response fields. |

Request fields are load-bearing — never drop one. Response fields rank by:

1. Primary identifiers: `id`, `key`, `name`, `uid`, `guid`, `<entity>Id`, `<entity>Key`.
2. Fields the vendor docs mark required.
3. Fields any other node in the same flow consumes (`response.<field>` references).
4. Top-level scalars before nested objects.
5. Declaration order in vendor docs.

If a non-budget response field is genuinely needed downstream, include it and note why in the cap-override warning.

### 2. Write the SR JSON

Match the [StandardResource format](../../../../../../uipath-platform/references/integration-service/standard-resource-format.md). Minimum required structure:

```jsonc
{
  "name": "<object-slug>",
  "path": "<vendor-relative-path>",        // extracted from WebFetch of vendor docs in Step 1
  "type": "standard",
  "elementKey": "<connector-key>",
  "displayName": "<Human Name>",
  "custom": "no",
  "metadata": {
    "baseUrl": "<from uip is connections base-url>",
    "method": {
      "POST": {                              // verb keys: POST/GET/PUT/PATCH/DELETE
        "path": "<vendor-relative-path>",
        "method": "POST",
        "operation": "Create",               // Create | List | Retrieve | Update | Replace | Delete
        "description": "<from docs>",
        "parameters": []
      }
    },
    "primaryKey": ["<id-field-name>"]
  },
  "fields": {
    "<field-name>": {
      "name": "<field-name>",
      "displayName": "<from docs>",
      "type": "string",                      // string | integer | number | boolean | date | date-time
      "description": "<from docs>",
      "required": true,
      "request": true,
      "design": { "position": "primary" },
      "reference": {                         // OPTIONAL — only for lookup fields
        "objectName": "<lookup-object-name-from-docs>",
        "path": "<lookup-endpoint-from-docs>",
        "lookupValue": "<id-field-on-lookup-response>",
        "lookupNames": ["<display-field-on-lookup-response>"]
      }
    }
  }
}
```

Save to a tmp path (e.g. `/tmp/<connector>-<object>.sr.json`).

### 3. Cache it

```bash
uip is resources standardize "$KEY" "$OBJ" \
  --connection-id "$CID" \
  --from-sr /tmp/<connector>-<object>.sr.json \
  --output json
```

`standardize` validates the JSON against `StandardResourceSchema` and writes it to the cache path. On validation error it tells you which field is wrong; fix the JSON and re-run.

### Alternative: compact spec → expander

If you'd rather author the shorter ipe-style spec (~58% smaller JSON, expander adds boilerplate), write a `<op>.spec.json` and pass `--from-spec` instead. See the [generate-standard-resource skill](https://github.com/UiPath/skills/blob/main/skills/uipath-platform/references/integration-service/standard-resource-format.md) for the spec shape.

## Reading SR for an HTTP-request-activity node

After `sr` returns the cached SR, pull these fields:

| HTTP-node field | SR source |
|---|---|
| `method` | First verb in `metadata.method` |
| `url` (relative) | `metadata.method.<VERB>.path` — this IS the vendor path; you authored it from docs |
| Base URL preview | `metadata.baseUrl` (do NOT hardcode into `url`; connector mode prepends it at runtime) |
| Required body fields | `Object.keys(fields).filter(f => fields[f].request && fields[f].required)` |
| Optional body fields | `Object.keys(fields).filter(f => fields[f].request && !fields[f].required)` |
| Reference lookups (channel→id, user→id) | `fields[name].reference` — resolve via [reference-resolution.md](../../../../../../uipath-platform/references/integration-service/reference-resolution.md) |
| Reference field UX hints | `fields[name].design.description` |

## End-to-end shape

Prompt example (any two-vendor "send X and create Y" flow follows this shape):
> "Create a flow that sends a `<vendor-A>` message AND creates a `<vendor-B>` record — using http-request activity."

Agent steps:

1. Parse → `[(<connector-key-A>, <action-A>), (<connector-key-B>, <action-B>)]`.
2. Resolve each `connectionId` via `uip is connections list <connector-key> --all-folders --output json`.
3. For each pair: `uip is resources sr <connector> <object> --connection-id <id> --output json`. Cache hit → use it. Cache miss → continue.
4. On cache miss: `WebFetch <vendor-api-docs-url>` for each action. Extract method, vendor relative path, required + optional fields, references. Build SR JSON files (see "Build an SR on cache miss" above).
5. `uip is resources standardize <connector> <object> --connection-id <id> --from-sr <path> --output json` for each. Validates + caches.
6. Re-read via `sr`. Extract `method`, `url` (vendor relative path), body field names, references.
7. Resolve reference fields to IDs (e.g. channel name → id via the reference endpoint declared in the SR).
8. Author two `core.action.http.v2` nodes following [impl.md — Step 3 connector mode](impl.md#step-3--configure-the-node). The `--detail` JSON shape:

```jsonc
{
  "authentication": "connector",
  "targetConnector": "<connector-key>",       // from Step 1
  "connectionId": "<connection-id>",          // from Step 2
  "folderKey": "<folder-key>",                // from connections list
  "method": "<verb-from-sr>",                 // metadata.method.<VERB>.method
  "url": "<vendor-relative-path-from-sr>",    // metadata.method.<VERB>.path — vendor URL, NOT IS slug
  "body": { /* body shape from sr.fields, with reference fields resolved to IDs */ }
}
```

9. Wire `start` → node-A → node-B → `end` per [impl.md — Step 5](impl.md#step-5--wire-edges).
10. `uip maestro flow validate "<ProjectName>.flow" --output json`.

Every concrete value (`method`, `url`, body field set, reference endpoints) MUST come from a live `sr` read in this run. None of them are baked into this doc.

## When to use SR cache vs raw `http-request` discovery

| Use SR cache | Use raw `http-request` |
|---|---|
| Repeated vendor action with stable payload shape | One-off identifier resolution (channel id from name, user id from email) |
| Need the full body shape + references + base URL ready to plug in | Need a single vendor-API value before composing |
| Building the same flow shape across multiple prompts → cache pays off | Vendor endpoint with no documented schema; probe to verify |

Both coexist. `http-request` (via `uip is resources run create <connector> http-request --body '{"method":"GET","url":"<vendor-path>"}'`) stays the right tool for resolving lookup values.

## Seeding the cache from an existing flow

When the user already has a flow with configured `core.action.http.v2` nodes, skip vendor-docs research for the request shape — pull it from the nodes:

```bash
uip maestro flow extract-http-nodes <ProjectName>.flow --output json
```

Emits one compact spec per `(elementKey, verb, normalizedPath)` tuple to `./extracted-specs/<elementKey>/<name>.spec.json`. Element-key resolution per node:

| Node configuration | Source of `elementKey` |
|---|---|
| Manual mode (absolute URL) | Hostname-derived `design-<org>-<vendor>`; override with `--vendor-hint` |
| Connector-mode, `targetConnector: design-<org>-<vendor>` | Passes through unchanged |
| Connector-mode, `targetConnector: custom-<org>-<vendor>` | Twin-mapped to `design-<org>-<vendor>` (org segment preserved verbatim) |
| Connector-mode, `targetConnector: uipath-<vendor>-<product>` (catalog) | `design-<accountName>-<slug>` |
| Connector-mode, `targetConnector: uipath-uipath-http` (generic proxy) | **Requires `--connection-vendor-hint <connectionId>=<vendor>`** per node — the proxy carries no vendor identity. Without the hint the node is skipped and reported. |

For a flow with three connections under `uipath-uipath-http` (outlook, salesforce, slack), pass one hint per connection:

```bash
uip maestro flow extract-http-nodes my-flow.flow --output json \
  --account-name acmecorp \
  --connection-vendor-hint conn-outlook-1=outlook \
  --connection-vendor-hint conn-salesforce-1=salesforce \
  --connection-vendor-hint conn-slack-1=slack
```

Resolves to `design-acmecorp-outlook`, `design-acmecorp-salesforce`, `design-acmecorp-slack`. The HTTP nodes' runtime binding (`uipath-uipath-http` + each connection) stays on the flow file unchanged.

Auth headers (`Authorization`, `X-Api-Key`, `Cookie`, anything containing `token`/`secret`/`key`/`auth`/`password`) are stripped — their names land in the report, values never.

The extractor seeds only the **request** side. Run the response-field-budget pass yourself before publishing.

Then promote each spec into the cache:

```bash
for spec in extracted-specs/<connector-key>/*.spec.json; do
  obj=$(basename "$spec" .spec.json)
  uip is resources standardize <connector-key> "$obj" \
    --connection-id <connection-id> --from-spec "$spec" --output json
done
```

## From flow to published connector

Background-publish-by-default. The flow keeps its HTTP nodes; the cached SRs become a reusable custom connector as a parallel side effect. This means:

- **The .flow file is NEVER mutated by this loop.** Rebinding HTTP nodes to the new connector is an explicit opt-in via `uip maestro flow rewrite-http-to-connector` — power-user tool, not in the default agent flow.
- The connector publish runs **async** via `remote publish --background`. The user proceeds with their primary destination (Studio Web / Orchestrator) without waiting.
- Studio Web sees the new connector in the picker 5-10 min later (registry propagation). The connection-creation prompt is deferred — the user creates one when they actually need to USE the connector in a future flow.

### The design → custom lifecycle

A single logical connector has **three coexisting key names** across its lifecycle. Confusing them is the most common source of "why doesn't this command find it" errors.

| Key | Where it lives | Visible to `flow registry`? | Filtered by POC override? | Created/written by |
|---|---|---|---|---|
| `uipath-{vendor}-{product}` (catalog) | `element_metadata` table | Yes | **Yes — filtered out** | CI semantic-release — read-only to users |
| `uipath-uipath-http` (generic HTTP proxy) | `element_metadata` table | Yes | **Yes — filtered out** | Backing connector for `core.action.http.v2`; agent's runtime binding only |
| `design-{org}-{vendor}` (creator-scoped) | `connector` table | **No** — invisible by nature | N/A | `uip is connectors builder remote import` |
| `custom-{org}-{vendor}` (tenant-wide published) | `element_metadata` table | Yes | **No — passes through filter** | `uip is connectors builder remote publish` (promotes the matching design-connector) |

**Key change vs catalog connectors**: `custom-*` is the POC's own output and *does* show up in `flow registry search/get` during the POC. Second-run flows reuse it instead of starting from scratch.

The publish chain: **edit design state → `remote import` → `remote publish` → `custom-` entry appears (5-10 min registry propagation) → `flow registry` would see it (if the POC filter weren't in place)**.

**Appending an activity to an already-published custom connector** follows the same chain: pull the design-state record (`remote get --include files`), add the new SR + element.json entry, `remote import` to update the design, `remote publish` to refresh the `custom-` published twin. Until `remote publish` completes, the new activity is not visible to `flow registry` — even though the design changes are persisted.

#### Which command surface for which question

`flow registry` and the connector-builder's `remote get` are two different surfaces with two different purposes. Use the right one per question:

| Question | Right command |
|---|---|
| "What node type should I use for this vendor API call?" (authoring) | Don't query — POC override says default to `core.action.http.v2`. |
| "Does a design connector for this vendor exist on the tenant?" (publish-time state discovery, Q2) | `uip is connectors builder remote get --key design-{org}-{vendor}` |
| "What activities does the existing design connector already have?" (Shape B/C triage) | `uip is connectors builder remote get design-{org}-{vendor} --include files` + `resource list` |
| "Does the user have a connection to this catalog or custom connector?" (connection binding for HTTP nodes) | `uip is connections list --all-folders` |
| "Is my background publish job done yet?" | `uip is connectors builder remote publish-status <publishId>` |

`flow registry search/get` is the wrong tool for every one of these — it only sees `element_metadata` (catalog + published custom), it can't see design-state connectors at all, and per the POC override it's filtered to near-empty anyway.

#### What's on the HTTP node vs what's published

For a single Outlook operation, the user ends up with these three names side-by-side:

| Field | Value | Purpose |
|---|---|---|
| HTTP node's `inputs.detail.bodyParameters.targetConnector` | `uipath-microsoft-outlook365` (catalog) or `custom-acmecorp-outlook365` (already-published custom) | **Runtime binding** — the connector that supplies base URL + auth at execute time. Stays put through every cycle. |
| The SR cache file path | `~/.uipath/cache/integrationservice/<tenantId>/<targetConnector>/<connectionId>/<object>.standard.json` | Cache key matches `targetConnector` (catalog or custom — whichever the connection is bound to). Lookup at authoring time. |
| Extractor's emitted `elementKey` | `design-{org}-outlook365` (remapped) | **Design-state key** for the custom connector being authored/extended. Used by `remote import` + `remote publish`. |
| After `remote publish` succeeds | `custom-{org}-outlook365` | **Published-state key** — what users see in Studio Web. Tenant-wide. |

The extractor handles the catalog/custom → design remap automatically: any `targetConnector` not already prefixed `design-` is converted to `design-{org}-{slugified-vendor}` for the published connector. The runtime binding (the catalog or already-published custom key on the HTTP node) is preserved as metadata in the spec so the publish step can inherit auth + base URL from it.

### Second-run reuse — existing custom connector in the registry

Per the POC override, `custom-*` connectors are NOT filtered from `flow registry`. When the agent picks a node type for a vendor on a second run, the registry may already have a POC-produced custom connector. Decide what to do before authoring the HTTP node.

**Step 1 — search per vendor:**

```bash
uip maestro flow registry search "outlook" --output json --output-filter "[*].{NodeType:NodeType,DisplayName:DisplayName}"
```

After POC filtering (catalog dropped, custom kept), one of two outcomes per vendor:

**Outcome A — no `custom-{org}-{vendor}` match.** First-run path: author `core.action.http.v2` connector-mode against `uipath-uipath-http` with the user's vendor-specific connection. SR cache loop populates the cache as usual. At publish time, Q2 Shape A creates a fresh design connector and promotes it to `custom-*`.

**Outcome B — `custom-{org}-{vendor}` exists.** Inspect its activities:

```bash
uip maestro flow registry get "uipath.connector.custom-{org}-{vendor}.<expected-action>" --output json
# Or list all activities on the connector:
uip maestro flow registry search "custom-{org}-{vendor}" --output json
```

Two sub-cases:

**B.1 — action present on the custom connector.** The activity the user wants is already built and published. Ask the user:

```text
AskUserQuestion: "Custom connector 'custom-acmecorp-outlook' already has the
                  'send_message' activity. How to use it?"
  - Use the existing native activity                                      (default)
       Authors a uipath.connector.custom-acmecorp-outlook.send_message node.
       Requires a connection to custom-acmecorp-outlook — agent creates one
       via `uip is connections create custom-acmecorp-outlook` if none exists.
  - Fall back to HTTP node
       Authors core.action.http.v2 against uipath-uipath-http with the
       vendor-specific connection. At publish time, the POC's Shape C
       triage runs (keep-both rename / replace / skip — see below).
  - Skip this action — I'll wire it manually
```

If the user picks "Use the existing native activity":
- Run `uip is connections list --all-folders --output json` filtered by `connectorKey == custom-acmecorp-outlook`.
- If a connection exists → use its `connectionId` directly.
- If no connection exists → `uip is connections create custom-acmecorp-outlook` (interactive OAuth/API-key flow).
- Author the node with `uip maestro flow node add uipath.connector.custom-acmecorp-outlook.send_message` + `node configure`.

If the user picks "Fall back to HTTP node":
- Author `core.action.http.v2` connector-mode pointing at `custom-acmecorp-outlook` (or `uipath-uipath-http` if a custom-keyed connection isn't available).
- At publish time, the [Q2 Shape C triage](#shape-c--existing-connector-activity-collision) runs — keep-both with rename (default), replace with diff confirmation, or skip.

**B.2 — action NOT present on the custom connector.** Auto fall back to HTTP node. No AskUserQuestion needed — the only sensible path is "author HTTP and let publish-time Shape B append the new activity to the existing custom connector". Tell the user this is happening so they're not surprised when `custom-acmecorp-outlook` grows a new activity after publish.

```text
Connector 'custom-acmecorp-outlook' exists but doesn't have 'read_inbox' yet.
Authoring an HTTP node now; at publish time we'll append 'read_inbox' to it.
```

### Q2 — the state-aware prompt

After the user picks a destination from the [What's next dropdown](../../greenfield.md#whats-next-dropdown), run a discovery batch and ask Q2 based on what's already on the tenant.

**Step 1 — discover state per distinct elementKey in the extracted specs:**

```bash
# Pull every distinct elementKey from extract-http-nodes output (one per vendor)
KEYS=$(jq -r '.[].spec.elementKey' extracted-specs/_report.json | sort -u)

# Check each one in parallel
for KEY in $KEYS; do
  uip is connectors builder remote get --key "$KEY" --output json > /tmp/remote-get-"$KEY".json &
done
wait

# Existing connectors (200) get their on-disk activity list pulled too:
for KEY in $KEYS; do
  if jq -e '.Result == "Success"' /tmp/remote-get-"$KEY".json > /dev/null; then
    uip is connectors builder remote get "$KEY" --include files --output json
    # parse .Data.Resources[].name → activity-set for this key
  fi
done
```

**Step 2 — pick the prompt shape per elementKey:**

| State | Detection | Prompt shape |
|---|---|---|
| **A. New connector** | `remote get` returned 404 | Shape A below |
| **B. Existing connector, no collisions** | `remote get` 200, no `spec.name` matches an existing activity | Shape B below |
| **C. Existing connector, ≥1 collision** | `remote get` 200, at least one `spec.name` ∈ existing activity set | Shape B for non-collisions + Shape C per colliding activity |

#### Shape A — net-new connector

```text
AskUserQuestion: "Also publish the HTTP nodes as a new custom connector 'design-acmecorp-stripe' in the background?"
  - Yes — publish in the background as a new connector       (default)
  - No  — leave the connector unpublished
  - Show me what would be published before deciding
```

#### Shape B — existing connector, only new activities

```text
AskUserQuestion: "Connector 'design-acmecorp-stripe' already exists. Republish it in the background to add 2 new activities (refunds, disputes)?"
  - Yes — republish in the background for the existing connector  (default)
  - No  — leave the existing connector untouched
  - Show me what would change (per-activity diff)
```

#### Shape C — existing connector, activity collision

Asked **per colliding activity**. Non-colliding activities from the same flow proceed through Shape B's path without re-prompting.

```text
AskUserQuestion: "Connector 'design-acmecorp-stripe' already exists, but 'charges' is already an activity on it. How to handle?"
  - Keep both — rename the new one to 'charges_v2'   (default; safest)
  - Replace the existing 'charges' activity           (audit field deltas first — see below)
  - Skip 'charges' — don't publish it
  - Something else
```

When the user picks **Replace**, diff field sets first:

```bash
diff <(jq -S '.fields | keys' app/element/standard-resources/charges.json) \
     <(jq -S '.fields | keys' ~/.uipath/cache/integrationservice/<tenantId>/<elementKey>/<connection>/charges.standard.json)
```

If the existing SR has fields the new one doesn't, ask once more:

```text
AskUserQuestion: "Replacing 'charges' will drop 3 fields the existing activity has but yours doesn't: reason, metadata, idempotency_key. Proceed?"
  - Replace anyway
  - Cancel — keep both with rename instead
```

If field sets are identical or the new one is a superset, replace is safe — no second prompt.

#### Multi-vendor batching

When the flow has HTTP nodes hitting more than one vendor (e.g. `api.stripe.com` and `api.shopify.com`), extract produces multiple distinct elementKeys. Run the discovery batch above for all of them, then surface the consolidated plan in **one** AskUserQuestion:

```text
AskUserQuestion: "Also publish HTTP nodes as connectors in the background?
                  • design-acmecorp-stripe   — extends existing (1 new activity)
                  • design-acmecorp-shopify  — new connector (3 activities)"
  - Yes — publish both
  - Yes — only the new connector (skip the extension)
  - No  — skip all
  - Show me the per-connector plan
```

### Background publish pipeline (per accepted elementKey)

After Q2 settles per-key state, run the pipeline. Steps adapt to state — skip what's not needed.

```bash
# 1. Scaffold connector tree                          (State A only)
uip is connectors builder connector scaffold --name '<Display Name>' --output json

# 2. Pull cached SRs into app/element/standard-resources/
uip is connectors builder resource sync-from-cache --output json
#   --connection-id, --object-name to scope
#   --overwrite ONLY for Shape C "Replace" path

# 3. Wire NEW SRs into element.json (per new object)
#    Shape A: every spec is new           → resource create per object
#    Shape B: only the new ones           → resource create per new object
#    Shape C "Rename":                    → resource create --name <object>_v2
#    Shape C "Replace":                   → state patch to align element.json with overwritten SR
uip is connectors builder resource create --name <object> \
  --vendor-path "$(jq -r '.data.metadata.method | to_entries[0].value.path' \
                   ~/.uipath/cache/integrationservice/<tenantId>/<connector>/<connection>/<object>.standard.json)" \
  --methods <comma-separated-verbs> --output json

# 4. Configure auth                                   (State A only)
uip is connectors builder auth set --auth-type <oauth2|basic|...> --output json

# 5. Validate
uip is connectors builder connector validate --output json

# 6. Push design connector to tenant (POST when 404; PUT when 200)
uip is connectors builder remote import --output json

# 7. Background-promote design → tenant-wide CUSTOM lifecycle
uip is connectors builder remote publish --background --output json
#   Returns { PublishId, Status: "PROCESSING" }. Fire-and-forget — the agent does NOT wait.
```

Persist the pending publish so the next session can check it:

```bash
# Agent writes alongside the .flow
cat > <ProjectName>.flow.pending-publish.json <<EOF
{
  "publishId": "<PUBLISH_ID>",
  "elementKey": "<KEY>",
  "startedAt": "<ISO8601>",
  "shape": "<A|B|C>",
  "newActivities": [...],
  "renamedActivities": [...],
  "replacedActivities": [...]
}
EOF
```

### What the agent reports to the user

Single line per accepted elementKey:

```text
Shape A:
  Connector publish started (id: pub-abc123).
    New connector:   design-acmecorp-stripe
    Activities:      charges, customers, refunds
  Studio Web shows it in the picker ~5-10 min after the job completes.

Shape B:
  Connector update started (id: pub-def456).
    Extending:       design-acmecorp-stripe
    Added:           refunds, disputes
    Unchanged:       charges, customers
  Studio Web reflects the new activities ~5-10 min after the job completes.

Shape C (with rename):
  Connector update started (id: pub-ghi789).
    Extending:       design-acmecorp-stripe
    Added:           charges_v2 (kept the existing charges intact)
    Replaced:        — (none, per your selection)
    Skipped:         — (none)
```

Closing instruction the agent ALWAYS prints:

```text
Check publish status anytime:
  uip is connectors builder remote publish-status <PUBLISH_ID>

When you want to use this connector in a flow, create a connection first:
  uip is connections create <ELEMENT_KEY>
```

### Why the .flow stays untouched

The full swap (replacing `core.action.http.v2` with `uipath.connector.<key>.<action>`) requires:
1. `flow registry search` for the published connector key (cold registry → slow)
2. `is resources describe` per action to fetch the curated activity shape
3. Rewriting the flow JSON with a full `essentialConfiguration` / `optionalConfiguration` jsonstring envelope
4. Re-validating against the new node type
5. Waiting 5-10 min for backend registry propagation before any of it works

The vendor receives an identical HTTP request whether the node is `core.action.http.v2` or `uipath.connector.<key>.<action>`. The swap is **purely cosmetic** in Studio Web (named activity in the picker vs. generic HTTP Request box). The flow that the user just validated and shipped is paid for; mutating it for a cosmetic win introduces a regression surface for zero runtime benefit.

So: don't do it on the default path. The connector publish is a free side effect — the flow's existing HTTP nodes keep working as-is, and the connector becomes available for FUTURE flows in the tenant.

### Power-user escape hatch — explicit rebind

If a specific flow really should bind to the new connector (e.g. for shared use across multiple flows, or to get the connector's named activity in Studio Web), the user can opt in after the background publish completes:

```bash
uip maestro flow rewrite-http-to-connector <flow> \
  --target-connector <elementKey> \
  --connection-id <id> --folder-key <key> \
  --dry-run                              # preview first
```

Default leaves manual-mode nodes alone unless `--rebind-auth connector,manual` is passed. Writes `<flow>.bak` before mutating. This is the **quick swap** (keeps `core.action.http.v2`, just flips auth mode + `targetConnector`). The full swap (different node type) is not implemented — see "Why the .flow stays untouched" above for why it's not worth doing.

## Anti-patterns

- Do NOT call `uip is resources standardize` without `--from-spec` or `--from-sr`. There is no auto path. The cli will error and tell you so.
- Do NOT use IS curated slugs as the HTTP node `url`. IS slugs are object names (often identical to the `<object>` argument, e.g. `/create_issue` for object `create_issue`). They are NOT vendor endpoints. The HTTP node `url` must be the vendor's documented relative path — that's why you ran WebFetch in Step 1.
- Do NOT use absolute vendor URLs in the HTTP node `url`. In connector mode `url` is RELATIVE; the connection prepends the base URL.
- Do NOT skip reference resolution. SR's `fields[name].reference` says where to look — resolve to IDs before stuffing into the body.
- Do NOT default to manual mode + `uipath-uipath-http` when a catalog `uipath-{vendor}-{product}` connector exists — use **connector mode** with that connector key as `targetConnector` so auth + base URL are managed at runtime. Manual mode is the fallback only when no catalog connector covers the vendor.
- Do NOT author native catalog-connector nodes (`uipath.connector.<key>.<activity>`) for vendor calls just because they appear in `flow registry search` results. Per [SKILL.md Critical Rule #3 — POC override](../../../../../SKILL.md), default to `core.action.http.v2` (connector or manual mode) so the node is extractable by `flow extract-http-nodes`. Use a native catalog-connector node only when the user explicitly names the catalog connector by key.
- Do NOT author a node keyed on `uipath-uipath-http` (e.g. `uipath.connector.uipath-uipath-http.<anything>`). `uipath-uipath-http` is the generic HTTP proxy connector that backs every `core.action.http.v2` node — the proper authoring path is the node type itself, never a catalog-connector activity bound to this key. The POC override in SKILL.md filters this key out of registry-driven selection; if you see it surface anywhere, drop it on the floor.
- Do NOT use placeholder auth tokens (`<SLACK_BOT_TOKEN>`, `<JIRA_BASIC_AUTH_B64>`, `Bearer <TOKEN>`) in headers. If you find yourself typing those, you're in the wrong mode — switch to connector mode and bind a real connection.

### Concrete failure to avoid

A flow built from the prompt "create a flow to send a slack message and create a jira ticket using http-request" should NOT produce:

```jsonc
// WRONG — manual mode for vendors that have IS connectors
{ "detail": { "connector": "uipath-uipath-http", "connectionId": "ImplicitConnection",
  "bodyParameters": { "authentication": "manual",
    "url": "https://slack.com/api/chat.postMessage",
    "headers": { "Authorization": "Bearer <SLACK_BOT_TOKEN>" }, ... } } }
```

Correct: read vendor docs → build SR → cache via `standardize --from-sr` → author connector-mode HTTP node with `targetConnector: "uipath-salesforce-slack"`, real `connectionId`, RELATIVE `url: "/chat.postMessage"`.
