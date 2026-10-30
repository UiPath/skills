---
name: uipath-byo-llm-connector
description: "UiPath BYO LLM custom connector for the LLM Gateway / AI Trust Layer, end to end via the uip CLI: build an Integration Service connector that bridges what a UiPath product sends (OpenAI chat-completions/responses/embeddings, Gemini, Bedrock Invoke/Converse, Anthropic Messages) to a customer or in-house LLM endpoint with pre/post-request hooks, zip it, import + publish it, create the test connection, run the product's compatibility probes through `uip llm-configuration byo-connections`, fix and re-probe until they pass, then create the runtime connection and save the configuration. For generic IS connector authoring (non-LLM)→uipath-connector-builder; for a BYO config on a built-in vendor connector (OpenAI, Azure OpenAI, Bedrock, Vertex)→uipath-platform."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# BYO LLM Custom Connector

Bring a customer's own LLM endpoint to a UiPath product when no built-in connector speaks to it — an internal LLM gateway, a vendor behind custom auth, a model served in a format the product does not send. The LLM Gateway calls the connector through Integration Service at a **fixed path per API flavor**, the connector's hooks translate the request to the vendor and the answer back, and the product's compatibility probes decide whether the configuration may be saved.

```text
UiPath product ──(API flavor body)──▶ LLM Gateway ──▶ Integration Service
    /v3/element/instances/{connectionId}{flavor path}
        └─ your connector: preRequest hook → vendor endpoint → postRequest hook
```

Everything here runs through `uip`: `uip is connectors builder` (author on disk), `uip is connectors import` and `publish` (tenant), `uip is connections` (credentials), `uip llm-configuration byo-connections` (probe + save).

## When to Use This Skill

- A customer wants a UiPath product (Agents, Autopilot, a feature listed by `list-product-configs`) to use an LLM endpoint that no built-in BYO connector covers.
- Building, publishing, or fixing a custom connector whose BYO configuration fails validation (`isAvailable: false` / `isCompatible: false`).
- Porting an existing custom-connector zip or an AI Gateway template to a new vendor, or re-publishing one after a hook fix.
- Creating the test and runtime Integration Service connections for a custom LLM connector and registering the BYO configuration on them.

## Critical Rules

1. **The API flavor fixes the contract.** The product decides the flavor (`allowedApiFlavors` in `list-product-configs`), and the flavor decides the exact resource path(s) the gateway calls and the body it sends. Expose exactly those paths — a connector at any other path returns 404 to the probe. Look the path up in [references/connector-contract-guide.md](references/connector-contract-guide.md); never guess it.
2. **Register with `--connector-type Custom --connector-template <template>`.** The gateway reads the template to route the call and to pick the strategy; without it the probe fails before it reaches the connector. A connector built from scratch or from an AI Gateway template is `CustomAiGateway`. Also put the matching template tag in `element-metadata.json:tags` (same guide) so the AI Trust Layer UI lists the connector for that flavor. If the CLI rejects `--connector-template`, upgrade `uip` — older releases cannot register Custom connectors.
3. **Scaffold with `builder init`; use templates and zips only as reference.** `init` derives the tenant key `design-{org}-{slug}` from your login. A template or an old zip carries someone else's key (every AI Gateway template is `design-entity-customaigatewaybyomtemplate`), and importing it updates whichever connector already owns that key. Copy resources, config entries and hook bodies from the reference into the fresh scaffold — see [references/connector-contract-guide.md](references/connector-contract-guide.md) §"Porting from a template or zip".
4. **Streaming responses bypass the postRequest hook.** On a streaming call Integration Service runs only the preRequest hook and relays the vendor's bytes raw. A connector can reshape a streamed *request*, never a streamed *response*: when the vendor's stream format differs from the flavor's, tell the user streaming will not work for that product, and choose a flavor the vendor streams natively if one is allowed.
5. **Credentials enter only through the connection form.** API keys, client secrets and tokens are typed by the user into the Integration Service connection page (`AuthUrl`). Never put one in a hook, an `element.json` default, a CLI argument, a file, or the chat. Never send a credential in a query string or path (`vendorType: "query"`/`"path"`, or in `request_vendor_path`) — full request URLs are recorded in telemetry. Headers or a form-encoded token body only.
6. **Hooks never log or echo content.** No `console.log`, no prompt, completion, header or token in an error message, `response_error_message`, or `connection_identity`. Return the vendor's error status and a fixed message instead.
7. **Log in and check the session before any tenant step.** `uip login status --output json` → `Data.Status` must be `"Logged in"` (the envelope says `Success` even when the session expired). The user needs the **OrganizationAdmin** role for AI Trust Layer to probe or save a configuration.
8. **Connections use the published `custom-…` key, live in a shared folder.** `publish` returns `PublishedKey` (`design-` → `custom-`); `uip is connections create` with the `design-…` key fails. The gateway reads connections with its own service identity, which cannot see a **Personal** workspace folder — a connection there probes as unavailable. Check the connection's folder before probing (see [references/connections-guide.md](references/connections-guide.md)).
9. **Every re-publish needs a higher version.** Bump `element-metadata.json:latestVersion` (or `publish --version`) before each `publish`; the server rejects an equal version. A fix is live only after `import` + `publish --wait` returns `SUCCESS`.
10. **Probing saves a configuration.** `byo-connections create` and `update` run the product probes and save only when every model passes; there is no dry run. Probe with `--no-enabled` so a passing test configuration never serves traffic, and ask the user before deleting a configuration (`byo-connections delete --force`) or a connection (`uip is connections delete --yes`).
11. **Stop after three failed probes on the same reason.** Read the reason, change one thing, re-publish, re-probe. After three attempts on one reason, stop and show the user the probe summary and the hook — do not keep guessing.
12. **Git Bash on Windows: disable path conversion first.** `export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'` before any builder command, or `/v1/chat/completions` is rewritten to a Windows path that validates, publishes, and then 404s.

