# Orchestrator Package Offline Eval Run

Submit offline evaluation runs for low-code agents published as Orchestrator packages.

Use this when the agent has been published to Orchestrator (via `uip solution deploy` or Studio) and you want to trigger an eval run against the published package rather than using the Agent Runtime.

## Command

```bash
uip or eval run-offline-evals \
  --package-name <processKey> \
  --package-version <version> \
  [--eval-set-id <guid>] \
  [--items <json>] \
  [--evaluators <json>] \
  [--is-low-code-agent] \
  [--batch-size <n>] \
  [--folder-key <folder-guid>] \
  [--tenant <tenant-name>]
```

The folder resolves from your personal workspace automatically. Pass `--folder-key` to target a specific folder instead.

`--eval-set-id` defaults to `00000000-0000-0000-0000-000000000000` when `--items` and `--evaluators` are provided inline.

## Options

| Flag | Required | Description |
|------|----------|-------------|
| `--package-name` | Yes | Orchestrator package name (processKey, e.g. `MyAutomation.Agent.agent`) |
| `--package-version` | Yes | Package version (e.g. `1.0.2`) |
| `--eval-set-id` | No | Eval set ID to run; mutually exclusive with `--items`/`--evaluators` |
| `--items` | No | JSON array of eval items to override those from the package |
| `--evaluators` | No | JSON array of evaluator configs to override those from the package |
| `--is-low-code-agent` | No | Auto-transform items/evaluators from the raw package format (flat JSON with `type`/`category` fields) to the API wire format. Use this when pasting directly from the package or portal. |
| `--batch-size` | No | Max concurrent evaluation pipelines (default: `5`) |
| `--folder-key` | No | Folder key GUID; defaults to personal workspace. Use `uip or folders list` to find available keys. |
| `--tenant` | No | UiPath tenant name |

## Examples

```bash
# Minimal — items/evaluators loaded from the published package
uip or eval run-offline-evals \
  --package-name "MyAutomation.Agent.agent" \
  --package-version "1.0.2" \
  --eval-set-id "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09"

# Inline override — paste evaluator and item JSON directly from the package/portal.
# Use --is-low-code-agent to auto-transform: wraps evaluator as { evaluatorTypeId, evaluatorConfig }
# and renames expectedAgentBehavior → expectedBehavior on items.
# Replace "model" with the actual model ID used by the agent (not "same-as-agent").
uip or eval run-offline-evals \
  --package-name "MyAutomation.Agent.agent" \
  --package-version "1.0.2" \
  --is-low-code-agent \
  --evaluators '[{
    "id": "8f3a1c72-bd4e-4f91-a832-9e5d2b7c04f6",
    "name": "Default Evaluator",
    "type": 5,
    "category": 1,
    "prompt": "As an expert evaluator, analyze the semantic similarity...",
    "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "targetOutputKey": "*",
    "createdAt": "2026-05-31T19:36:35.382Z",
    "updatedAt": "2026-05-31T19:36:35.382Z"
  }]' \
  --items '[{
    "id": "7b2e9f48-c3a1-4d85-b6f2-1e8c5a9d3b70",
    "name": "Test Case 1",
    "inputs": {},
    "expectedOutput": { "content": "The current date is 2026-05-31." },
    "expectedAgentBehavior": ""
  }]'

# Explicit folder key instead of personal workspace
uip or eval run-offline-evals \
  --package-name "MyAutomation.Agent.agent" \
  --package-version "1.0.2" \
  --eval-set-id "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09" \
  --folder-key "a9f3b2c1-7d4e-4a8b-9c2f-5e1d3b6a8f7e"
```

## Output

```json
{
  "Result": "Success",
  "Code": "EvalRunSubmitted",
  "Data": {
    "Package": "MyAutomation.Agent.agent v1.0.2",
    "Folder": "user@uipath.com's workspace",
    "EvalSetId": "9e4b2f17-7c3a-4d81-b592-3f6e8a1d5c09",
    "EvalSetRunId": "f3a7d219-8b4c-4e62-a951-7d3f6e2c8b04"
  }
}
```

Use the `EvalSetRunId` to track results in the UiPath portal.

## Items and Evaluators Format

### Without `--is-low-code-agent` (API wire format)

Pass the data already in the format the API expects:

**Evaluators** — each item must have `id`, `evaluatorTypeId` (string), and `evaluatorConfig`:

