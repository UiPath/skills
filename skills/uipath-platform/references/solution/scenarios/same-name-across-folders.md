# Same-name resource across cloud folders

You have two tools (or two bindings, or two project references) that target a resource with **the same name in different cloud folders**. Most common case: an agent with two API Workflow tools, both called "API Workflow", living in `Shared/Solution 50` and `Shared/DependenciesSolution`. RCS is happy with this — names are unique per folder, not globally — but the solution flattens both into a single `resources/solution_folder/process/api/` directory.

## Setup

Two bindings in the agent's `bindings_v2.json`, same `value.name.defaultValue`, different `value.folderPath.defaultValue`:

```json
{
  "version": "2.0",
  "resources": [
    { "resource": "process", "key": "API Workflow",
      "value": { "name": { "defaultValue": "API Workflow" },
                 "folderPath": { "defaultValue": "Shared/Solution 50" } },
      "metadata": { "subType": "api", "bindingsVersion": "2.2", "solutionsSupport": "true" } },
    { "resource": "process", "key": "API Workflow",
      "value": { "name": { "defaultValue": "API Workflow" },
                 "folderPath": { "defaultValue": "Shared/DependenciesSolution" } },
      "metadata": { "subType": "api", "bindingsVersion": "2.2", "solutionsSupport": "true" } }
  ]
}
```

Each tool's `resource.json` carries the cloud key in `referenceKey` and the cloud FQN in `properties.folderPath`.

## What happens at `solution resource refresh`

```
Synced 2 resources (0 already in solution)
```

The SDK applies `addResourceWithUniqueName`: the first import lands as `API_Workflow.json` with the first cloud key; the second hits a name conflict and is **suffixed** to `API_Workflow_1.json` with the second cloud key.

```
resources/solution_folder/process/api/
├── API_Workflow.json     (key=6337a36e..., name="API Workflow")
└── API_Workflow_1.json   (key=5aaddd83..., name="API Workflow_1")  ← suffix added by SDK
```

The `_1` suffix is **expected and stable** — re-running refresh does not bump it further. Tool resource files are not touched; their `referenceKey` still points at the right cloud GUID.

## Gotchas

- **Tool dialogs in Studio Web may show only one tool** opening correctly. This is an SW UI bug present even on solutions authored entirely in Studio Web — confirmed by inspecting raw `Solution.uis` exports. The packed and deployed runtime is unaffected: the agent's `runtimeDependencies` carry distinct `resourceKey` + cloud `folderKey` per tool, so Orchestrator dispatches to the correct cloud workflow.
- **Tool-agent dedup collapses bindings in the agent's nupkg** to one entry per `processName`. The packed `content/bindings_v2.json` shows a single `key: "API Workflow"` even though the agent has two tools. This is shared with Studio Web's server-side pack output. Don't try to fix it at the bindings layer — the deploy-time resolution path uses `tool.referenceKey → solution resource → debug_overwrites → cloud folder`, not the collapsed binding.
- **Don't rename `processName` on the second tool by hand to dodge the collapse.** It changes the agent's call signature without rewriting the agent code/prompt that references the tool, and the next `agent validate` will revert it.

## Verify

```bash
uip solution resource list --kind Process --solution-folder ./MySolution --source local --output json
```

You should see two `process`/`api` entries with **different keys** but matching the cloud GUIDs you wanted (compare against `uip flow registry search "API Workflow"`).

> See: [develop-solution.md — Step 7: Refresh Resources](../develop-solution.md#step-7-refresh-resources).