## Workflow

Use placeholders for every tenant value. Pass `--output json` whenever you read the result.

### 0. Preflight — is a custom connector allowed here?

```bash
uip login status --output json                 # Data.Status == "Logged in"
uip llm-configuration byo-connections list-product-configs \
  --product <PRODUCT> --feature <FEATURE> --output json
```

From the row read: `modelsConfigurationOption` (multi-mapping needed for `AllModels`/`AnyModel`), each model's `allowedApiFlavors` and `allowedConnectors`, and `addYourOwn`. `Custom` must appear in `allowedConnectors` (or as a key of `addYourOwn` for a customer-added model). If it does not, custom connectors are not enabled for this organization or feature — stop and tell the user; do not build a connector the gateway will refuse.

### 1. Agree the contract with the user

Ask for (unless already given): the vendor base URL; how it authenticates (API key header, bearer token, OAuth2 client credentials, AWS SigV4, custom token exchange); its request and response format, or one sample of each; whether the product's calls stream; the model identifier the vendor expects (becomes `--llm-identifier`). Pick the flavor from the model's `allowedApiFlavors` that is closest to the vendor's own format — the closer it is, the less the hooks translate. Then read the flavor's resource paths, tag and template in [references/connector-contract-guide.md](references/connector-contract-guide.md).

### 2. Scaffold the connector

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

Repeat `activity create` once per path the flavor needs (the streaming twin too, for Gemini and Bedrock). Choose `--auth` from [references/connector-contract-guide.md](references/connector-contract-guide.md) §"Authentication". Then set the template tag: query the whole `element-metadata.json`, change `tags`, patch the whole object back:

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

If the vendor already speaks the flavor's format, the hooks only fix auth, URL and model — keep them that small. Otherwise translate with [references/format-mapping-guide.md](references/format-mapping-guide.md). Runtime rules, variables and recipes: [references/hook-authoring-guide.md](references/hook-authoring-guide.md). Where a full Node.js runtime is available, check every hook with `node --check <file>` and the offline harness in the hook guide before registering it; where it is not, the probe in step 7 is the test.

### 4. Validate and zip

```bash
uip is connectors builder validate --output json
```

0 errors is required. For a BYO connector, exactly these warnings are expected and acceptable — say so in the summary: a fieldless activity on each flavor resource (the gateway sends a raw body, there is no Studio activity to type); on a path such as `/model/{modelId}/converse`, a path variable with no vendor slot when the hook moves the model into the body or URL; and a missing `provisionAuthValidation` resource when the vendor has no cheap authenticated `GET` to check the key with. Fix every other warning. Then run the BYO checks in [references/connector-contract-guide.md](references/connector-contract-guide.md) §"Pre-publish checklist".

When the user also wants the archive (to upload in the portal, or to hand over), zip the connector folder so it is the only top-level entry and holds `app/element/**` — the same layout `import` builds:

```bash
cd <WORK_DIR>
zip -r <CONNECTOR_DIR>.zip <CONNECTOR_DIR>/app/element -x '*.DS_Store'                          # macOS / Linux
tar -a -c -f <CONNECTOR_DIR>.zip <CONNECTOR_DIR>/app/element                                     # Windows 10+
```

### 5. Import and publish

```bash
uip is connectors import --output json                  # create-or-update by key
uip is connectors publish --wait --output json          # Data.Status == "SUCCESS"; note Data.PublishedKey
```

A `FAILURE` status or a non-zero exit stops the workflow: read the message, fix, bump `latestVersion`, re-import, re-publish.

### 6. Create the test connection

```bash
uip is connections create <PUBLISHED_KEY> --no-wait --output json      # Data.AuthUrl, Data.SessionId
```

Give the user `AuthUrl` and ask them to open it, enter the vendor credentials, and confirm when done. Then find the connection, confirm its state and folder, and ping it:

```bash
uip is connections list <PUBLISHED_KEY> --all-folders --refresh --output json
uip or folders list --output json                        # the connection's FolderKey must not be Type: Personal
uip is connections ping <CONNECTION_ID> --output json
```