```json
[
  {
    "id": "8f3a1c72-bd4e-4f91-a832-9e5d2b7c04f6",
    "version": "",
    "evaluatorTypeId": "5",
    "evaluatorConfig": {
      "id": "8f3a1c72-bd4e-4f91-a832-9e5d2b7c04f6",
      "name": "Default Evaluator",
      "type": 5,
      "category": 1,
      "prompt": "As an expert evaluator...",
      "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
      "targetOutputKey": "*",
      "createdAt": "2026-05-31T19:36:35.382Z",
      "updatedAt": "2026-05-31T19:36:35.382Z"
    }
  }
]
```

**Items** — each item must include `id`, `name`, `inputs`, and `expectedOutput`:

```json
[
  {
    "id": "7b2e9f48-c3a1-4d85-b6f2-1e8c5a9d3b70",
    "name": "Test Case 1",
    "inputs": {},
    "expectedOutput": { "content": "Expected agent response here." },
    "expectedBehavior": ""
  }
]
```

### With `--is-low-code-agent` (raw package format)

Paste the evaluator JSON directly from the package file (flat, with `type` and `category` at the top level). The CLI will auto-transform to the wire format.

> **Note:** Replace `"model": "same-as-agent"` with the actual model ID (e.g. `"anthropic.claude-3-5-sonnet-20240620-v1:0"`). The `same-as-agent` value requires loading `agent.json` from the package, which is not available in inline mode.

```json
[
  {
    "id": "8f3a1c72-bd4e-4f91-a832-9e5d2b7c04f6",
    "name": "Default Evaluator",
    "type": 5,
    "category": 1,
    "prompt": "As an expert evaluator...",
    "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
    "targetOutputKey": "*",
    "createdAt": "2026-05-31T19:36:35.382Z",
    "updatedAt": "2026-05-31T19:36:35.382Z"
  }
]
```

Items use `expectedAgentBehavior` (renamed to `expectedBehavior` automatically):

```json
[
  {
    "id": "7b2e9f48-c3a1-4d85-b6f2-1e8c5a9d3b70",
    "name": "Test Case 1",
    "inputs": {},
    "expectedOutput": { "content": "Expected agent response here." },
    "expectedAgentBehavior": ""
  }
]
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Auth expired or not configured | Run `uip login` |
| `Authentication failed` | No active session | Run `uip login` first |
| `Package not found` | Package not published or wrong name/version | Verify with `uip or packages list`; re-publish with `uip solution deploy` |
| `Eval set not found` | Invalid `--eval-set-id` GUID | Verify the eval set exists in the portal; use `--items` and `--evaluators` inline instead |
| `'same-as-agent' model option requires agent settings` | Inline evaluator has `"model": "same-as-agent"` — agent.json not available in inline mode | Replace with explicit model ID (e.g. `anthropic.claude-3-5-sonnet-20240620-v1:0`) |
| `personal workspace not found` | Account has no personal workspace | Pass `--folder-key` explicitly |
| `Folder not found` | `--folder-key` GUID invalid or inaccessible | Run `uip or folders list` to find valid keys |

## Validation rules

The CLI enforces these rules before making any network calls:

1. **Must provide `--eval-set-id` OR both `--items` and `--evaluators`.** Omitting all three is an error.
2. **`--eval-set-id` and `--items`/`--evaluators` are mutually exclusive.** Providing both is an error.
3. **`--items` and `--evaluators` must be provided together.** Providing one without the other is an error.
4. **`--batch-size` must be a positive integer.** Non-numeric values are rejected with an error.

## Anti-patterns

- **Don't run against an unpublished package version.** The command targets the package already in Orchestrator. Bump `--package-version` after each publish; stale versions return results from old agent logic.
- **Don't mix `--eval-set-id` with `--items`/`--evaluators`.** They are mutually exclusive. Use `--eval-set-id` to load from a saved eval set, or `--items`/`--evaluators` to provide inline. Not both.
- **Don't use `--eval-file` schema that mismatches the package's eval set.** Field names differ between legacy (`expectedAgentBehavior`) and wire format (`expectedBehavior`). Use `--is-low-code-agent` when pasting directly from the package or portal.
- **Don't pass `"model": "same-as-agent"` with inline `--evaluators`.** Inline mode has no access to `agent.json`; the CLI cannot resolve `same-as-agent` and will error at runtime.
