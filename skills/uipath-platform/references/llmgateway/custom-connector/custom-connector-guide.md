# BYO LLM Custom Connector

Bring a customer's own LLM endpoint to a UiPath product when no built-in connector speaks to it — an internal LLM gateway, a vendor behind custom auth, a model served in a format the product does not send. The LLM Gateway calls the connector through Integration Service at a **fixed path per API flavor**, the connector's hooks translate the request to the vendor and the answer back, and the product's compatibility probes decide whether the configuration may be saved.

```text
UiPath product ──(API flavor body)──▶ LLM Gateway ──▶ Integration Service
    /v3/element/instances/{connectionId}{flavor path}
        └─ your connector: preRequest hook → vendor endpoint → postRequest hook
```

Everything here runs through `uip`: `uip is connectors builder` (author on disk), `uip is connectors import` and `publish` (tenant), `uip is connections` (the runtime connection), `uip llm-configuration byo-connections` (probe + save).

<!--skill-flavor:draft-intro:start-->
The one exception is the unpublished draft: `curl` creates its test connection and calls the connector through it, on the Integration Service API, with the token from `uip login refresh`. The draft is tested that way and stays unpublished until those calls pass; the product's probes run once, on the published connector's runtime connection, when the configuration is saved.
<!--skill-flavor:draft-intro:end-->

<!--skill-flavor:host-availability-extra:start-->

<!--skill-flavor:host-availability-extra:end-->

## When to Use This Guide