Details, the Personal-folder trap, and credential rotation: [references/connections-guide.md](references/connections-guide.md).

### 7. Probe with the product's own probes

```bash
uip llm-configuration byo-connections create --product <PRODUCT> --feature <FEATURE> \
  --folder-key <SHARED_FOLDER_KEY> --name '<TEST_CONFIG_NAME>' --no-enabled \
  --connector-type Custom --connector-template CustomAiGateway \
  --connection-id <TEST_CONNECTION_ID> --api-flavor <API_FLAVOR> \
  --llm-name <CATALOG_MODEL> --llm-identifier <VENDOR_MODEL_ID> --output json
```

Use repeated `--mapping '…,connector-type=Custom,connector-template=CustomAiGateway'` for `AllModels` / `AnyModel` features. Exit 0 with every model `isAvailable: true` and `isCompatible: true` is a pass. Otherwise read `unavailabilityReason` / `incompatibilityReason` / `vendorRawResponse` and fix per [references/probes-guide.md](references/probes-guide.md). After a fix is published, re-probe the same configuration with `update <ID>` and the same mapping (or re-run `create` if the failed one was never saved).

### 8. Runtime connection and the real configuration

The test connection usually holds the builder's own or a sandbox key. Ask the user which credentials production uses, create the runtime connection the same way (step 6) in the shared folder the product will use, then point the configuration at it and enable it:

```bash
uip llm-configuration byo-connections update <CONFIG_ID> \
  --folder-key <SHARED_FOLDER_KEY> --name '<CONFIG_NAME>' --enabled \
  --connector-type Custom --connector-template CustomAiGateway \
  --connection-id <RUNTIME_CONNECTION_ID> --api-flavor <API_FLAVOR> \
  --llm-name <CATALOG_MODEL> --llm-identifier <VENDOR_MODEL_ID> --output json
```

`update` re-runs the probes against the runtime connection. Finish with `byo-connections get <CONFIG_ID> --force-refresh --output json`, and ask before deleting the test connection (`uip is connections delete <TEST_CONNECTION_ID> --yes`). Report: connector key + version, flavor, the connections (id, folder), the configuration id, the probe verdict, and any limitation (streaming, unsupported parameters).

## Command Map

```text
uip login status                                         # session check (Data.Status)
uip llm-configuration byo-connections
  list-product-configs --product --feature               # allowed flavors / connectors / models
  create | update <id> | get <id> [--force-refresh] | list | delete <id> --force
uip is connectors builder                                # author on disk (see Workflow 2–4)
  init | activity create | activity hook create | auth set | auth system create
  state query <ptr> | state patch <ptr> --value-file | inspect | validate
uip is connectors import | publish --wait | publish-status <id> | get <key>
uip is connections create <custom-key> --no-wait | list <key> --all-folders | ping <id> | edit <id> --no-wait | delete <id> --yes
uip or folders list                                      # folder Type (Personal vs Standard)
```

## Reference Navigation

| Task → read this | Reference |
|---|---|
| Which path, tag, template and auth a flavor needs; porting a template or zip; the pre-publish checklist | [references/connector-contract-guide.md](references/connector-contract-guide.md) |
| Hook runtime, variables, URL/model rewrites, token exchange, streaming, error handling | [references/hook-authoring-guide.md](references/hook-authoring-guide.md) |
| Translating between OpenAI, Gemini, Anthropic and Bedrock bodies (messages, tools, usage, finish reasons, media) | [references/format-mapping-guide.md](references/format-mapping-guide.md) |
| Test vs runtime connections, the Personal-folder trap, credential rotation | [references/connections-guide.md](references/connections-guide.md) |
| Reading a probe verdict and fixing each failure reason | [references/probes-guide.md](references/probes-guide.md) |

For general connector authoring depth (every auth type, `state patch` semantics, system resources), the `uipath-connector-builder` skill covers the builder; this skill carries everything a BYO LLM connector needs on its own.

## Anti-patterns

1. Importing a template or an old zip as-is — it carries a shared key and overwrites another connector (Rule 3).
2. Exposing the vendor's path (`/v2/generate`) as the resource path instead of the flavor's path — the probe gets a 404 (Rule 1).
3. Registering `--connector-type Custom` without `--connector-template` — the probe fails inside the gateway (Rule 2).
4. Translating a streamed response in a postRequest hook — it never runs on a stream (Rule 4).
5. Asking the user to paste an API key into the chat, or baking one into `element.json` as a default (Rule 5).
6. Creating the connection with the `design-…` key, or leaving it in a Personal workspace (Rule 8).
7. Re-publishing without bumping `latestVersion`, then probing the old version (Rule 9).
8. Probing with `--enabled`, so a passing test configuration starts serving the product (Rule 10).
9. Logging the prompt or the vendor response "to debug" from a hook (Rule 6).
10. Reporting done on "publish succeeded" without a passing probe on the runtime connection.
