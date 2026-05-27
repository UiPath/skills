# uipath-mcp-servers — eval task suite

Regression tasks for the `uipath-mcp-servers` skill. Each scenario replays the agent's reasoning against a manifest-driven `uip` CLI mock — no live UiPath tenant, no network. All fixtures use synthetic, public-safe values (mock connector instances, mock project keys, mock channel IDs).

## Layout

```
tests/tasks/uipath-mcp-servers/
├── _shared/
│   └── mock_template/
│       └── mocks/
│           └── uip                       # shared Python dispatcher (copy of diagnostics/_shared)
├── README.md                             # this file
├── jira-create/                          # cascade + designTimeLookups (IS-activity)
├── slack-create/                         # reference fields (channel, send_as) (IS-activity)
├── outlook-create/                       # GET with timezone reference (IS-activity)
├── gmail-create/                         # array reference exposed at runtime (IS-activity)
├── jira-update-fix-lookups/              # high-leverage: fix missing labels on existing tool (IS-activity)
├── remote-create/                        # generic Server Types: remote MCP + asset substitution + refresh-tools
└── resource-create/                      # generic Tool Kinds: create-resource on a uipath-type server
    ├── task.yaml                         # TaskDefinition; uses --dry-run on every mutation
    └── fixtures/
        └── mocks/
            └── responses/
                ├── manifest.json         # rule dispatch (substring match → response file)
                └── *.json                # canned per-rule responses
```

## Running

From the repo root:

```bash
cd tests
.venv/bin/coder-eval run tasks/uipath-mcp-servers/jira-create/task.yaml -e experiments/default.yaml -v
```

A passing run produces `score: 1.0`. Inspect `mocks/.calls.jsonl` in the run artifact to confirm which mock rules fired.

## Coverage

Rule numbers below reference SKILL.md generic Critical Rules (1-6) and the IS-Activity-Specific Critical Rules (IS 1-5) in `references/is-activity-workflow.md`.

| Scenario | Rules exercised | Key assertion |
|---|---|---|
| `jira-create`              | IS 1, IS 4, IS 5 + generic 4 | cascade `-f` expands schema; both lookups populated; `--description` present |
| `slack-create`             | IS 5 + generic 4             | `send_as` lookup (`Bot - bot`); channel exposed in inputSchema |
| `outlook-create`           | IS 4, IS 5 + generic 4       | parameters-only schema; `outputTimezone` reference resolved |
| `gmail-create`             | IS 5 + generic 4             | array reference (`addLabelIds[*]`) exposed at runtime — no lookup needed |
| `jira-update-fix-lookups`  | IS 5 + update                | fetch existing → diagnose missing lookups → rebuild → update with scalars |
| `remote-create`            | generic 2, 3, 4, 5           | slug regex compliance; discover payload shape via `--print-schema`/`template remote`; submit via `--file`/`--body`; refresh-tools + verify |
| `resource-create`          | generic 4, 5                 | `mcp-tools create-resource` (NOT `create-is-activity`); `--category automation`; `candidates --category automation`; `template resource`; verify via `mcp-tools list` |

## Why synthetic fixtures (not live captures)

The repo policy is "public-safe fixture corpus" — no tenant data, no real connection GUIDs, no internal project names. Other skills (`uipath-diagnostics`, `uipath-maestro-bpmn`) follow this pattern. Every value in the fixtures here uses a `mock-*` / `MOCKPROJ` / `mock.user@example.com` style placeholder.

If you need to validate the skill against a real tenant, **don't commit those captures**. Capture locally, run the skill, observe behavior, then update the synthetic fixtures here if the shape changed.

## Capturing fresh shapes from a live tenant (for fixture maintenance)

When a real CLI response shape changes (new field, renamed key), recapture out-of-band and translate the shape to a synthetic fixture. The full command set the skill exercises (across IS-activity AND server CRUD / non-IS tool kinds):

```bash
# Folder enumeration
uip or folders list --output json

# AgentHub server listing
uip agenthub mcp list --folder-path Shared --output json
uip agenthub mcp-tools list --mcp <slug> --folder-path Shared --output json

# Activity discovery
uip agenthub mcp-tools candidates --category is-activity --name <vendor> --output json
uip agenthub mcp-tools candidates --category is-activity --connector <connector-key> --output json

# Connection discovery
uip is connections list <connector-key> --output json
uip is connections list <connector-key> --folder-key <guid> --output json

# Operation + field discovery
uip is resources describe <connector-key> <objectName> --connection-id <id> --output json
uip is resources describe <connector-key> <objectName> --connection-id <id> --operation <op> --output json

# Cascade describe (api-type ObjectActions only — Jira curated_create_issue, Salesforce SOQL, Dataservice V3)
uip is resources describe <connector-key> <objectName> --connection-id <id> --operation <op> \
  -f <parent-field>=<value> --output json

# Reference label resolution
uip is resources execute list <connector-key> <reference-object-name> --connection-id <id> --output json

# Tool authoring (dry-run for inspection)
uip agenthub mcp-tools create-is-activity --mcp <slug> --name "<name>" --description "<text>" \
  --folder-path "<folder>" --target-identifier <conn-guid> \
  --metadata "<json>" --input-schema "<json>" --output-schema "<json>" \
  --dry-run --output json

# Tool fetch / update / delete
uip agenthub mcp-tools get --name "<tool>" --mcp <slug> --folder-path <folder> --output json
uip agenthub mcp-tools update <tool-id> --mcp <slug> --folder-path <folder> --description "<text>" \
  --metadata "<json>" --input-schema "<json>" --output-schema "<json>" --dry-run --output json
uip agenthub mcp-tools delete <tool-id> --mcp <slug> --folder-key <guid> --output json
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

The `mocks/uip` script is the [shared dispatcher from uipath-diagnostics](../uipath-diagnostics/_shared/mock_template/mocks/uip) — substring-match-first, supports `passthrough: true` for open-ended commands, logs every call to `.calls.jsonl`. Don't edit per scenario; if a new dispatch behavior is needed, update the upstream copy and propagate.