- A customer wants a UiPath product (Agents, Autopilot, a feature listed by `list-product-configs`) to use an LLM endpoint that no built-in BYO connector covers.
- Building, publishing, or fixing a custom connector whose BYO configuration fails validation (`isAvailable: false` / `isCompatible: false`).
- Porting an existing custom-connector zip or an AI Gateway template to a new vendor, or re-publishing one after a hook fix.
- Changing a connector that is already published — a hook fix, another host, a new field or flavor — while configurations run on it: [§"Change a published connector"](#change-a-published-connector).
- Testing a custom LLM connector before publishing it (the builder's test connection, called through Integration Service), then creating the runtime connection and registering the BYO configuration on it.

## Critical Rules

1. **The API flavor fixes the contract.** The product decides the flavor (`AllowedApiFlavors` in `list-product-configs`), and the flavor decides the exact resource path(s) the gateway calls and the body it sends. Expose exactly those paths — a connector at any other path returns 404 to the probe. Look the path up in [connector-contract-guide.md](connector-contract-guide.md); never guess it.
2. **Register with `--connector-type Custom`; the template comes from the connector's tags.** The gateway needs the connector template to route the call and to pick the strategy. The CLI reads it from the connection's connector tags, as the AI Trust Layer UI does, so put the flavor's tag in `element-metadata.json:tags` (same guide): an `aigateway-*` tag, on a connector built from scratch or from an AI Gateway template, becomes `CustomAiGateway`. Integration Service reports those tags only for a connection on the published connector, so the configuration is saved on the runtime connection (step 9), never on the test connection. If `uip llm-configuration byo-connections create --help` does not say the template is read from the connection's connector tags, run `uip update` and check again; if it still does not, this CLI release cannot register a Custom connector: build, test and publish the connector, then stop before saving the configuration in step 9 and tell the user.
3. **Scaffold with `builder init`; use templates and zips only as reference.** `init` derives the tenant key `design-{org}-{slug}` from your login. A template or an old zip carries someone else's key (every AI Gateway template is `design-entity-customaigatewaybyomtemplate`), and importing it updates whichever connector already owns that key. Copy resources, config entries and hook bodies from the reference into the fresh scaffold — see [connector-contract-guide.md](connector-contract-guide.md) §"Porting from a template or zip".
4. **Streaming responses bypass the postRequest hook.** On a streaming call Integration Service runs only the preRequest hook and relays the vendor's bytes raw. A connector can reshape a streamed *request*, never a streamed *response*: when the vendor's stream format differs from the flavor's, tell the user streaming will not work for that product, and choose a flavor the vendor streams natively if one is allowed.
5. **Credentials enter only through the connection form.** API keys, client secrets and tokens are typed by the user into the Integration Service connection page (`AuthUrl`). Never put one in a hook, an `element.json` default, a CLI argument, a file, or the chat. Never send a credential in a query string or path (`vendorType: "query"`/`"path"`, or in `request_vendor_path`) — full request URLs are recorded in telemetry. Headers or the token request's body only (form-encoded or JSON, whichever the token service takes). The same goes for the UiPath access token the step 6 helper reads: it reaches `curl` on stdin only — never print it or `$S`, and never put it in a command line, a file or a URL.
6. **Hooks never log or echo content.** No `console.log`, no prompt, completion, header or token in an error message, `response_error_message`, or `connection_identity`. Return the vendor's error status and a fixed message instead.
7. **Log in and check the session before any tenant step.** `uip login status --output json` → `Data.Status` must be `"Logged in"` (the envelope says `Success` even when the session expired). If it is not, ask the user to run `uip login`; until then build offline only, and never guess a tenant, folder or connection id. The user needs the **OrganizationAdmin** role for AI Trust Layer to probe or save a configuration.
8. **Test the unpublished draft through Integration Service; publish once those calls pass.** The test connection (step 6) is the Connector Builder's Add connection button, called over the API: it connects the imported design connector, and that connection runs whatever was last imported — a fix is one `import` away, with no version bump and no publish. Step 7 sends the flavor's requests to it at the path the gateway calls. It belongs to the draft: `uip is connections` never lists it, only its creator sees it, and the gateway cannot probe it (Rule 2). The runtime connection is made on the **published** `custom-…` key (`PublishedKey` from `publish`) in the shared folder — with the Connections API call in [connections-guide.md](connections-guide.md) §"Create the runtime connection", which takes the folder, its page opened in the user's browser (or from the Integration Service web UI); `uip is connections create` cannot pick one.
9. **Every publish needs a higher version.** Bump `element-metadata.json:latestVersion` (or `publish --version`) before each `publish`; the server rejects an equal version. While testing, only re-import.
10. **Probing saves a configuration.** `byo-connections create` and `update` run the product probes and save only when every model passes; there is no dry run. Create with `--enabled`: the probes gate the save, so a configuration that fails is never saved, and one that passes serves the product at once — on a production tenant, say so before saving, and use `--no-enabled` only when the user asks to keep it off. Ask the user before deleting a configuration (`byo-connections delete --force`) or a runtime connection (`uip is connections delete --yes`). The draft's test connection is kept once the work is done: do not delete it, and do not ask whether to (step 9).
11. **Stop after three failed attempts on the same failure.** Read the failure (the step 7 answer, or the probe's reason in step 9), change one thing, re-import, try again. After three attempts on one failure, stop and show the user the answer or the probe summary and the hook — do not keep guessing.
12. **Git Bash on Windows: disable path conversion for `uip` only.** `export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'` before any builder, `import` or `publish` command, or `/v1/chat/completions` is rewritten to a Windows path that validates, publishes, and then 404s. With conversion off, pass file paths relative or as `C:/…`: a `/c/…` path reaches the CLI as `C:\c\…`. The same holds for the native Windows `jq` and `curl`, which cannot open an unconverted `/c/…` path: `run-probes.sh` stops with "a probe file is not valid JSON", and `curl --data-binary @/c/…` with "error encountered when reading a file". Run `run-probes.sh` and the `curl` calls in a shell without those variables, or give them relative paths.
13. **A custom token exchange has fixed lifecycle resources.** Integration Service calls `GET /onProvision` when a connection is created and `POST /onRefresh` on the first call after the token's lifetime has elapsed. The builder writes `vendorMethod: "GET"` on the first and `/on-refresh` for the second, so neither runs until patched. A `provisionAuthValidation` resource runs before `onProvision` — with no token yet — and fails every connection. Recipe: [hook-authoring-guide.md](hook-authoring-guide.md) §"Custom token exchange". An exchange that takes several calls (Apple's OIDC sign-in: authenticate, then trade the JWT for a token) is chained, not coded with `axios`: `onProvision` and `onRefresh` name a step resource in `nextResource`, whose hooks read `request_previous_response` — §"Chained token exchange" in the same guide.

## Workflow

Use placeholders for every tenant value. Pass `--output json` whenever you read the result. The first call of the day to a `uip` tool can print `Checking today's update for '<tool>'.` on stdout ahead of the JSON: parse from the first `{`.

### 0. Preflight — which products, and is a custom connector allowed there?

```bash
uip login status --output json                 # Data.Status == "Logged in"
```

Ask the customer which UiPath products the connector is for, and which features of each — for example Agents' design and evaluation, or ECS search. Ask even when the request already names one: ask whether other products or features will use the connector too, before you choose a flavor. Do not take the named one as the whole scope: each product feature is a configuration of its own, and the probes that decide whether it can be saved are that product's and that feature's (step 1), so a connector that passes for one can fail for another. When they cannot name them, list every product and feature this tenant offers and let them choose:

```bash
uip llm-configuration byo-connections list-product-configs --output json    # one row per Product + Feature
```

Then, for each feature they chose:

```bash
uip llm-configuration byo-connections list-product-configs \
  --product <PRODUCT> --feature <FEATURE> --output json
```

From the row read (the CLI returns these keys PascalCase): `ModelsConfigurationOption` (multi-mapping needed for `AllModels`/`AnyModel`), each entry of `Models` with its `AllowedApiFlavors` and `AllowedConnectors`, and `AddYourOwn`. `Custom` must appear in `AllowedConnectors` (or as a key of `AddYourOwn` for a customer-added model). If it does not, custom connectors are not enabled for this organization or feature — stop and tell the user; do not build a connector the gateway will refuse. With several features, build for the API flavors they share, and run steps 1, 7 and 9 once per feature: its own probes, its own configuration.

Then ask, per feature, how the vendor's model should appear in the product — the same choice [byo-connections.md](../byo-connections.md) offers for a built-in connector. Ask it even when the request names a model:

- **Replace a catalog model.** The product keeps asking for a model in `Models` (`--llm-name`), and the vendor's model answers in its place (`--llm-identifier`). Offer the catalog models whose `AllowedConnectors` include `Custom`.
- **Add a custom alias.** Only on an `AnyModelWithOwnAdditions` feature, and always offered there: the user picks a name of their own that is not in `Models`, and it appears in the product beside the catalog models. Its flavors are the ones `AddYourOwn.Custom` lists, it goes to `--llm-name` as-is (step 9), and the gateway runs the default and code-built probes for it plus the ones the feature itself lists (step 1).

The gateway allows one configuration per product, feature and model — and on a feature whose `ModelsConfigurationOption` is `AllModels`, one per product and feature, whatever the model: a configuration there for another model, on another connector, already takes the place. It refuses a second one at the very end, after the connector is built and published. So check now, before building, whether the place is taken:

```bash
uip llm-configuration byo-connections list --include-connection-details --output json   # Product, OperationGroupName, FolderId, LlmConfigurations[].DesiredModel
```

Look in every folder, not only the one the product will use: the limit is per folder only where the organization has folder-level granularity for BYO configurations, and tenant-wide everywhere else. When one exists for that product and feature (`AllModels`), or for that product, feature and model (the other options), tell the user and let them choose: move the existing configuration to the new connector's connection (`update <CONFIG_ID>` in step 9, which can rename it too — on an `AllModels` feature this replaces what the existing one served, so say which model and connection it gives up), or, where the feature allows it, add the model as a custom alias instead. Another shared folder is a choice only with folder-level granularity; when you cannot tell, do not create a folder to try it — a `create` refused there too leaves an empty folder behind.

### 1. Agree the contract with the user

Ask for (unless already given): the vendor base URL; how it authenticates (API key header, bearer token, OAuth2 client credentials, AWS SigV4, custom token exchange); its request and response format, or one sample of each; whether the product's calls stream; the model identifier the vendor expects (becomes `--llm-identifier`). Pick the flavor from the model's `AllowedApiFlavors` that is closest to the vendor's own format — the closer it is, the less the hooks translate. Then read the flavor's resource paths, tag and template in [connector-contract-guide.md](connector-contract-guide.md).

Check the vendor can do what the product's probes ask before building. Every configuration gets the gateway's default probe for its flavor, or the probe the gateway's code builds for that product in its place (Agents and UIA have one). On top of those, a product's Model Hub configuration can list its own probes for a feature. Those are opt in: ask the user, or the product team, which `ProbeId`s the feature lists, and name each with `--probe` (none named: the default and code-built probes only).

<!--skill-flavor:probe-list:start-->
List what will run, offline (`<GUIDE_DIR>` is the folder holding this guide: `references/llmgateway/custom-connector/` in the uipath-platform skill):

```bash
bash <GUIDE_DIR>/scripts/run-probes.sh --product <PRODUCT> --feature <FEATURE> --flavor <API_FLAVOR> \
  --llm-name <CATALOG_MODEL> [--probe <PROBE_ID>]... --list
```

Each line names a file under `<GUIDE_DIR>/assets/probes/` holding the request body and what the answer must show ([probes-guide.md](probes-guide.md)).
<!--skill-flavor:probe-list:end-->

Agents forces a tool call (a required `tool_choice`, `parallel_tool_calls: false`); the probes a product lists can send images, several choices (`n`) or web-search grounding. Autopilot's round-trip probes (`autopilot_*_stream_roundtrip_probe`, one per flavor) stream both ways: the vendor must stream tool calls in the flavor's own event format, then answer from the tool results sent back. A connector cannot reshape a stream (Rule 4), so a vendor whose stream is not the flavor's cannot pass them. A vendor without the feature cannot pass, however the hooks are written — tell the user and agree whether to go on.

### 2. Scaffold the connector

A connector that already exists is never scaffolded again: start from its source, as [§"Change a published connector"](#change-a-published-connector) says.

```bash
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'      # Git Bash only
mkdir <WORK_DIR> && cd <WORK_DIR>                      # fresh, empty directory
uip is connectors builder init --name '<CONNECTOR_NAME>' \
  --description '<ONE_LINE_DESCRIPTION>' --categories 'Generative AI' \
  --base-url <VENDOR_BASE_URL> \
  --auth customApiKey --api-key-param-name Authorization --api-key-prefix 'Bearer ' \
  --output json
uip is connectors builder activity create --name chat_completions \
  --display-name 'Chat completions' \
  --resource-path /v1/chat/completions --vendor-path <VENDOR_PATH> \
  --methods POST --no-curate --output json
```

`init` takes the organization for the key from your login; offline, pass `--organization <org-slug>`. It writes the credential's config entry (`custom.api.key` for `customApiKey`) without a `hintText`: query the entry, add one, and patch the whole entry back (`state query` / `state patch element.json/configuration/custom.api.key`). Repeat `activity create` once per path the flavor needs (the streaming twin too, for Gemini and Bedrock). Choose `--auth` from [connector-contract-guide.md](connector-contract-guide.md) §"Authentication"; a vendor that exchanges credentials for a token (`--auth custom`) also needs the lifecycle resources in [hook-authoring-guide.md](hook-authoring-guide.md) §"Custom token exchange", patched as Rule 13 says. Then set the template tag: query the whole `element-metadata.json`, change `tags`, patch the whole object back:

```bash
uip is connectors builder state query element-metadata.json --output json > <WORK_DIR>/meta-query.json
# write Data.Value from meta-query.json to meta.json with "tags": "custom, <FLAVOR_TAG>"
uip is connectors builder state patch element-metadata.json --value-file meta.json --output json
```

### 3. Write the hooks

Write one `.js` per resource + phase, then register it — the builder derives `contextParams` from the code:

```bash
uip is connectors builder activity hook create --resource-name chat_completions \
  --method POST --hook-type preRequest --custom-code-file <HOOKS_DIR>/chat-pre.js --output json
uip is connectors builder activity hook create --resource-name chat_completions \
  --method POST --hook-type postRequest --custom-code-file <HOOKS_DIR>/chat-post.js --output json
```

If the vendor already speaks the flavor's format, the hooks only fix auth, URL and model — keep them that small. Otherwise translate with [format-mapping-guide.md](format-mapping-guide.md). Runtime rules, variables and recipes: [hook-authoring-guide.md](hook-authoring-guide.md). Where a full Node.js runtime is available, check every hook with `node --check <file>` and the offline harness in the hook guide before registering it; where it is not, the calls in step 7 are the test.

### 4. Validate and zip

```bash
uip is connectors builder validate --output json
```

0 errors is required. For a BYO connector, exactly these warnings are expected and acceptable — say so in the summary: a fieldless activity on each flavor resource (the gateway sends a raw body, there is no Studio activity to type); on a path such as `/model/{modelId}/converse`, a path variable with no vendor slot when the hook moves the model into the body or URL; and a missing `provisionAuthValidation` resource when the vendor has no cheap authenticated `GET` to check the key with, or when the connector exchanges credentials for a token at connect time (Rule 13). Fix every other warning. Then run the BYO checks in [connector-contract-guide.md](connector-contract-guide.md) §"Pre-publish checklist".

When the user also wants the archive (to upload in the portal, or to hand over), zip the connector folder so it is the only top-level entry and holds `app/element/**` — the same layout `import` builds:

```bash
cd <WORK_DIR>
zip -r <CONNECTOR_DIR>.zip <CONNECTOR_DIR>/app/element -x '*.DS_Store'                          # macOS / Linux
tar -a -c -f <CONNECTOR_DIR>.zip <CONNECTOR_DIR>/app/element                                     # Windows 10+
```

### 5. Import

```bash
uip is connectors import --connector-dir <CONNECTOR_DIR> --output json           # create-or-update by key
```

The `builder` commands find the connector from `<WORK_DIR>`; `import` and `publish` look only at the current directory and above, so pass `--connector-dir` (the `RepoName` folder `init` printed). Note `Data.Id` — the `<CONNECTOR_ID>` step 6 needs. Do not publish yet: the draft is tested first.

### 6. Create the test connection on the draft

The user connects twice, so say which connection this is before asking for it: this first one is only for testing the unpublished draft, a sandbox key is enough for it, and no product ever uses it. The connection the product runs on comes second, after publishing (step 9), and that one takes the credentials production must use.

<!--skill-flavor:draft-test-connection:start-->
This is the Connector Builder's **Add connection**, called with `curl` (it needs `curl`, `jq` and `node`). Shell variables do not survive between commands, so write a helper once, outside the connector folder, and source it in every call. It reads a fresh token from `uip login refresh` and hands it to `curl` on stdin, so the token never reaches a command line, a file or the output:

```bash
cat > <WORK_DIR>/is-api.sh <<'EOF'
# Sourced before each call. It holds no token; $S does, so never print $S.
S=$(uip login refresh --login-validity 15 --output json) && jq -e '.Data.AccessToken' <<<"$S" >/dev/null ||
  { echo 'Not logged in: ask the user to run uip login.' >&2; return 1; }
T=$(jq -r '.Data | "\(.BaseUrl)/\(.OrganizationId)/\(.TenantName)"' <<<"$S")
NI="$T/elements_/v1/elements/normalized-instances"
api() {
  local out
  out=$(jq -r '"header = \"Authorization: Bearer \(.Data.AccessToken)\""' <<<"$S" |
    curl -sS --fail-with-body -K - -H 'Accept: application/json' -H 'Content-Type: application/json' \
      -H 'x-uipath-source: UiPath.IntegrationService.ConnectorBuilder' "$@") || { printf '%s\n' "$out" >&2; return 1; }
  printf '%s\n' "$out"
}
EOF
```

Open a connection session on the draft, in your Personal workspace, with a connection id you choose — without one the connection is created with an empty id no configuration can use. Each line ends in `&&`, so the first failed call stops the block; do not rely on `set -e`, which many agent shells ignore:

```bash
( set -o pipefail; source <WORK_DIR>/is-api.sh &&
  CONNECTOR=$(api "$T/elements_/v3/element/connectors/<CONNECTOR_ID>" | jq -c '{key, elementId: .sobaId}') &&
  FOLDER=$(api "$T/orchestrator_/odata/PersonalWorkspaces/UiPath.Server.Configuration.OData.GetPersonalWorkspace" |
    jq -c '{key: .Key, name: .Name, path: .Name, folderType: "Personal", personalWorkspace: true}') &&
  CONNECTION_ID=$(node -e 'console.log(crypto.randomUUID())') &&
  SESSION=$(api "$NI/applications/default/sessions" --data-raw "$(jq -nc --argjson c "$CONNECTOR" --argjson f "$FOLDER" \
    --arg id "$CONNECTION_ID" '{elementKey: $c.key, elementVersion: "Design", debug: true, usePreAuth: true,
                                instanceId: "", connectionId: $id, folder: $f}')") &&
  ASKS_NOTHING=$(api "$NI/applications/sessions/$(jq -r .sessionID <<<"$SESSION")" | jq '.elementMetadata
    | .authentication.type == "none" and all(.configuration[]?; (.configScreenType // "") | startswith("pre") | not)') &&
  jq --argjson c "$CONNECTOR" --arg id "$CONNECTION_ID" --argjson asksNothing "$ASKS_NOTHING" \
    '{elementId: $c.elementId, connectionId: $id, sessionId: .sessionID, authUrl: .redirectUrl, expiresAt: .expiration, asksNothing: $asksNothing}' <<<"$SESSION"
)
```

- `asksNothing: true` — the connector has no authentication and no connection field, so finish the session yourself, as the page's Connect button would:

```bash
( set -o pipefail; source <WORK_DIR>/is-api.sh &&
  DETAILS=$(api "$NI/applications/sessions/<SESSION_ID>") &&
  api "$NI/authenticate" -H "x-uipath-folderkey: $(jq -r .headers.folderKey <<<"$DETAILS")" -H 'x-uipath-foldertype: Personal' \
    --data-raw "$(jq -c --arg name '<CONNECTOR_NAME> test' '{element: {key: .elementMetadata.key, version: .elementVersion},
      sessionID, tags: .elementInstanceTags, configuration: (.configs // {}), name: $name}' <<<"$DETAILS")" |
    jq '.elementInstance | {connectionId, instanceId: .id, name}'
)
```

- `asksNothing: false` — open `authUrl` for the user straight away, in their own browser, where they are already signed in to UiPath: `open '<AUTH_URL>'` on macOS, `xdg-open '<AUTH_URL>'` on Linux, `Start-Process '<AUTH_URL>'` on Windows (from Git Bash: `powershell.exe -NoProfile -Command "Start-Process '<AUTH_URL>'"`). Open it only when it starts with the `BaseUrl` you are logged in to, and never in a browser you drive yourself, which is not signed in. Tell the user the page is open, that it is the test connection for the draft, and that it expires at `expiresAt` (about 12 minutes after the session opens), and ask them to enter the vendor credentials (a sandbox key is fine) and say when it is done. Hand them the link instead only when no browser opens from this shell (a remote or headless session). Never fill in the form or complete this session yourself.

Either way `connectionId` is the test connection (the connection step 7 calls), and `elementId` addresses the draft's connections. Confirm it exists — a `404` "No element instances found" means none does yet:

```bash
( set -o pipefail; source <WORK_DIR>/is-api.sh &&
  api "$T/elements_/elements/api-v2/elements/<ELEMENT_ID>/instances" | jq 'map({connectionId, instanceId: .id, name, createdDate})'
)
```

The connection belongs to the draft, so `uip is connections list` and `ping` do not see it; the step 7 calls are its test. Errors, delete and credential changes: [connections-guide.md](connections-guide.md).
<!--skill-flavor:draft-test-connection:end-->

### 7. Call the draft through Integration Service

<!--skill-flavor:draft-calls:start-->
Send the product's probe requests to the test connection, the way the gateway sends them when the configuration is saved: the same bodies, at the flavor's resource path (`POST …/v3/element/instances/{connectionId}{flavor path}`), with the model the vendor expects in the body or the path, and the same checks on each answer. `run-probes.sh` does it with the step 6 helper, so the token stays in `api`:

```bash
bash <GUIDE_DIR>/scripts/run-probes.sh --product <PRODUCT> --feature <FEATURE> --flavor <API_FLAVOR> \
  --llm-name <CATALOG_MODEL> [--probe <PROBE_ID>]... --model <VENDOR_MODEL_ID> \
  --connection <TEST_CONNECTION_ID> --helper <WORK_DIR>/is-api.sh --out <WORK_DIR>/probes
```

Each probe prints `PASS`, `INCOMPATIBLE <reason>` (the reason the gateway would give, and what the check wants), `UNAVAILABLE` with the HTTP status and the start of the answer, or `RETRY` when the gateway would send it once more with an edited body. Every request and answer is kept in `<WORK_DIR>/probes/` (`<name>.request.json`, `<name>.response.json`). Exit 0 means every probe passed; 1, that one failed; 2, that none was sent: a usage error, a flavor no probe has, or no probe for that product, feature and flavor. Which files run, their format and how to add one: [probes-guide.md](probes-guide.md).

A probe marked `"roundTrip": true` (Autopilot's `autopilot_*_stream_roundtrip_probe`s) is two streamed calls with ids and codes drawn for the run: the runner sends both, reassembles each stream as the gateway does, and keeps each turn's request and raw stream (`<name>.turn1.request.json`, `<name>.turn1.stream.txt`, and the same for `turn2`). A stub or a canned answer fails it by design, so run it against the vendor's real model.

No other probe streams. If the product streams and no round-trip probe ran, also send one streamed request with the header the gateway sends with a stream: for chat completions, Responses and Messages, a probe's request with `"stream": true` at the same path; for Gemini and Bedrock, the same body at the flavor's stream path ([connector-contract-guide.md](connector-contract-guide.md), `?alt=sse` for Gemini). It passes when the events arrive in the flavor's own stream format. On the draft, Integration Service may append one line that is not an event (`{"message":"Published Connector not found with key design-…"}`) after the vendor's last one; ignore it:

```bash
( set -o pipefail; source <WORK_DIR>/is-api.sh &&
  jq '. + {stream: true}' <WORK_DIR>/probes/<PROBE_NAME>.request.json >"<WORK_DIR>/probes/stream.request.json" &&
  api -N "$T/elements_/v3/element/instances/<TEST_CONNECTION_ID><FLAVOR_STREAM_PATH>" -H 'Accept: text/event-stream' \
    --data-binary @<WORK_DIR>/probes/stream.request.json
)
```

A connector whose hook refuses streams ([hook-authoring-guide.md](hook-authoring-guide.md) §"Streaming") answers this call with that same message alone, as a `404`: it is Integration Service's answer to the refusal, not a missing resource. Repeat the call with `Accept: application/json` to see the hook's own refusal.
<!--skill-flavor:draft-calls:end-->

When a probe fails, read its answer, fix the hook or the config entry it points at, `builder validate`, `import` (the test connection runs the new import at once) and run the probes again. Integration Service answers two failures itself, both `404`: "No API found at that URL for the given token and credentials" (no resource at that path, Rule 1) and "Invalid Element Instance Id provided." (the test connection is gone). Every other answer comes from the vendor through your hooks. A vendor error keeps the vendor's status, but its body reaches you inside Integration Service's own envelope, flattened into `providerMessage` (`error - {message=…}`): read the vendor's reason there.

### 8. Publish

Only once every probe passes on the test connection (and the streamed call, if the product streams):

```bash
uip is connectors publish --connector-dir <CONNECTOR_DIR> --wait --output json   # Data.Status == "SUCCESS"; note Data.PublishedKey
```

A `FAILURE` status or a non-zero exit stops the workflow: read the message, fix, bump `latestVersion`, re-import, re-publish.

### 9. Runtime connection and the configuration

<!--skill-flavor:runtime-connection:start-->
The test connection usually holds the builder's own or a sandbox key. Ask the user which credentials production uses, then open the runtime connection's page for them: start the session on the published connector (`<PUBLISHED_KEY>`) in the shared folder the product will use with the Connections API call in [connections-guide.md](connections-guide.md) §"Create the runtime connection" (`uip is connections create` cannot pick a folder), and open its `authUrl` in their browser as in step 6. If the connection lands in the Personal workspace, have them create it from Integration Service in the web UI instead. Find its id:
<!--skill-flavor:runtime-connection:end-->

```bash
uip is connections list <PUBLISHED_KEY> --all-folders --refresh --output json    # Id, State, FolderKey
```

Save the configuration on it. This runs the product's compatibility probes through the gateway, on the published version:

```bash
uip llm-configuration byo-connections create --product <PRODUCT> --feature <FEATURE> \
  --folder-key <SHARED_FOLDER_KEY> --name '<CONFIG_NAME>' --enabled \
  --connector-type Custom --connection-id <RUNTIME_CONNECTION_ID> --api-flavor <API_FLAVOR> \
  --llm-name <CATALOG_MODEL> --llm-identifier <VENDOR_MODEL_ID> --output json
```

Use repeated `--mapping '…,connector-type=Custom'` for `AllModels` / `AnyModel` features. The CLI first reads the connector template from the connection's connector tags and stops, before any probe, on a connection Integration Service does not list or a connector whose tags name no template. Exit 0 with every model `IsAvailable: true` and `IsCompatible: true` is a pass: the CLI answers in PascalCase, the verdict under `Data.Validation` keyed by the model name PascalCased (`gemini-3.8-flash` → `Gemini3.8Flash`), and the saved configuration's id at `Data.Configuration.Id` — the `<CONFIG_ID>` for `update` and `get`. Otherwise read `unavailabilityReason` / `incompatibilityReason` / `vendorRawResponse` per [probes-guide.md](probes-guide.md). To fix:
- reproduce it with step 7 on the test connection, which sends the same requests;
- fix the hook and re-import until that probe passes;
- bump `latestVersion`, then `import` and `publish --wait`;
- run the probes again: `create` again (a failed one saved nothing) or `update <CONFIG_ID>` with the same mapping.

A configuration saved with `--no-enabled` at the user's request is switched on later with `update <CONFIG_ID>`, the same mapping and `--enabled` (it runs the probes again). Finish with `byo-connections get <CONFIG_ID> --force-refresh --output json`. Keep the draft's test connection, without asking the user about it: it costs nothing, no product can reach it, and the next fix is tested on it. Delete it only when the user asks ([connections-guide.md](connections-guide.md) §"Delete").

When `create` answers that there is already a configuration for this product, feature and model in the folder — or, on an `AllModels` feature, "there is already a configuration for this product and operation group under the same folder" — nothing was saved and the probes did not run: it is step 0's check, met late. "The same folder" means the tenant where folder-level granularity is off, so the same answer for a different folder is that case, not a wrong key. Ask the user as step 0 says; to move the existing configuration over, `update <CONFIG_ID>` with this mapping and, to rename it, `--name`.

When the save is refused with a model "not available" (`VendorInvalidRequest`, or a provisioning failure) on a connection that passed before, read `vendorRawResponse` before touching a hook: a URL named there as not reachable or invalid is the connection's own host or token-service URL no longer answering — the token refresh failed, and no request reached the model. Check that each URL the connection holds answers from the internet (a temporary tunnel or sandbox host may be gone), have the user point the connection at one that does (`uip is connections edit`, as in §"Change a published connector" step 6), and save again. The connector needs no change and no new version.

### 10. Report to the user

The reader is usually the customer's administrator, not a UiPath engineer. Write for them: short, plain language, in the product's terms. Leave out what only matters while building: resource paths, hook variables, probe reason codes, `IsModelNameSimilar`, Integration Service envelopes, CLI output. Keep the ids (connector key, connection and configuration ids) out of the report too, and give them when the user asks, for example for a support ticket.

1. **The outcome, in one sentence**: the product and feature, the model the product asks for and the vendor model that answers it, and whether the configuration is enabled.
2. **A short status table**: the connector (name, version, published), the connection (name, folder), the configuration (name, checks passed, enabled or not).
3. **What works and what does not**: what the checks covered (text answers, tool calls, images), then each limitation once, with what to do instead — a stream the connector cannot serve, request options it refuses (structured output, several choices, built-in tools such as search grounding), settings it ignores.
4. **The next step**, when one is left: for example, editing the connection to the production host and credentials, or enabling a configuration the user asked to keep off.
5. **End with the link to the configuration in AI Trust Layer** — one per configuration when the connector serves several features — and open it for the user where you can, as in step 6:

```text
<BaseUrl>/<Organization>/portal_/admin/ai-trust-layer/llm-configurations/<TenantId>/<FOLDER_ID>/edit/<CONFIG_ID>
```

<!--skill-flavor:config-link-values:start-->
`BaseUrl`, `Organization` and `TenantId` come from `uip login status --output json`.
<!--skill-flavor:config-link-values:end-->
`<FOLDER_ID>` is the shared folder's **numeric** id, not its key: `uip or folders get <SHARED_FOLDER_KEY> --output json` prints it as `Data.Id` (`uip or folders list` does not).

## Change a published connector

A connector that is published may already serve products. Change it from its own source, test the change on the draft, publish it, then bring every connection and configuration on it along. The commands are the workflow's; what differs is the order and what to check.

1. **Find what runs on it.** The published key is `Key` in `uip is connectors list --output json` (`Stage` `CUSTOM`); its connections are `uip is connections list <PUBLISHED_KEY> --all-folders --refresh --output json`; the configurations on them are the entries of `uip llm-configuration byo-connections list --include-connection-details --output json` whose `LlmConfigurations[].ConnectionId` is one of those. Every one of those connections runs a new version the moment it is published — nothing is re-created or re-authorized, and an enabled configuration serves it to its product at once — so tell the user which configurations the change reaches and which are enabled, and agree the change with them.
2. **Start from its source.** Download the draft into a fresh, empty directory:

   ```bash
   uip is connectors download <DESIGN_KEY> --connector-dir <WORK_DIR> --output json   # Data.ConnectorRoot is the <CONNECTOR_DIR>
   ```

   `<DESIGN_KEY>` is the published key with `custom-` replaced by `design-`. Never run `init` for a connector that exists: under the same name it derives the same key, and `import` replaces the draft, then the next publish the connector, with a rebuild that has lost every patch the connector carried (Rule 13's lifecycle resources among them); under another name it makes a second connector. The download is the draft as last imported, which can be ahead of what was published: when it differs from what you expect (a local copy from the build, or the user's account of the last change), ask before building on it. Copy the downloaded folder somewhere untouched before you change anything — it is the rollback (step 7 below).

   The download keeps the resources, lifecycle patches and configuration entries, with each hook's code inline in `element.json` (`resources[].hooks[].body`) instead of a file. It also writes a second copy of each resource, hooks included, into its `standard-resources/<name>.json` under `resources`, and `import` takes the hooks from that copy: left in place, every hook change is silently dropped — `import` answers `Updated`, and the draft keeps running the old code. After making the untouched copy, delete the `resources` key from every `standard-resources/*.json` of the one you will change: `state query standard-resources/<name>`, drop `resources` from `Data.Value`, and `state patch standard-resources/<name> --value-file <file>` with the rest. Two more things do not survive the download, and `builder validate` fails until both are back:
   - `element-metadata.json:latestVersion` is gone. Set it above the published version, which is `Data[0].Version` in `uip is connectors metadata <PUBLISHED_KEY> --output json` (`connectors get` does not show it): query the whole file, add the field, patch it back as in step 2 of the workflow.
   - Each header parameter of `type: "value"` has lost `source: "request"` ("missing required field 'source'"). Query `element.json/parameters`, add `"source": "request"` to each such entry, and patch the array back.

   `validate` then also warns "publishStatus not set"; that one is expected on a download.
3. **Change it** with the builder commands of steps 2–4 run against `--connector-dir <CONNECTOR_DIR>`, then `builder validate` and the pre-publish checklist. To change a hook, save its body to a `.js` file, edit that, and register it again with `activity hook create` (same resource, method and hook type): the builder replaces the inline code with the file.
4. **Test the draft.** `import` changes only the draft; the runtime connections keep running the published version. Check first that the import carried the change: download the draft again into another empty directory and look for it in `element.json` — an answer that still comes from the old code means a `standard-resources` copy was left in (step 2). Then run the probes of every configuration from step 1 (steps 1 and 7 of the workflow, once per feature), and the streamed call if the product streams, on a test connection. Create a new one (step 6) when the old one is gone or the change touches what its page asked for — the host, a field, the auth type: a test connection's fields cannot be edited.
5. **Publish** with `import` and `publish --wait` (step 8 of the workflow), once `latestVersion` (set in step 2 above) is still higher than `Data[0].Version` in `uip is connectors metadata <PUBLISHED_KEY>`.
6. **Bring each connection and configuration along.**
   - A runtime connection keeps the field values and the auth it was made with. When the change adds a field the page asks for, changes the host a field holds, or changes the auth type, open each connection's page for the user: `uip is connections edit <CONNECTION_ID> --no-wait --output json` returns its `AuthUrl`, opened as in step 6; never fill it in yourself. The edit page shows the connection's own values, not the connector's new defaults: tell the user which fields to change and to what, every one of them — a token call reads its own URL field, so changing only the base URL still fails with "Failed to execute API … during provisioning" naming the old host.
   - Before saving anything on an existing connection, check it still reaches the vendor: one probe from step 7 of the workflow on the runtime connection. A connection whose host or token-service URL stopped answering fails every save with the model "not available", whatever the connector does (step 9 of the workflow).
   - Probe every configuration from step 1 again. `update` replaces all of a configuration's mappings, so rebuild them from `byo-connections get <CONFIG_ID> --output json`, one `--mapping` per entry of `Data.LlmConfigurations`: `llm-name=<DesiredModel>,llm-identifier=<CustomerModel>,connector-type=<ConnectorType>,api-flavor=<ApiFlavor>,connection-id=<ConnectionId>`, plus `--enabled` when `Data.Enabled` is true:

     ```bash
     uip llm-configuration byo-connections update <CONFIG_ID> \
       --mapping 'llm-name=<DesiredModel>,llm-identifier=<CustomerModel>,connector-type=Custom,api-flavor=<ApiFlavor>,connection-id=<ConnectionId>' \
       --enabled --output json
     ```

   - A failed `update` leaves the configuration as it was — still enabled, on a connector that now fails its probes. Roll back (step 7) first, then fix and repeat from step 3.
7. **Roll back** by publishing the untouched copy from step 2: give it step 2's two repairs, with `latestVersion` above the version now published, and leave its `standard-resources` copies in, since they hold the same old code. `import`, `publish --wait`; the connections run it as soon as it is published, as they ran the change. Then run step 6's `update` once more.

Report as in step 10: what changed, the version now published, and each configuration with whether its probes passed.

## Command Map

```text
uip login status                                         # session check (Data.Status)
uip llm-configuration byo-connections
  list-product-configs --product --feature               # allowed flavors / connectors / models
  create | update <id> | get <id> [--force-refresh] | list | delete <id> --force
uip is connectors builder                                # author on disk (see Workflow 2–4)
  init | activity create | activity hook create | auth set | auth system create
  state query <ptr> | state patch <ptr> --value-file | inspect | validate
uip is connectors import | publish --wait | publish-status <id> | get <key>       # import/publish: --connector-dir <dir>
uip is connectors download <design-key> --connector-dir <dir>                     # an existing connector's source (Change a published connector)
uip login refresh                                        # token for the curl calls (via <WORK_DIR>/is-api.sh)
curl … elements_/v1/elements/normalized-instances        # the draft's test connection (Workflow 6)
  POST applications/default/sessions | GET applications/sessions/<id> | POST authenticate
curl … elements_/elements/api-v2/elements/<element-id>/instances   # list | DELETE …/<instance-id>
bash <GUIDE_DIR>/scripts/run-probes.sh … [--probe <id>]… --list | --connection <id> --helper …  # default + code-built + named probes (Workflow 1, 7)
curl … elements_/v3/element/instances/<connection-id><flavor-path>  # what run-probes sends; a streamed call (Workflow 7)
curl … connections_/api/v1/Connections -H 'x-uipath-folderkey: <folder>'   # runtime connection session in a shared folder (Workflow 9)
uip is resources run create <key> '<flavor-path>' --connection-id <id> --body '<json>'   # one call to a connection, no shell needed
uip or folders get <folder-key>                          # the folder's numeric Id, for the configuration link (Workflow 10)
uip is connections list <custom-key> --all-folders | ping <id> | edit <id> --no-wait | delete <id> --yes
uip or folders list                                      # folder Type (Personal vs Standard)
```

## Reference Navigation

| Task → read this | Reference |
|---|---|
| Which path, tag, template and auth a flavor needs; porting a template or zip; the pre-publish checklist | [connector-contract-guide.md](connector-contract-guide.md) |
| Hook runtime, variables, URL/model rewrites, token exchange, streaming, error handling | [hook-authoring-guide.md](hook-authoring-guide.md) |
| Translating between OpenAI, Gemini, Anthropic and Bedrock bodies (messages, tools, usage, finish reasons, media) | [format-mapping-guide.md](format-mapping-guide.md) |
| The draft's test connection vs the runtime connection, folders, credential rotation | [connections-guide.md](connections-guide.md) |
| Which probes a product runs, the probe file format and adding one; reading a probe verdict and fixing each failure reason | [probes-guide.md](probes-guide.md) |

For general connector authoring depth (every auth type, `state patch` semantics, system resources), the `uipath-connector-builder` skill covers the builder; this guide carries everything a BYO LLM connector needs on its own.

## Anti-patterns

1. Importing a template or an old zip as-is — it carries a shared key and overwrites another connector (Rule 3).
2. Exposing the vendor's path (`/v2/generate`) as the resource path instead of the flavor's path — the gateway's call gets a 404 (Rule 1).
3. Saving the configuration on the test connection, or on a connector whose `element-metadata.json:tags` lacks the flavor's tag — the CLI cannot read the template and stops (Rule 2).
4. Translating a streamed response in a postRequest hook — it never runs on a stream (Rule 4).
5. Asking the user to paste an API key into the chat, or baking one into `element.json` as a default (Rule 5).
6. Publishing a version per fix to test it, instead of re-importing and calling the draft's test connection again; or leaving the runtime connection in a Personal workspace, where only its creator can manage it (Rule 8).
7. Re-publishing without bumping `latestVersion` (Rule 9).
8. Taking the one product the request names as the whole scope, without asking whether other products or features will use the connector — another feature can allow other flavors and run other probes (step 0). Likewise taking the model the request names as a replacement without asking whether it replaces a catalog model or is added as a custom alias, or building before checking that no configuration already takes that place — per model, or per feature on an `AllModels` one, and tenant-wide unless the organization has folder-level granularity.
9. Logging the prompt or the vendor response "to debug" from a hook (Rule 6).
10. Reporting done on "publish succeeded" without a passing probe on the runtime connection.
11. Keeping the builder's `onProvision` / `onRefresh` entries as written, or a `provisionAuthValidation` beside a token exchange — the token is never fetched and every connection fails with the vendor's 401 (Rule 13).
12. Reading the caller's request from `request_body_map` in a postRequest hook — there it is the vendor's body; the caller's is `request_body_raw`.
13. Running `init` again to change a connector that already exists, instead of downloading its source — the rebuild replaces the draft, and the next publish the connector, without the patches it carried (§"Change a published connector").
14. Publishing a change and probing only the configuration you came for — every configuration on the connector's connections runs the new version.
15. Importing a downloaded connector with the resource copies still in its `standard-resources` files — `import` answers `Updated` and the draft keeps the old hooks (§"Change a published connector" step 2).
