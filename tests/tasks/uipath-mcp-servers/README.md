# uipath-mcp-servers — eval task suite

Regression tasks for the `uipath-mcp-servers` skill (Agent Gateway MCP servers). Two kinds:

- **Mocked smoke tasks** replay the agent against a manifest-driven `uip` CLI mock — no live UiPath tenant, no network. All fixtures use synthetic, public-safe values.
- **Live e2e tasks** (`e2e-*`) run the real CLI against the shared test tenant. Each writes `report.json` (`{"slug", "folder_path"}`) and the `post_run` hook `_setup/cleanup_mcp_server.py` deletes that server (`mcp delete --yes`).

## Layout

```
tests/tasks/uipath-mcp-servers/
├── README.md                          # this file
├── _shared/mock_template/mocks/uip    # shared Python mock dispatcher (mocked tasks)
├── _setup/cleanup_mcp_server.py       # e2e post_run cleanup
├── remote-create/                     # mocked
├── resource-create/                   # mocked
├── update-cross-folder-retarget/      # mocked
│   ├── task.yaml
│   └── fixtures/mocks/responses/
│       ├── manifest.json              # rule dispatch (substring match → response file)
│       └── *.json                     # canned per-rule responses
├── e2e-command-server/                # live
├── e2e-platform-server/               # live
├── e2e-remote-server/                 # live
├── e2e-swagger-server/                # live
└── e2e-uipath-allkinds/               # live
```

## Running

From the repo root (one-time `make install` in `tests/` first):

```bash
cd tests
.venv/bin/coder-eval run tasks/uipath-mcp-servers/resource-create/task.yaml -e experiments/default.yaml -v
```

A passing run produces `score: 1.0`. Inspect `mocks/.calls.jsonl` in the run artifact to confirm which mock rules fired. The `e2e-*` tasks need an authenticated `uip` (they run under `experiments/nightly.yaml`). CI images install `@uipath/cli@dev` and the tool plugins from the `@dev` feed (`tests/docker/Dockerfile`); a local `npm install -g @uipath/cli` gets the stable release, which can lag what the skill describes.

The e2e tasks grade the server the agent left on the tenant (`mcp get`, `mcp-tools list`), so an agent may create it with scalar flags or with a camelCase `--file` / `--body` payload. Checks on how the create was spelled (flags vs payload) are advisory (weight 0); the `refresh-tools` checks still require a folder flag, which every refresh needs.

## Coverage

Rule numbers reference the SKILL.md Critical Rules (1-10).

| Scenario | Tier | Rules | Key assertion |
|---|---|---|---|
| `remote-create`                | smoke (mock) | 1, 3, 4, 5, 7 | an Authorization header whose whole value is `%ASSETS/SLACK_BOT_TOKEN%`, via `--header` or a camelCase payload `headers` line, no `Bearer ` prefix (graded from the mock call log by `check_remote_create.py`); `refresh-tools`; inspection via `mcp get` / `mcp list` / `mcp-tools list` |
| `resource-create`              | smoke (mock) | Tools section | `candidates --category automation`; `mcp-tools create-resource ... --dry-run` scoped to the server (`template resource` is advisory) |
| `update-cross-folder-retarget` | smoke (mock) | Tools section | `mcp-tools update` (not a new create) with `--target-identifier` + explicit `--target-folder-*` |
| `e2e-command-server`           | e2e (live)   | 2, 7          | `mcp get` shows a command server running `npx` with `@modelcontextprotocol/server-everything`; async `refresh-tools` with a folder flag |
| `e2e-platform-server`          | e2e (live)   | 2, 7, 9       | `mcp get` shows the `testmanager` service; `mcp-tools list` returns exactly `Get_test_sets` and `Get_test_cases` |
| `e2e-remote-server`            | e2e (live)   | 2, 7          | `mcp get` shows the DeepWiki URI; sync `refresh-tools` with a folder flag stored tools (`mcp-tools list`) |
| `e2e-swagger-server`           | e2e (live)   | 2, 7          | sync `refresh-tools` with a folder flag; `mcp-tools list` holds the Petstore operations (`getPetById`) |
| `e2e-uipath-allkinds`          | e2e (live)   | Tools section | one `create-resource` per category (automation / agent / agentic-process / api-workflow) on one server; 4 tools listed |

## Why synthetic fixtures (not live captures)

The repo policy is "public-safe fixture corpus" — no tenant data, no real connection GUIDs, no internal project names. Every value in the fixtures here uses a `mock-*` / `MOCKPROJ` / `mock.user@example.com` style placeholder.

If you need to validate the skill against a real tenant, **don't commit those captures**. Capture locally, run the skill, observe behavior, then update the synthetic fixtures here if the shape changed. The real CLI PascalCases what it prints, except `mcp template <TYPE>` and `--print-schema`, which print the API's camelCase (CLI 1.204+); `mcp-tools template` stays PascalCase. Mirror that in new fixtures (`remote-create` and `resource-create` do; `update-cross-folder-retarget` still uses older camelCase list / get / dry-run shapes the CLI never prints).

## Capturing fresh shapes from a live tenant (for fixture maintenance)

When a real CLI response shape changes (new field, renamed key), recapture out-of-band and translate the shape to a synthetic fixture. The full command set the skill exercises:

```bash
# Folder enumeration
uip or folders list --output json

# Server listing and schemas
uip agenthub mcp list --folder-path Shared --output json
uip agenthub mcp get <slug> --folder-path Shared --output json
uip agenthub mcp create remote --print-schema --output json
uip agenthub mcp template remote --output json
uip agenthub mcp update <slug> --folder-path Shared --print-schema --output json

# Platform service and tool names
uip agenthub platform-services list --output json
uip agenthub platform-tools list --service testmanager --limit 1000 --output json
uip agenthub mcp-tools list --mcp <slug> --folder-path Shared --output json

# Resource discovery and authoring
uip agenthub mcp-tools candidates --category automation --output json
uip agenthub mcp-tools template resource --output json
uip agenthub mcp-tools create-resource --mcp <slug> --name "<name>" --description "<text>" \
  --folder-path "<folder>" --target-identifier <resource-guid> --category automation \
  --metadata "<json>" --input-schema "<json>" --output-schema "<json>" --dry-run --output json

# Tool fetch / update / delete
uip agenthub mcp-tools get --name "<tool>" --mcp <slug> --folder-path <folder> --output json
uip agenthub mcp-tools update <tool-id> --mcp <slug> --folder-path <folder> --description "<text>" \
  --metadata "<json>" --input-schema "<json>" --output-schema "<json>" --dry-run --output json
uip agenthub mcp-tools delete <tool-id> --mcp <slug> --folder-key <guid> --yes --output json
```

Then translate the captured shapes into the per-scenario `manifest.json` + response files using synthetic values.

## Adding a new scenario

1. Create `<scenario-name>/` next to the existing ones.
2. Drop a `task.yaml` (copy from the closest existing scenario; adjust `task_id`, `description`, `initial_prompt`, `success_criteria`).
3. Build `fixtures/mocks/responses/manifest.json` listing each CLI command the agent will run + its response file.
4. Hand-fabricate the response JSONs. Match real shape, use mock values.
5. Run the eval; iterate until the agent's behavior matches `success_criteria`.
6. Update CODEOWNERS if introducing a new owner.

## Notes on the mock dispatcher

`_shared/mock_template/mocks/uip` is substring-match-first, supports `passthrough: true` for open-ended commands, and logs every call to `.calls.jsonl`. Don't edit it per scenario.
